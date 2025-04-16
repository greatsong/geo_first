import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import requests
from io import StringIO
import branca.colormap as cm

st.set_page_config(layout="wide")

# 🔐 SGIS API 인증 정보
SGIS_KEY = st.secrets["SGIS_KEY"]
SGIS_SECRET = st.secrets["SGIS_SECRET"]

@st.cache_data
def get_access_token():
    token_url = "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
    params = {
        "consumer_key": SGIS_KEY,
        "consumer_secret": SGIS_SECRET
    }
    res = requests.get(token_url, params=params)
    return res.json()["result"]["accessToken"]

@st.cache_data
def get_geojson(adm_cd="11", low_search="2"):
    access_token = get_access_token()
    geo_url = "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson"
    geo_params = {
        "accessToken": access_token,
        "adm_cd": adm_cd,
        "low_search": low_search,
        "year": "2022"
    }
    geo_resp = requests.get(geo_url, params=geo_params)
    return gpd.read_file(StringIO(geo_resp.text))

@st.cache_data
def load_age_data():
    df = pd.read_csv("age.csv")

    # 행정동 이름 정제
    df["행정동풀네임"] = df["행정구역"].str.extract(r'\s(.+)\(')[0]  # ex: "종로구 청운효자동"
    df["행정동"] = df["행정동풀네임"].str.extract(r'(\S+)$')          # ex: "청운효자동"

    # 청소년 인구 비율 계산 (10세 ~ 19세)
    youth_cols = [f"2025년03월_계_{i}세" for i in range(10, 20)]
    df["청소년수"] = df[youth_cols].sum(axis=1)
    df["청소년비율(%)"] = (df["청소년수"] / df["2025년03월_계_총인구수"]) * 100

    return df[["행정동", "청소년비율(%)"]]

# 🌍 Streamlit 화면
st.title("🧑‍🎓 서울시 행정동별 청소년 비율 지도")

# 1. 데이터 불러오기
geo_gdf = get_geojson()
age_df = load_age_data()

# 2. 병합: GeoJSON의 'adm_nm' ↔ age_df의 '행정동'
merged = geo_gdf.merge(age_df, how="left", left_on="adm_nm", right_on="행정동")

# 3. 컬러맵 설정 (청소년 비율 시각화)
min_val = merged["청소년비율(%)"].min()
max_val = merged["청소년비율(%)"].max()
colormap = cm.linear.YlGnBu_09.scale(min_val, max_val)

def style_function(feature):
    val = feature["properties"].get("청소년비율(%)", None)
    color = colormap(val) if val is not None else "gray"
    return {
        "fillColor": color,
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.7
    }

# 4. 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 5. GeoJson + 툴팁 설정
tooltip = GeoJsonTooltip(
    fields=["adm_nm", "청소년비율(%)"],
    aliases=["행정동", "청소년 비율 (%)"],
    localize=True,
    sticky=True
)

folium.GeoJson(
    merged,
    style_function=style_function,
    tooltip=tooltip,
    name="청소년비율"
).add_to(m)

# 6. 컬러 범례 추가
colormap.caption = "청소년 비율 (%)"
colormap.add_to(m)

# 7. 출력
st_folium(m, width=1000, height=700)
