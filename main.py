# streamlit_app.py

import streamlit as st
import geopandas as gpd
import requests
from io import StringIO
import matplotlib.pyplot as plt
import koreanize_matplotlib  # 한국어 폰트 이슈 해결

# 🔐 SGIS 인증 정보
SGIS_KEY = st.secrets["SGIS_KEY"]
SGIS_SECRET = st.secrets["SGIS_SECRET"]

@st.cache_data
def get_access_token():
    url = "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
    params = {
        "consumer_key": SGIS_KEY,
        "consumer_secret": SGIS_SECRET
    }
    response = requests.get(url, params=params)
    return response.json()["result"]["accessToken"]

@st.cache_data
def get_geojson(adm_cd="11", low_search="2"):
    access_token = get_access_token()
    url = "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson"
    params = {
        "accessToken": access_token,
        "adm_cd": adm_cd,
        "low_search": low_search,
        "year": "2022"
    }
    response = requests.get(url, params=params)
    gdf = gpd.read_file(StringIO(response.text))
    return gdf

# 🎛️ Streamlit UI
st.title("🗺️ 한국 행정구역 지도 시각화")

regions = {
    "서울특별시": "11", "부산광역시": "26", "대구광역시": "27", "인천광역시": "28",
    "광주광역시": "29", "대전광역시": "30", "울산광역시": "31", "세종특별자치시": "36",
    "경기도": "41", "강원특별자치도": "51", "충청북도": "43", "충청남도": "44",
    "전라북도": "45", "전라남도": "46", "경상북도": "47", "경상남도": "48",
    "제주특별자치도": "50"
}

selected_region = st.selectbox("시/도 선택", list(regions.keys()))
selected_adm_cd = regions[selected_region]

gdf = get_geojson(adm_cd=selected_adm_cd)

# 🖼️ 지도 시각화
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, edgecolor="black", color="#B4D9FF")
ax.set_title(f"{selected_region} 하위 행정동 경계", fontsize=18)
ax.axis("off")
st.pyplot(fig)
