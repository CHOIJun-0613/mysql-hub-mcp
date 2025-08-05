## LLM에  database정보와 테이블 schema 정보를  system prompt에 포함해서 전달하는 방법 대신에, 모델에게 Tool을 사용해서 DB table 정보를 획득하게 하려고 함.
- 이유: prompt에 포함해서 전달하는 사이즈 한계가 있는데, 테이블이 많아지면 prompt를 통해 전달이 어려워질 수 있음.
- groq나 ollama provider 둘 다 적용
- 관련 소스 파일: sever/ai_provider.py, server/database.py

##모델에 전달할 Tool 목록: database.py에 정의되어 있음
- get_database_info: """데이터베이스 정보를 반환합니다."""
- get_table_list: """데이터베이스의 모든 테이블 목록을 반환합니다."""
- get_table_schema: """테이블 스키마 정보를 반환합니다."""

## 참고 소스 sample: 아래 코드 내용은 참고만 하고 지금 프로젝트에 맞게 반영해 줄것
<참고소스 시작>
import ollama
import mysql.connector
from mysql.connector import Error
import json
import pandas as pd

# --- 1. MySQL 연결 정보 설정 ---
# 사용자의 실제 MySQL 데이터베이스 정보로 수정하세요.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'your_database'
}

def create_db_connection():
    """MySQL 데이터베이스 연결을 생성하고 반환합니다."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("MySQL 데이터베이스에 성공적으로 연결되었습니다.")
            return connection
    except Error as e:
        print(f"'{e}' 오류로 인해 연결에 실패했습니다.")
        return None

# --- 2. LLM이 사용할 도구(Tools) 정의 ---
# 각 함수의 docstring은 LLM이 함수의 용도와 파라미터를 이해하는 데 매우 중요합니다.

def list_tables() -> str:
    """
    현재 데이터베이스에 있는 모든 테이블의 목록을 반환합니다.
    이 함수는 인자가 필요 없습니다.
    """
    conn = create_db_connection()
    if not conn:
        return json.dumps({"error": "데이터베이스에 연결할 수 없습니다."})
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return json.dumps({"tables": tables})

def get_table_schema(table_names: list[str]) -> str:
    """
    주어진 테이블 이름 목록에 대한 스키마(CREATE TABLE 구문)를 반환합니다.
    :param table_names: 스키마를 조회할 테이블 이름의 리스트. 예: ["customers", "orders"]
    """
    conn = create_db_connection()
    if not conn:
        return json.dumps({"error": "데이터베이스에 연결할 수 없습니다."})
        
    schemas = {}
    cursor = conn.cursor()
    for table_name in table_names:
        try:
            cursor.execute(f"SHOW CREATE TABLE {table_name};")
            row = cursor.fetchone()
            if row:
                schemas[table_name] = row[1]
            else:
                schemas[table_name] = f"'{table_name}' 테이블을 찾을 수 없습니다."
        except Error as e:
            schemas[table_name] = f"'{table_name}' 스키마 조회 중 오류 발생: {e}"
    conn.close()
    return json.dumps({"schemas": schemas})

def execute_sql_query(sql: str) -> str:
    """
    보안상의 이유로 SELECT 문만 실행하여 그 결과를 반환합니다.
    :param sql: 실행할 SELECT SQL 쿼리 문자열.
    """
    if not sql.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "보안 정책에 따라 SELECT 쿼리만 실행할 수 있습니다."})
    
    conn = create_db_connection()
    if not conn:
        return json.dumps({"error": "데이터베이스에 연결할 수 없습니다."})
        
    try:
        # pandas를 사용하여 결과를 보기 좋은 형식으로 읽어옵니다.
        df = pd.read_sql_query(sql, conn)
        result = df.to_string()
        return json.dumps({"result": result})
    except Error as e:
        return json.dumps({"error": f"SQL 실행 중 오류 발생: {e}"})
    finally:
        conn.close()


# --- 3. 메인 에이전트 실행 로직 ---

def run_text_to_sql_agent(query: str):
    """사용자의 자연어 쿼리를 받아 SQL을 생성하고 실행하는 에이전트"""
    
    client = ollama.Client()
    
    # LLM과의 대화를 관리하기 위한 메시지 히스토리
    messages = [
        {
            'role': 'system',
            'content': '당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다. '
 
        },
        {
            'role': 'user',
            'content': query
        }
    ]
    
    print(f"\n[사용자 쿼리] \"{query}\"")

    while True:
        # Ollama 클라이언트에 메시지 히스토리와 도구 목록을 전달
        response = client.chat(
            model='llama3:8b', 
            messages=messages,
            tools=[
                # LLM이 사용할 수 있는 도구 목록을 JSON 형식으로 정의
                {
                    'type': 'function',
                    'function': {
                        'name': 'list_tables',
                        'description': '데이터베이스의 모든 테이블 목록을 가져옵니다.',
                        'parameters': {} # 인자가 없는 경우
                    },
                },
                {
                    'type': 'function',
                    'function': {
                        'name': 'get_table_schema',
                        'description': '지정된 테이블들의 스키마(CREATE TABLE 구문)를 가져옵니다.',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'table_names': {
                                    'type': 'array',
                                    'items': {'type': 'string'},
                                    'description': '스키마를 조회할 테이블 이름의 리스트',
                                },
                            },
                            'required': ['table_names'],
                        },
                    },
                },
                {
                    'type': 'function',
                    'function': {
                        'name': 'execute_sql_query',
                        'description': '데이터 조회를 위한 SELECT SQL 쿼리를 실행합니다.',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'sql': {
                                    'type': 'string',
                                    'description': '실행할 SELECT SQL 쿼리',
                                },
                            },
                            'required': ['sql'],
                        },
                    },
                },
            ]
        )
        
        # LLM의 응답을 메시지 히스토리에 추가
        messages.append(response['message'])

        # LLM이 도구 사용을 요청했는지 확인
        if not response['message'].get('tool_calls'):
            print("\n[최종 LLM 답변]")
            print(response['message']['content'])
            break # 도구 사용 요청이 없으면 루프 종료

        # LLM이 요청한 도구들을 실행
        tool_calls = response['message']['tool_calls']
        print(f"\n[LLM의 판단] 다음 도구를 사용해야 합니다: {[tc['function']['name'] for tc in tool_calls]}")

        for tool_call in tool_calls:
            func_name = tool_call['function']['name']
            func_args = tool_call['function']['arguments']
            
            print(f"  - 함수: {func_name}, 인자: {func_args}")
            
            # 함수 이름에 따라 실제 Python 함수를 호출
            if func_name == 'list_tables':
                result = list_tables()
            elif func_name == 'get_table_schema':
                result = get_table_schema(**func_args)
            elif func_name == 'execute_sql_query':
                result = execute_sql_query(**func_args)
            else:
                result = json.dumps({"error": f"알 수 없는 함수 '{func_name}'"})

            # 도구 실행 결과를 'tool' 역할로 메시지 히스토리에 추가
            messages.append({
                'role': 'tool',
                'content': result,
                'tool_call_id': tool_call['id'] # 어떤 도구 호출에 대한 결과인지 명시
            })


# --- 4. 메인 실행 부분 ---
if __name__ == "__main__":
    # 먼저 DB 연결이 가능한지 테스트
    if create_db_connection():
        # 에이전트 실행
        user_query = "가장 최근에 가입한 고객 2명의 이름과 이메일 주소를 알려줘."
        run_text_to_sql_agent(user_query)
<참고소스 끝>