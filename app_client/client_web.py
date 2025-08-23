import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="MySQL Hub MCP Client",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 서버 URL 설정
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:9000")

def make_request(endpoint, data=None, method="GET"):
    """서버에 요청을 보내는 함수"""
    try:
        url = f"{SERVER_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=200)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=200)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"서버 연결 오류: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "서버 응답을 파싱할 수 없습니다."}

def display_dataframe(data, title="조회 결과"):
    """데이터프레임을 표시하는 함수"""
    if not data:
        st.warning("표시할 데이터가 없습니다.")
        return
    
    # 데이터 구조 확인 및 처리
    if isinstance(data, list):
        # 리스트 형태로 직접 반환된 경우
        rows = data
    elif isinstance(data, dict) and "rows" in data:
        # {"rows": [...]} 형태인 경우
        rows = data["rows"]
    else:
        st.warning("지원하지 않는 데이터 형식입니다.")
        return
    
    if not rows:
        st.warning("표시할 데이터가 없습니다.")
        return
    
    df = pd.DataFrame(rows)
    st.subheader(f"📊 {title}")
    st.dataframe(df, use_container_width=True)
    
    # 데이터 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 행 수", len(rows))
    with col2:
        st.metric("총 열 수", len(rows[0]) if rows else 0)
    with col3:
        st.metric("조회 시간", datetime.now().strftime("%H:%M:%S"))

def main():
    # 헤더
    st.markdown('<h1 class="main-header">🗄️ MySQL Hub MCP Client</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 서버 URL 설정
        server_url = st.text_input(
            "서버 URL",
            value=SERVER_URL,
            help="MySQL Hub MCP 서버의 URL을 입력하세요"
        )
        
        st.divider()
        
        # 빠른 액션
        st.header("🚀 빠른 액션")
        
        if st.button("📋 데이터베이스 정보", use_container_width=True):
            with st.spinner("데이터베이스 정보를 가져오는 중..."):
                result = make_request("/database/info")
                if not result.get("success", False):
                    st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
                else:
                    # 세션 상태에 데이터베이스 정보 저장
                    st.session_state.sidebar_db_info = result.get("data", {})
                    st.session_state.sidebar_db_info_loaded = True
        
        # 사이드바에 저장된 데이터베이스 정보 표시
        if hasattr(st.session_state, 'sidebar_db_info_loaded') and st.session_state.sidebar_db_info_loaded:
            info = st.session_state.sidebar_db_info
            if isinstance(info, str):
                try:
                    info = eval(info)
                except:
                    st.error("데이터베이스 정보를 파싱할 수 없습니다.")
                    return
            
            st.success("✅ 데이터베이스 정보 로드 완료!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔗 연결 정보")
                # 작은 글씨로 메트릭 표시
                st.markdown("""
                <style>
                .small-metric {
                    font-size: 0.8em;
                    color: #666;
                    margin-bottom: 2px;
                }
                .small-value {
                    font-size: 0.9em;
                    font-weight: bold;
                    margin-bottom: 8px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # 데이터베이스
                st.markdown(f'<div class="small-metric">데이터베이스</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="small-value">{info.get("database_name", "N/A")}</div>', unsafe_allow_html=True)
                
                # 호스트
                st.markdown(f'<div class="small-metric">호스트</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="small-value">{info.get("host", "N/A")}</div>', unsafe_allow_html=True)
                
                # 포트
                st.markdown(f'<div class="small-metric">포트</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="small-value">{info.get("port", "N/A")}</div>', unsafe_allow_html=True)
                
                # 사용자
                st.markdown(f'<div class="small-metric">사용자</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="small-value">{info.get("user", "N/A")}</div>', unsafe_allow_html=True)
            
            with col2:
                st.subheader("📊 테이블 목록")
                tables = info.get("tables", [])
                if tables:
                    for table in tables:
                        st.write(f"• {table}")
                else:
                    st.write("테이블이 없습니다.")
            
            # 연결 상태
            status = info.get("connection_status", "unknown")
            if status == "connected":
                st.success("🟢 데이터베이스 연결됨")
            else:
                st.error("🔴 데이터베이스 연결 실패")
    
    # 메인 컨텐츠
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 자연어 쿼리", "⚡ 직접 SQL", "📋 데이터베이스 정보", "📊 테이블 스키마"])
    
    with tab1:
        st.header("🤖 자연어로 데이터베이스 질문하기")
        
        # 자연어 쿼리 입력
        query = st.text_area(
            "질문을 입력하세요",
            placeholder="예: 가장 비싼 상품을 주문한 사용자의 이름과 상품명을 조회해주세요",
            height=100
        )
        
        if st.button("🔍 질문하기", type="primary"):
            if query.strip():
                with st.spinner("AI가 SQL을 생성하고 실행하는 중..."):
                    result = make_request("/database/natural-query", {"question": query}, "POST")
                    
                    if not result.get("success", False):
                        st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
                    else:
                        st.success("✅ 쿼리 실행 완료!")
                        
                        data = result.get("data", {})
                        
                        # 생성된 SQL 표시
                        if "generated_sql" in data:
                            st.subheader("🔧 생성된 SQL")
                            st.code(data["generated_sql"], language="sql")
                        
                        # 결과 표시
                        if "result" in data:
                            display_dataframe(data["result"], "자연어 쿼리 결과")
                        elif "data" in data:
                            display_dataframe(data["data"], "자연어 쿼리 결과")
        
        st.info("💡 **팁**: 자연어로 데이터베이스에 질문하세요. AI가 자동으로 SQL을 생성하고 실행합니다.")
    
    with tab2:
        st.header("⚡ 직접 SQL 실행")
        
        # SQL 입력
        sql_query = st.text_area(
            "SQL 쿼리를 입력하세요",
            placeholder="SELECT * FROM users LIMIT 10;",
            height=150
        )
        
        if st.button("🚀 실행", type="primary"):
            if sql_query.strip():
                with st.spinner("SQL을 실행하는 중..."):
                    result = make_request("/database/execute", {"query": sql_query}, "POST")
                    
                    if not result.get("success", False):
                        error_msg = result.get('error', '알 수 없는 오류')
                        if "400" in error_msg or "Bad Request" in error_msg:
                            st.error(f"SQL 문법 오류: {error_msg}")
                            st.info("💡 **팁**: 테이블명이 MySQL 예약어인 경우 백틱(`)으로 감싸주세요. 예: `order`, `group`")
                        else:
                            st.error(f"오류: {error_msg}")
                    else:
                        st.success("✅ SQL 실행 완료!")
                        data = result.get("data", {})
                        display_dataframe(data, "SQL 실행 결과")
        
        st.info("💡 **팁**: 직접 SQL을 작성하여 더 정확한 쿼리를 실행할 수 있습니다.")
    
    with tab3:
        st.header("📋 데이터베이스 정보")
        
        if st.button("🔄 정보 새로고침", type="primary"):
            with st.spinner("데이터베이스 정보를 가져오는 중..."):
                result = make_request("/database/info")
                
                if not result.get("success", False):
                    st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
                else:
                    st.success("✅ 데이터베이스 정보 로드 완료!")
                    
                    # 데이터베이스 정보 표시
                    info = result.get("data", {})
                    if isinstance(info, str):
                        try:
                            info = eval(info)
                        except:
                            st.error("데이터베이스 정보를 파싱할 수 없습니다.")
                            return
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("🔗 연결 정보")
                        # 작은 글씨로 메트릭 표시
                        st.markdown("""
                        <style>
                        .small-metric {
                            font-size: 0.8em;
                            color: #666;
                            margin-bottom: 2px;
                        }
                        .small-value {
                            font-size: 0.9em;
                            font-weight: bold;
                            margin-bottom: 8px;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # 데이터베이스
                        st.markdown(f'<div class="small-metric">데이터베이스</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="small-value">{info.get("database_name", "N/A")}</div>', unsafe_allow_html=True)
                        
                        # 호스트
                        st.markdown(f'<div class="small-metric">호스트</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="small-value">{info.get("host", "N/A")}</div>', unsafe_allow_html=True)
                        
                        # 포트
                        st.markdown(f'<div class="small-metric">포트</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="small-value">{info.get("port", "N/A")}</div>', unsafe_allow_html=True)
                        
                        # 사용자
                        st.markdown(f'<div class="small-metric">사용자</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="small-value">{info.get("user", "N/A")}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.subheader("📊 테이블 목록")
                        tables = info.get("tables", [])
                        if tables:
                            for table in tables:
                                st.write(f"• {table}")
                        else:
                            st.write("테이블이 없습니다.")
                    
                    # 연결 상태
                    status = info.get("connection_status", "unknown")
                    if status == "connected":
                        st.success("🟢 데이터베이스 연결됨")
                    else:
                        st.error("🔴 데이터베이스 연결 실패")
    
    with tab4:
        st.header("📊 테이블 스키마 조회")
        
        # 테이블 선택
        table_name = st.text_input(
            "테이블 이름",
            placeholder="예: users, orders, post",
            help="스키마를 확인할 테이블 이름을 입력하세요"
        )
        
        if st.button("🔍 스키마 조회", type="primary"):
            if table_name.strip():
                with st.spinner(f"{table_name} 테이블의 스키마를 가져오는 중..."):
                    result = make_request("/database/table-schema", {"table_name": table_name}, "POST")
                    
                    if not result.get("success", False):
                        st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
                    else:
                        st.success(f"✅ {table_name} 테이블 스키마 로드 완료!")
                        
                        schema = result.get("data", {})
                        if isinstance(schema, str):
                            try:
                                schema = eval(schema)
                            except:
                                st.error("스키마 정보를 파싱할 수 없습니다.")
                                return
                        
                        if schema:
                            df = pd.DataFrame(schema)
                            st.dataframe(df, use_container_width=True)
                            
                            # 스키마 요약
                            st.subheader("📋 스키마 요약")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("총 컬럼 수", len(schema))
                            with col2:
                                primary_keys = len([col for col in schema if col.get("COLUMN_KEY") == "PRI"])
                                st.metric("기본키", primary_keys)
                            with col3:
                                nullable_cols = len([col for col in schema if col.get("IS_NULLABLE") == "YES"])
                                st.metric("NULL 허용", nullable_cols)
                        else:
                            st.warning("스키마 정보가 없습니다.")
    


if __name__ == "__main__":
    main() 