"""
Sentinel 위성 다운로드 에이전트 - Streamlit UI
"""
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# 로컬 모듈 import
from satellite_tools import (
    download_sentinel1_grd,
    download_sentinel2_l2a,
    sentinel1_download_tool,
    sentinel2_download_tool,
    geocode_location_tool,
    geocode_location
)

# 환경 변수 로드
load_dotenv()

# 저장 경로
SAVE_DIR = r"E:\2025\18.LLM project\sentinel2 ai agent"

# Tools 리스트
tools = [sentinel1_download_tool, sentinel2_download_tool, geocode_location_tool]


def get_llm_with_tools():
    """LLM + Tools 바인딩"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.bind_tools(tools)


# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="Sentinel Satellite Agent", page_icon="🛰️")
st.title("🛰️ Sentinel 위성 다운로드 에이전트")
st.caption(
    "Sentinel-1 (SAR) 및 Sentinel-2 (광학) 위성 데이터를 자연어로 요청하거나 직접 다운로드할 수 있습니다.\n"
    f"다운로드 경로: {SAVE_DIR}"
)

tab_chat, tab_s1, tab_s2 = st.tabs(["🧠 Chat Agent", "🛰️ Sentinel-1 Direct", "🌍 Sentinel-2 Direct"])

# 메시지 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        SystemMessage(
            content=(
                "You are a helpful satellite data assistant. "
                "You can help users download Sentinel-1 (SAR) and Sentinel-2 (optical) data.\n\n"
                
                "WORKFLOW:\n"
                "1. If user mentions a location name (not coordinates), use geocode_location_tool FIRST\n"
                "2. WAIT for geocoding result, then extract lat/lon from it\n"
                "3. Use sentinel1_download_tool or sentinel2_download_tool with the extracted coordinates\n"
                "4. Provide a final summary in Korean\n\n"
                
                "Location examples: '부산 광안대교', '서울 강남역', 'Tokyo Tower', '제주도 성산일출봉'\n\n"
                
                "Satellite selection:\n"
                "- SAR/radar/'Sentinel-1' → sentinel1_download_tool\n"
                "- Optical/RGB/'Sentinel-2' → sentinel2_download_tool\n"
                "- If not specified, ask user\n\n"
                
                f"Always use save_dir='{SAVE_DIR}'\n"
                "If date not specified, use 2023-06-01\n\n"
                
                "Respond in Korean naturally."
            )
        )
    ]

# ========== 탭 1: Chat Agent ==========
with tab_chat:
    st.markdown("### 💬 자연어로 위성 데이터 요청")

    for msg in st.session_state["messages"]:
        if isinstance(msg, SystemMessage):
            continue
        elif isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            if msg.content:
                with st.chat_message("assistant"):
                    st.markdown(msg.content)

    user_input = st.chat_input("예) 부산 광안대교 2023년 6월 Sentinel-2 광학 영상 내려줘")

    if user_input:
        st.session_state["messages"].append(HumanMessage(content=user_input))
        
        with st.chat_message("user"):
            st.markdown(user_input)

        llm_with_tools = get_llm_with_tools()
        
        # 여러 번의 tool call이 있을 수 있으므로 반복
        max_iterations = 5  # 무한루프 방지
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            with st.spinner("처리 중..."):
                response = llm_with_tools.invoke(st.session_state["messages"])

            # Tool call이 있으면 실행
            if getattr(response, "tool_calls", None):
                st.session_state["messages"].append(response)
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    args = tool_call["args"]
                    
                    # geocode_location_tool 처리
                    if tool_name == "geocode_location_tool":
                        with st.chat_message("assistant"):
                            st.markdown(f"📍 '{args['location_query']}' 위치를 검색하는 중...")
                        
                        with st.spinner("위치 검색 중..."):
                            result_text = geocode_location(args["location_query"])
                        
                        tool_message = ToolMessage(
                            content=result_text,
                            tool_call_id=tool_call["id"]
                        )
                        st.session_state["messages"].append(tool_message)
                        
                        with st.chat_message("assistant"):
                            st.info(result_text)
                    
                    # sentinel 다운로드 tool 처리
                    elif tool_name in ["sentinel1_download_tool", "sentinel2_download_tool"]:
                        satellite_type = "Sentinel-1 (SAR)" if tool_name == "sentinel1_download_tool" else "Sentinel-2 (광학)"
                        
                        with st.chat_message("assistant"):
                            st.markdown(
                                f"🛰️ {satellite_type} 다운로드를 시작합니다...\n\n"
                                f"- 위도: {args['lat']}\n"
                                f"- 경도: {args['lon']}\n"
                                f"- 날짜: {args['date_str']}\n"
                                f"- 검색 범위: ±10일"
                            )
                        
                        with st.spinner(f"{satellite_type} 검색 및 다운로드 중..."):
                            if tool_name == "sentinel1_download_tool":
                                result_text = download_sentinel1_grd(
                                    lon=args["lon"],
                                    lat=args["lat"],
                                    date_str=args["date_str"],
                                    save_dir=args["save_dir"],
                                    days_margin=10,
                                )
                            else:
                                result_text = download_sentinel2_l2a(
                                    lon=args["lon"],
                                    lat=args["lat"],
                                    date_str=args["date_str"],
                                    save_dir=args["save_dir"],
                                    days_margin=10,
                                    max_cloud_cover=20,
                                )
                        
                        tool_message = ToolMessage(
                            content=result_text,
                            tool_call_id=tool_call["id"]
                        )
                        st.session_state["messages"].append(tool_message)
                        
                        with st.chat_message("assistant"):
                            st.code(result_text, language="text")
                
                # Tool 실행 후 계속 진행 (다음 iteration에서 LLM이 판단)
                continue
            
            # Tool call이 없으면 최종 응답
            else:
                if response.content:
                    with st.chat_message("assistant"):
                        st.markdown(response.content)
                    st.session_state["messages"].append(response)
                break  # 루프 종료

        st.rerun()

# ========== 탭 2: Sentinel-1 Direct ==========
with tab_s1:
    st.markdown("### 🛰️ Sentinel-1 (SAR) 직접 다운로드")

    col1, col2 = st.columns(2)
    with col1:
        lat_s1 = st.number_input("위도 (lat)", value=35.1796, format="%.6f", key="lat_s1")
    with col2:
        lon_s1 = st.number_input("경도 (lon)", value=129.0750, format="%.6f", key="lon_s1")

    date_s1 = st.date_input("기준 날짜", value=datetime(2023, 6, 2), key="date_s1")
    days_s1 = st.slider("±일 범위", min_value=1, max_value=30, value=10, key="days_s1")

    if st.button("Sentinel-1 다운로드 실행"):
        date_str = date_s1.strftime("%Y-%m-%d")
        with st.spinner("Sentinel-1 GRD 검색 및 다운로드 중..."):
            result_text = download_sentinel1_grd(
                lon=lon_s1,
                lat=lat_s1,
                date_str=date_str,
                save_dir=SAVE_DIR,
                days_margin=days_s1,
            )
        st.success("다운로드 완료!")
        st.code(result_text, language="text")

# ========== 탭 3: Sentinel-2 Direct ==========
with tab_s2:
    st.markdown("### 🌍 Sentinel-2 (광학) 직접 다운로드")

    col1, col2 = st.columns(2)
    with col1:
        lat_s2 = st.number_input("위도 (lat)", value=35.1796, format="%.6f", key="lat_s2")
    with col2:
        lon_s2 = st.number_input("경도 (lon)", value=129.0750, format="%.6f", key="lon_s2")

    date_s2 = st.date_input("기준 날짜", value=datetime(2023, 6, 2), key="date_s2")
    days_s2 = st.slider("±일 범위", min_value=1, max_value=30, value=10, key="days_s2")
    cloud_s2 = st.slider("최대 구름 비율 (%)", min_value=0, max_value=100, value=20, key="cloud_s2")

    if st.button("Sentinel-2 다운로드 실행"):
        date_str = date_s2.strftime("%Y-%m-%d")
        with st.spinner("Sentinel-2 L2A 검색 및 다운로드 중..."):
            result_text = download_sentinel2_l2a(
                lon=lon_s2,
                lat=lat_s2,
                date_str=date_str,
                save_dir=SAVE_DIR,
                days_margin=days_s2,
                max_cloud_cover=cloud_s2,
            )
        st.success("다운로드 완료!")
        st.code(result_text, language="text")
