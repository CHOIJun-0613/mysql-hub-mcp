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
    page_title="Database Hub MCP Client",
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
    elif isinstance(data, dict):
        if "rows" in data:
            # {"rows": [...]} 형태인 경우
            rows = data["rows"]
        elif "result" in data:
            # {"result": [...], "sql_query": "..."} 형태인 경우
            rows = data["result"]
            
            # SQL 쿼리도 표시
            if "sql_query" in data:
                st.subheader("🔧 생성된 SQL")
                st.code(data["sql_query"], language="sql")
        elif "data" in data:
            # {"data": {...}} 형태인 경우 (중첩된 data 키)
            nested_data = data["data"]
            if isinstance(nested_data, dict) and "result" in nested_data:
                rows = nested_data["result"]
                
                # SQL 쿼리도 표시
                if "sql_query" in nested_data:
                    st.subheader("🔧 생성된 SQL")
                    st.code(nested_data["sql_query"], language="sql")
            else:
                st.error(f"❌ 중첩된 data 키의 내용을 처리할 수 없습니다: {nested_data}")
                return
        else:
            st.error(f"❌ 지원하지 않는 데이터 형식입니다. 키: {list(data.keys())}")
            return
    else:
        st.error(f"❌ 지원하지 않는 데이터 타입입니다. 예상: list/dict, 실제: {type(data)}")
        return
    
    # rows가 유효한 리스트인지 확인
    if not isinstance(rows, list):
        st.error(f"행 데이터 형식이 올바르지 않습니다. 예상: list, 실제: {type(rows)}")
        return
    
    if not rows:
        st.warning("표시할 데이터가 없습니다.")
        return
    
    # 첫 번째 행이 딕셔너리인지 확인
    if rows and not isinstance(rows[0], dict):
        st.error(f"행 데이터 형식이 올바르지 않습니다. 예상: dict, 실제: {type(rows[0])}")
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
    st.markdown('<h1 class="main-header">🗄️ DataBase(MySQL, PostgreSQL, Oracle) Hub MCP Client</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 서버 URL 설정
        server_url = st.text_input(
            "서버 URL",
            value=SERVER_URL,
            help="Database Hub MCP 서버의 URL을 입력하세요"
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
            
            # 데이터 타입 검증 및 변환
            if isinstance(info, str):
                try:
                    # 문자열을 파이썬 객체로 변환 시도
                    import ast
                    info = ast.literal_eval(info)
                except (ValueError, SyntaxError):
                    try:
                        # eval 대신 ast.literal_eval 사용 (더 안전함)
                        info = eval(info)
                    except:
                        st.error("데이터베이스 정보를 파싱할 수 없습니다.")
                        return
            
            # info가 유효한 딕셔너리인지 확인
            if not isinstance(info, dict):
                st.error(f"데이터베이스 정보 형식이 올바르지 않습니다. 예상: dict, 실제: {type(info)}")
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
                st.subheader("📊 데이터베이스 상태")
                # 연결 상태
                status = info.get("connection_status", "unknown")
                if status == "connected":
                    st.success("🟢 데이터베이스 연결됨")
                else:
                    st.error("🔴 데이터베이스 연결 실패")
                
                # 테이블 수 표시
                tables = info.get("tables", [])
                if tables:
                    st.metric("총 테이블 수", len(tables))
                else:
                    st.metric("총 테이블 수", 0)
    
    # 메인 컨텐츠
    # 활성 탭 관리 - Streamlit에서는 직접적인 탭 인덱스 제어가 불가능하므로
    # 세션 상태를 통해 스키마 탭으로 이동할 때 자동 조회하도록 처리
    
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
                        
                        # 결과 표시
                        display_dataframe(data, "자연어 쿼리 결과")
        
        st.info("💡 **팁**: 자연어로 데이터베이스에 질문하세요. AI가 자동으로 SQL을 생성하고 실행합니다.")
    
    with tab2:
        st.header("⚡ 직접 SQL 실행")
        
        # SQL 입력
        sql_query = st.text_area(
            "SQL 쿼리를 입력하세요",
            placeholder="SELECT * FROM users LIMIT 10;",
            height=150,
            help="💡 **SQL 작성 팁**:\n• 테이블명은 백틱(`)으로 감싸거나 그냥 입력하세요\n• 예약어 테이블명: `order`, `group`, `user` 등\n• 문자열 값만 작은따옴표(') 사용\n• 세미콜론(;)은 선택사항"
        )
        
        # SQL 예시 버튼들
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 기본 예시", use_container_width=True):
                st.session_state.sql_example = "SELECT * FROM users LIMIT 5"
        with col2:
            if st.button("🔍 조건 검색", use_container_width=True):
                st.session_state.sql_example = "SELECT * FROM orders WHERE status = 'completed'"
        with col3:
            if st.button("📊 집계 쿼리", use_container_width=True):
                st.session_state.sql_example = "SELECT COUNT(*) as total FROM users"
        
        # SQL 입력 실시간 검증 및 제안
        if sql_query.strip():
            # 테이블명에 작은따옴표가 잘못 사용된 경우 감지
            if "'" in sql_query and "from" in sql_query.lower():
                # FROM 절에서 테이블명 추출
                import re
                from_match = re.search(r'from\s+[\'"`]?(\w+)[\'"`]?\s', sql_query.lower())
                if from_match:
                    table_name = from_match.group(1)
                    if f"'{table_name}'" in sql_query:
                        st.warning(f"⚠️ **주의**: 테이블명 '{table_name}'에 작은따옴표를 사용했습니다.")
                        corrected_sql = sql_query.replace(f"'{table_name}'", f"`{table_name}`")
                        st.info(f"💡 **수정 제안**: `{corrected_sql}`")
                        if st.button("✅ 수정된 SQL 사용", type="secondary"):
                            st.session_state.sql_example = corrected_sql
                            st.rerun()
        
        # 예시 SQL이 선택된 경우 표시
        if hasattr(st.session_state, 'sql_example'):
            st.info(f"💡 **선택된 예시**: `{st.session_state.sql_example}`")
            if st.button("✅ 이 예시 사용", type="secondary"):
                sql_query = st.session_state.sql_example
                st.rerun()
        
        if st.button("🚀 실행", type="primary"):
            if sql_query.strip():
                with st.spinner("SQL을 실행하는 중..."):
                    result = make_request("/database/execute", {"query": sql_query}, "POST")
                    
                    if not result.get("success", False):
                        error_msg = result.get('error', '알 수 없는 오류')
                        if "400" in error_msg or "Bad Request" in error_msg:
                            st.error(f"SQL 문법 오류: {error_msg}")
                            st.info("💡 **SQL 작성 가이드**:\n• 테이블명: `orders` (백틱 사용) 또는 orders (그냥 입력)\n• 문자열 값: 'completed' (작은따옴표 사용)\n• 예약어 테이블명은 반드시 백틱(`)으로 감싸기")
                        else:
                            st.error(f"오류: {error_msg}")
                    else:
                        st.success("✅ SQL 실행 완료!")
                        data = result.get("data", {})
                        display_dataframe(data, "SQL 실행 결과")
        
        st.info("💡 **SQL 작성 규칙**:\n• 테이블명: `orders`, `users` (백틱 권장)\n• 문자열 값: 'completed', 'active' (작은따옴표)\n• 숫자 값: 100, 5 (따옴표 없음)\n• 예약어 테이블명은 반드시 백틱(`) 사용")
    
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
                    
                    # 데이터 타입 검증 및 변환
                    if isinstance(info, str):
                        try:
                            # 문자열을 파이썬 객체로 변환 시도
                            import ast
                            info = ast.literal_eval(info)
                        except (ValueError, SyntaxError):
                            try:
                                # eval 대신 ast.literal_eval 사용 (더 안전함)
                                info = eval(info)
                            except:
                                st.error("데이터베이스 정보를 파싱할 수 없습니다.")
                                return
                    
                    # info가 유효한 딕셔너리인지 확인
                    if not isinstance(info, dict):
                        st.error(f"데이터베이스 정보 형식이 올바르지 않습니다. 예상: dict, 실제: {type(info)}")
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
                        st.subheader("📊 테이블 통계")
                        tables = info.get("tables", [])
                        if tables:
                            # 테이블 통계 계산
                            total_tables = len(tables)
                            
                            # 테이블 데이터를 표 형태로 변환하여 설명 정보 추출
                            if isinstance(tables[0], dict):
                                # 딕셔너리 형태인 경우 (TABLE_NAME, TABLE_COMMENT 등)
                                table_data = []
                                for table in tables:
                                    table_name = table.get("TABLE_NAME", str(table))
                                    table_comment = table.get("TABLE_COMMENT", "")
                                    table_data.append({
                                        "테이블명": table_name,
                                        "설명": table_comment or "설명 없음"
                                    })
                            else:
                                # 문자열 형태인 경우
                                table_data = [{"테이블명": str(table), "설명": ""} for table in tables]
                            
                            # 통계 계산
                            tables_with_comment = len([t for t in table_data if t["설명"] and t["설명"] != "설명 없음"])
                            tables_without_comment = total_tables - tables_with_comment
                            
                            # 연결 상태
                            status = info.get("connection_status", "unknown")
                            if status == "connected":
                                st.success("🟢 데이터베이스 연결됨")
                            else:
                                st.error("🔴 데이터베이스 연결 실패")
                            
                            # 테이블 통계 메트릭
                            st.metric("전체 테이블", total_tables)
                            st.metric("설명 있는 테이블", tables_with_comment)
                            st.metric("설명 없는 테이블", tables_without_comment)
                        else:
                            st.metric("전체 테이블", 0)
                            st.metric("설명 있는 테이블", 0)
                            st.metric("설명 없는 테이블", 0)
                    
                    # 테이블 목록을 연결정보 하단으로 이동
                    st.subheader("📋 테이블 목록")
                    tables = info.get("tables", [])
                    if tables:
                        # 테이블 데이터를 표 형태로 변환
                        if isinstance(tables[0], dict):
                            # 딕셔너리 형태인 경우 (TABLE_NAME, TABLE_COMMENT 등)
                            table_data = []
                            for table in tables:
                                table_name = table.get("TABLE_NAME", str(table))
                                table_comment = table.get("TABLE_COMMENT", "")
                                table_data.append({
                                    "테이블명": table_name,
                                    "설명": table_comment or "설명 없음"
                                })
                        else:
                            # 문자열 형태인 경우
                            table_data = [{"테이블명": str(table), "설명": ""} for table in tables]
                        
                        # 페이지네이션
                        items_per_page = 25
                        total_tables = len(table_data)
                        total_pages = (total_tables + items_per_page - 1) // items_per_page
                        
                        if total_pages > 1:
                            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
                            with col_page2:
                                current_page = st.selectbox(
                                    f"페이지 (총 {total_pages}페이지)",
                                    range(1, total_pages + 1),
                                    key="main_table_page"
                                )
                        else:
                            current_page = 1
                        
                        # 현재 페이지의 테이블 표시
                        start_idx = (current_page - 1) * items_per_page
                        end_idx = start_idx + items_per_page
                        current_tables = table_data[start_idx:end_idx]
                        
                        # 테이블 목록 표시
                        if current_tables:
                            df = pd.DataFrame(current_tables)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            # 페이지 정보 표시
                            if total_pages > 1:
                                st.caption(f"📄 {start_idx + 1}-{min(end_idx, total_tables)} / {total_tables} 테이블 (페이지 {current_page}/{total_pages})")
                            else:
                                st.caption(f"📊 총 {total_tables}개 테이블")
                            
                            # 스키마 조회 안내
                            st.info("💡 **스키마 조회**: '📊 테이블 스키마' 탭에서 테이블명을 입력하여 스키마를 확인할 수 있습니다.")
                        else:
                            st.write("테이블이 없습니다.")
                    else:
                        st.write("테이블이 없습니다.")
    
    with tab4:
        st.header("📊 테이블 스키마 조회")
        
        # 테이블 선택
        table_name = st.text_input(
            "테이블 이름",
            placeholder="예: users, orders, post",
            help="스키마를 확인할 테이블 이름을 입력하세요"
        )
        
        # 빠른 테이블 선택 (최근 사용한 테이블들)
        if hasattr(st.session_state, 'recent_tables'):
            recent_tables = st.session_state.recent_tables
            if recent_tables:
                st.subheader("🕒 최근 사용한 테이블")
                cols = st.columns(min(5, len(recent_tables)))
                for i, recent_table in enumerate(recent_tables[:5]):
                    with cols[i]:
                        if st.button(recent_table, key=f"recent_{recent_table}"):
                            table_name = recent_table
                            st.rerun()
        
        if st.button("🔍 스키마 조회", type="primary"):
            if table_name.strip():
                # 최근 사용한 테이블에 추가
                if not hasattr(st.session_state, 'recent_tables'):
                    st.session_state.recent_tables = []
                if table_name not in st.session_state.recent_tables:
                    st.session_state.recent_tables.insert(0, table_name)
                    # 최대 10개까지만 유지
                    st.session_state.recent_tables = st.session_state.recent_tables[:10]
                
                with st.spinner(f"{table_name} 테이블의 스키마를 가져오는 중..."):
                    result = make_request("/database/table-schema", {"table_name": table_name}, "POST")
                    
                    if not result.get("success", False):
                        st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
                    else:
                        st.success(f"✅ {table_name} 테이블 스키마 로드 완료!")
                        
                        schema = result.get("data", {})
                        
                        # 스키마 데이터 타입 검증 및 변환
                        if isinstance(schema, str):
                            try:
                                # 문자열을 파이썬 객체로 변환 시도
                                import ast
                                schema = ast.literal_eval(schema)
                            except (ValueError, SyntaxError):
                                try:
                                    # eval 대신 ast.literal_eval 사용 (더 안전함)
                                    schema = eval(schema)
                                except:
                                    st.error("스키마 정보를 파싱할 수 없습니다.")
                                    return
                        
                        # 스키마가 유효한 딕셔너리인지 확인
                        if not isinstance(schema, dict):
                            st.error(f"스키마 데이터 형식이 올바르지 않습니다. 예상: dict, 실제: {type(schema)}")
                            return
                        
                        # COLUMNS 키에서 컬럼 배열 추출
                        columns = schema.get("COLUMNS", [])
                        if not isinstance(columns, list):
                            st.error(f"컬럼 데이터 형식이 올바르지 않습니다. 예상: list, 실제: {type(columns)}")
                            return
                        
                        if columns and len(columns) > 0:
                            # 첫 번째 항목이 딕셔너리인지 확인
                            if not isinstance(columns[0], dict):
                                st.error(f"컬럼 데이터 형식이 올바르지 않습니다. 예상: dict, 실제: {type(columns[0])}")
                                return
                            
                            # 테이블 정보 표시
                            st.subheader(f"📋 테이블 정보")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("테이블명", schema.get("TABLE_NAME", "N/A"))
                            with col2:
                                st.metric("테이블 설명", schema.get("TABLE_COMMENT", "N/A") or "설명 없음")
                            
                            # 컬럼 정보를 데이터프레임으로 표시
                            st.subheader(f"🔧 컬럼 정보")
                            df = pd.DataFrame(columns)
                            st.dataframe(df, use_container_width=True)
                            
                            # 스키마 요약
                            st.subheader("📊 스키마 요약")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("총 컬럼 수", len(columns))
                            with col2:
                                # 안전한 기본키 계산
                                try:
                                    primary_keys = len([col for col in columns if isinstance(col, dict) and col.get("COLUMN_KEY") == "PRI"])
                                except:
                                    primary_keys = 0
                                st.metric("기본키", primary_keys)
                            with col3:
                                # 안전한 NULL 허용 컬럼 계산
                                try:
                                    nullable_cols = len([col for col in columns if isinstance(col, dict) and col.get("IS_NULLABLE") == "YES"])
                                except:
                                    nullable_cols = 0
                                st.metric("NULL 허용", nullable_cols)
                        else:
                            st.warning("컬럼 정보가 없습니다.")
    


if __name__ == "__main__":
    main() 