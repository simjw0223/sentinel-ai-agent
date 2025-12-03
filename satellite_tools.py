"""
Sentinel 위성 데이터 다운로드 함수 및 LangChain Tools
"""
import os
from datetime import datetime, timedelta, timezone
import requests
from pystac_client import Client
from langchain.tools import tool


def download_sentinel1_grd(
    lon: float,
    lat: float,
    date_str: str,
    save_dir: str = "downloads",
    days_margin: int = 10,
):
    """
    Sentinel-1 GRD (SAR) 다운로드
    """
    os.makedirs(save_dir, exist_ok=True)

    center_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_date = (center_date - timedelta(days=days_margin)).strftime("%Y-%m-%dT00:00:00Z")
    end_date = (center_date + timedelta(days=days_margin)).strftime("%Y-%m-%dT23:59:59Z")

    catalog_url = "https://earth-search.aws.element84.com/v1"
    catalog = Client.open(catalog_url)

    delta = 0.2
    bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

    search = catalog.search(
        collections=["sentinel-1-grd"],
        bbox=bbox,
        datetime=f"{start_date}/{end_date}",
        limit=50,
    )
    items = list(search.get_items())
    print(f"검색된 Sentinel-1 GRD 개수: {len(items)}")

    if not items:
        return (
            f"±{days_margin}일 범위에서도 Sentinel-1 GRD 영상을 찾지 못했습니다.\n"
            f"기준 날짜: {date_str}, 좌표(lon={lon}, lat={lat})"
        )

    def get_time_diff(item):
        item_datetime_str = item.properties.get("datetime")
        if item_datetime_str is None:
            return float("inf")
        item_datetime = datetime.fromisoformat(item_datetime_str.replace("Z", "+00:00"))
        return abs((item_datetime - center_date).total_seconds())

    items.sort(key=get_time_diff)
    item = items[0]
    selected_time = item.properties.get("datetime")
    print(f"선택된 item ID: {item.id}")
    print(f"촬영 시각: {selected_time}")

    assets = item.assets
    vv_asset = assets.get("vv")
    vh_asset = assets.get("vh")

    def s3_to_http(href: str) -> str:
        if href.startswith("s3://"):
            no_scheme = href[len("s3://"):]
            bucket, key = no_scheme.split("/", 1)
            return f"https://{bucket}.s3.amazonaws.com/{key}"
        else:
            return href

    downloaded_paths = {}

    # VV 다운로드
    if vv_asset is not None:
        vv_url = s3_to_http(vv_asset.href)
        vv_filename = os.path.join(save_dir, f"{item.id}_vv.tif")
        resp = requests.get(vv_url, stream=True)
        if resp.status_code == 200:
            with open(vv_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            downloaded_paths["VV"] = vv_filename
        else:
            downloaded_paths["VV"] = f"다운로드 실패 (status code: {resp.status_code})"
    else:
        downloaded_paths["VV"] = "해당 장면에 VV 편파 없음"

    # VH 다운로드
    if vh_asset is not None:
        vh_url = s3_to_http(vh_asset.href)
        vh_filename = os.path.join(save_dir, f"{item.id}_vh.tif")
        resp = requests.get(vh_url, stream=True)
        if resp.status_code == 200:
            with open(vh_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            downloaded_paths["VH"] = vh_filename
        else:
            downloaded_paths["VH"] = f"다운로드 실패 (status code: {resp.status_code})"
    else:
        downloaded_paths["VH"] = "해당 장면에 VH 편파 없음"

    result_msg = [
        "Sentinel-1 다운로드 결과:",
        f" VV: {downloaded_paths['VV']}",
        f" VH: {downloaded_paths['VH']}",
        f"촬영 시각: {selected_time}",
    ]
    return "\n".join(result_msg)


def download_sentinel2_l2a(
    lon: float,
    lat: float,
    date_str: str,
    save_dir: str = "downloads",
    days_margin: int = 10,
    max_cloud_cover: int = 20,
):
    """
    Sentinel-2 L2A (광학) 다운로드
    """
    os.makedirs(save_dir, exist_ok=True)

    center_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_date = (center_date - timedelta(days=days_margin)).strftime("%Y-%m-%dT00:00:00Z")
    end_date = (center_date + timedelta(days=days_margin)).strftime("%Y-%m-%dT23:59:59Z")

    catalog_url = "https://earth-search.aws.element84.com/v1"
    catalog = Client.open(catalog_url)

    delta = 0.2
    bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

    search = catalog.search(
        collections=["sentinel-2-l1a"], # l2a(대기보정, 타일) -> l1c(대기보정 x 전체)로 변경
        bbox=bbox,
        datetime=f"{start_date}/{end_date}",
        query={"eo:cloud_cover": {"lt": max_cloud_cover}},
        limit=50,
    )

    items = list(search.get_items())
    print(f"검색된 Sentinel-2 L2A 개수 (구름 <{max_cloud_cover}%): {len(items)}")

    if not items:
        return (
            f"±{days_margin}일 범위, 구름 <{max_cloud_cover}% 조건에서 "
            f"Sentinel-2 영상을 찾지 못했습니다.\n"
            f"기준 날짜: {date_str}, 좌표(lon={lon}, lat={lat})"
        )

    def get_time_diff(item):
        item_datetime_str = item.properties.get("datetime")
        if item_datetime_str is None:
            return float("inf")
        item_datetime = datetime.fromisoformat(item_datetime_str.replace("Z", "+00:00"))
        return abs((item_datetime - center_date).total_seconds())

    items.sort(key=get_time_diff)
    item = items[0]

    selected_time = item.properties.get("datetime")
    cloud_cover = item.properties.get("eo:cloud_cover", "N/A")
    
    print(f"선택된 item ID: {item.id}")
    print(f"촬영 시각: {selected_time}")
    print(f"구름 비율: {cloud_cover}%")

    assets = item.assets

    target_assets = {}
    if "visual" in assets:
        target_assets["visual"] = assets["visual"]
    if "red" in assets:
        target_assets["red"] = assets["red"]
    if "green" in assets:
        target_assets["green"] = assets["green"]
    if "blue" in assets:
        target_assets["blue"] = assets["blue"]

    if not target_assets:
        return "다운로드 가능한 RGB 관련 asset을 찾지 못했습니다."

    def s3_to_http(href: str) -> str:
        if href.startswith("s3://"):
            no_scheme = href[len("s3://"):]
            bucket, key = no_scheme.split("/", 1)
            return f"https://{bucket}.s3.amazonaws.com/{key}"
        else:
            return href

    downloaded_files = {}
    
    for asset_name, asset in target_assets.items():
        http_url = s3_to_http(asset.href)
        filename = os.path.join(save_dir, f"{item.id}_{asset_name}.tif")
        
        resp = requests.get(http_url, stream=True)
        
        if resp.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            downloaded_files[asset_name.upper()] = filename
        else:
            downloaded_files[asset_name.upper()] = f"실패 (status: {resp.status_code})"

    result_lines = ["Sentinel-2 L2A 다운로드 결과:"]
    for asset_name, path in downloaded_files.items():
        result_lines.append(f"  {asset_name}: {path}")
    result_lines.append(f"촬영 시각: {selected_time}")
    result_lines.append(f"구름 비율: {cloud_cover}%")
    
    return "\n".join(result_lines)


# ==============================
# LangChain Tools
# ==============================
@tool
def sentinel1_download_tool(lon: float, lat: float, date_str: str, save_dir: str) -> str:
    """
    지정한 경도(lon), 위도(lat), 날짜(date_str)에 대해
    해당 위치를 포함하는 ±10일 이내의 Sentinel-1 GRD SAR 장면을 검색하고
    VV/VH 영상을 다운로드합니다.
    date_str 형식: 'YYYY-MM-DD'
    """
    return download_sentinel1_grd(
        lon=lon,
        lat=lat,
        date_str=date_str,
        save_dir=save_dir,
        days_margin=10,
    )


@tool
def sentinel2_download_tool(lon: float, lat: float, date_str: str, save_dir: str) -> str:
    """
    지정한 경도(lon), 위도(lat), 날짜(date_str)에 대해
    해당 위치를 포함하는 ±10일 이내, 구름 20% 이하의
    Sentinel-2 L2A 광학 영상을 다운로드합니다.
    date_str 형식: 'YYYY-MM-DD'
    """
    return download_sentinel2_l2a(
        lon=lon,
        lat=lat,
        date_str=date_str,
        save_dir=save_dir,
        days_margin=10,
        max_cloud_cover=20,
    )

# satellite_tools.py에 추가
# satellite_tools.py
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def geocode_location(location_query: str) -> str:
    """
    자연어 위치 설명을 위도/경도로 변환 (실제 함수)
    """
    try:
        geolocator = Nominatim(user_agent="sentinel_downloader")
        location = geolocator.geocode(location_query, timeout=10)
        
        if location:
            return f"위도: {location.latitude}, 경도: {location.longitude}\n주소: {location.address}"
        else:
            return f"'{location_query}' 위치를 찾을 수 없습니다. 더 구체적인 주소를 입력해주세요."
    
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return f"위치 검색 중 오류 발생: {str(e)}"


@tool
def geocode_location_tool(location_query: str) -> str:
    """
    자연어 위치 설명을 위도/경도로 변환합니다.
    예: "부산 광안대교", "서울 강남역", "Busan Gwangan Bridge"
    
    Returns: "위도: XX.XXXX, 경도: YYY.YYYY" 형식의 문자열
    """
    return geocode_location(location_query)
