# streamlit_youth_map.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import requests
from io import StringIO

# 🌐 SGIS 인증
SGIS_KEY = st.secrets["SGIS_KEY"]
SGIS_SECRET = st.secrets["SGIS_SECRET"]

@st.cache_data
def get_token():
    url = "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
    params = {
        "consumer_key": SGIS_KEY,
        "consumer_secret": SGIS_SECRET
    }
    res = requests.get(url, params=params)
    return res.json()["result"]["accessToken"]

@st.cache_data
def get_geojson(adm_cd="11", low_search="2"):
    token = get_token()
    url = "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson"
    params = {
        "accessToken": token,
        "adm_cd": adm_cd,
        "low_search": low_search,
        "year": "2022"
    }
    geo_resp = requests.get(url, params=params)
    return gpd.read_file(StringIO(geo_resp.text))

@st.cache_data
def load_age_data():
    df = pd.read_csv("age.csv")
    # 행정구역 이름 정리
    df["행정동"] = df["행정구역"].str.extract(r'\s(.+)\(')[0]
    # 청소년(10~19세) 비율 계산
    youth_cols = [f"2025년03월_계_{i}세" for i in range(10, 20)]
    df["청소년수"] = df[youth_cols].sum(axis=1)
    df["청소년비율(%)"] = (df["청소년수"] / df["2025년03월_계_총인구수"]) * 100
    return df[["행정동", "청소년비율(%)"]]

# 📍 메인 앱
st.title("📊 서울시 행정동별 청소년 비율 지도")

gdf = get_geojson()
age_df = load_age_data()

# 병합 (GeoDataFrame의 adm_nm과 age_df의 행정동명 기준)
merged = gdf.merge(age_df, how="left", left_on="adm_nm", right_on="행정동")

# folium 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 행정경계 시각화 + 툴팁 추가
style = lambda x: {
    "fillColor": "#228B22",
    "color": "black",
    "weight": 0.5,
    "fillOpacity": 0.4
}

tooltip = GeoJsonTooltip(
    fields=["adm_nm", "청소년비율(%)"],
    aliases=["행정동", "청소년 비율(%)"],
    localize=True,
    sticky=True
)

folium.GeoJson(
    merged,
    tooltip=tooltip,
    style_function=style
).add_to(m)

# Streamlit에 지도 표시
st_folium(m, width=800, height=600)
