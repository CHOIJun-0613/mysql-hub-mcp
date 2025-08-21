# ------------------------------------------------------------------------------
# 파일: agent.py
# ------------------------------------------------------------------------------
# 목적:
# Google ADK LLM Agent를 로드하고 구성하는 AgentWrapper 클래스를 정의합니다.
# 이 클래스는 MCP 서버와 통신할 수 있으며 (HTTP 또는 STDIO를 통해),
# 초기화 중에 각 서버별로 로드된 도구를 rich print를 사용하여 로깅합니다.
# ------------------------------------------------------------------------------

import asyncio
from rich import print  # 컬러 터미널 로깅을 위해 사용
from dotenv import load_dotenv

# ADK의 내장 LLM agent 클래스
from google.adk.agents.llm_agent import LlmAgent

# MCP 서버에서 호스팅되는 도구에 대한 접근을 제공
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

# 다양한 유형의 MCP 서버에 대한 연결 설정
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool import StdioConnectionParams

# Non-Google LLM을 연결하기 위한 LiteLLM 래퍼
from google.adk.models.lite_llm import LiteLlm

# config.json 파일을 읽기 위한 유틸리티 함수
try:
    from utilities import read_config_json
except ImportError:
    # 상대 import 시도
    try:
        from .utilities import read_config_json
    except ImportError:
        # 절대 경로 import 시도
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from utilities import read_config_json

# ------------------------------------------------------------------------------
# 설정 상수
# ------------------------------------------------------------------------------

# ADK 앱 식별자 (세션이나 도구를 등록할 때 사용)
APP_NAME = "mysql_assistant"

# 현재 세션을 위한 고유 사용자 ID
USER_ID = "mysql_assistant_001"

# 고유 세션 ID (여러 세션을 재개하거나 구분하는 데 도움이 됨)
SESSION_ID = "session_001"

#클라이언트가 사용할 수 있는 도구 세트 정의

READ_ONLY_TOOLS = [
    'execute_sql',
    'natural_language_query',
    'get_database_info',
    'get_table_list',
    'get_table_schema'
]

SYSTEM_PROMPT = """
## 당신은 MySQL 데이터베이스 전문가 AI 비서입니다.

## 🚨 중요 규칙
- **동일한 도구를 반복해서 호출하지 마세요**
- **한 번에 하나의 도구만 호출하세요**
- **사용자 질문에 대해 단계별로 진행하세요**
- **각 단계가 완료되면 다음 단계로 진행하세요**
- **SQL 작성 시 존재하지 않은 테이블과 컬럼은 사용하지 마세요** 
- **사용자의 질의에 답변이 완료되면 다음 질의를 받을때까지 대기하세요**

## 📋 도구 사용 순서 (반드시 이 순서를 따르세요)

### 1단계: 데이터베이스 구조 파악
1. `get_table_list()` - 전체 테이블 목록 확인 (한 번만 호출)
2. 사용자 질의를 분석해서 관련 테이블을 추론한다.

### 2단계: 관련 테이블 스키마 확인 및 SQL 쿼리 작성
1. `get_table_schema("table_name")` - 사용자 질문과 관련된 테이블의 스키마 확인
** 관련된 테이블에서 필요하다고 판단하는 테이블들에 대해 `get_table_schema("table_name")` 호출**
2. 스키마 정보를 바탕으로 **직접 SQL 문을 작성**하세요
3. SQL문을 작성할 때는 스키마 정보를 기준으로 작성하세요, 
4. 테이블 리스트에 없는 테이블이나 스키마 정보에 없는 컬럼을 절대 사용하지 마세요.

### 3단계: SQL 쿼리 작성 및 실행
1. `execute_sql("SQL문")` - 작성한 SQL 실행
2. `execute_sql("SQL문")` 호출 결과를 받으면 도구 호출을 멈추고 수집된 정보를 종합하여 사용자에게 답변합니다.
3. `execute_sql("SQL문")`을 호출했으면 natural_language_query(query)를 호출하지 마세요 
4. `execute_sql("SQL문")`을 호출 결과를 확인하고 사용자에게 SQL문과 그 결과를 반환
5. `execute_sql("SQL문")`을 호출 결과를 표시할 때는 테이블 형태로 표시하세요
** 주의: 
- SQL문이 정상적으로 작성하지 못한 경우에만 `natural_language_query(query)`도구 사용
- execute_sql() 도구 사용이 적절하지 않은 경우에만 `natural_language_query(query)`도구 사용
- execute_sql() 도구 사용후에는 절대 도구 호출 형식의 코드를 포함하지 마세요.

### 4단계: 결과 확인 및 사용자 질의 답변
1. 사용자 질의에 답변이 완료되면 다음 질의를 받을때까지 대기하세요

## 🔧 사용 가능한 도구
- `get_table_list()` - 테이블 목록 확인 (한 번만!)
- `get_table_schema(table_name)` - 테이블 스키마 확인(필요시 관련 테이블 수 만큼 호출)
- `execute_sql(sql)` - SQL 실행(한 번만!)
- `natural_language_query(query)` - 복잡한 자연어 질의 (필요할 때만 호출)

## ❌ 금지사항
- 같은 도구를 연속으로 반복해서 호출하지 마세요
- 불필요한 반복을 하지 마세요
- 한 번에 여러 도구를 동시에 호출하지 마세요
- `get_table_list()`를 여러 번 호출하지 마세요
- 같은 테이블에 대해서 `get_table_schema(table_name)`를 반복해서 호출하지 마세요
- `execute_sql()` 호출 후 사용자에게 마지막 결과를 반한할 때는 절대 도구 호출형식의 코드를 포함하지 마세요
- `execute_sql()` 호출 후 결과를 확인하고 사용자에게 그 결과를 반환하고 절대 다른 도구 호출을 하지 마세요
- 'execute_sql()' 호출 후 'natural_language_query()'를 호출하지 마세요

## ✅ 올바른 응답 패턴
각 도구 호출 후 결과를 확인하고, 다음 단계로 진행하세요. 
**예시**
User: "가장 많이 구매한 사용자는 누구야?"
Assistant: tool_calls: [get_table_list()]
Tool: result: [...]
Assistant: tool_calls: [get_table_schema(...)]
Tool: result: [...]
Assistant: tool_calls: [execute_sql(...)]
Tool: result: [{"user_name": "홍길동", ...}]
Assistant: "가장 많이 구매한 사용자는 홍길동 님입니다."
"""
ENG_SYSTEM_PROMPT = """
## You are an AI assistant who is an expert on MySQL databases.

🚨 Important Rules
You must answer in Korean.
Do not call the same tool repeatedly.
Call only one tool at a time.
Proceed step-by-step with the user's query.
Once each step is complete, proceed to the next step.
When writing SQL, do not use tables or columns that do not exist.
After you have finished answering the user's query, wait until you receive the next query.

📋 Tool Usage Sequence (You MUST follow this sequence)
Step 1: Understand the Database Structure
get_table_list() - Check the full list of tables (Call only once).
Analyze the user's query to infer the relevant tables.

Step 2: Check Relevant Table Schemas and Compose the SQL Query
get_table_schema("table_name") - Check the schemas of tables relevant to the user's question.
** Call get_table_schema("table_name") for all tables you determine are necessary from the list of relevant tables.**
Based on the schema information, write the SQL statement yourself.
When writing the SQL statement, base it on the schema information.
Never use tables that are not in the table list or columns that are not in the schema information.

Step 3: Compose and Execute the SQL Query
execute_sql("SQL_statement") - Execute the SQL you have written.
After receiving the result from the execute_sql("SQL_statement") call, stop calling tools and synthesize the collected information to answer the user.
If you have called execute_sql("SQL_statement"), do not call natural_language_query(query).
After calling execute_sql("SQL_statement"), verify the result and return the SQL statement and its result to the user.
When displaying the result of the execute_sql("SQL_statement") call, display it in a table format.

** Note:
Only use the natural_language_query(query) tool if you could not correctly write the SQL statement.
Only use the natural_language_query(query) tool if using the execute_sql() tool is not appropriate.
After using the execute_sql() tool, never include code in the tool-calling format in your final response.

Step 4: Confirm the Result and Answer the User's Query
After you have finished answering the user's query, wait until you receive the next query.

🔧 Available Tools
get_table_list() - Check the list of tables (Only once!)
get_table_schema(table_name) - Check a table's schema (Call as many times as necessary for relevant tables)
execute_sql(sql) - Execute SQL (Only once!)
natural_language_query(query) - For complex natural language queries (Call only when necessary)

❌ Forbidden Actions
Do not call the same tool consecutively and repeatedly.
Do not perform unnecessary repetitions.
Do not call multiple tools at the same time.
Do not call get_table_list() multiple times.
Do not call get_table_schema(table_name) repeatedly for the same table.
After calling execute_sql(), when returning the final result to the user, absolutely do not include anything in the tool-calling format.
After calling execute_sql(), verify the result, return it to the user, and do not call any other tools.
Do not call natural_language_query() after calling execute_sql().

✅ Correct Response Pattern
After each tool call, check the result and proceed to the next step.
**Example**
User: "Who is the user that purchased the most?"
Assistant: tool_calls: [get_table_list()]
Tool: result: [...]
Assistant: tool_calls: [get_table_schema(...)]
Tool: result: [...]
Assistant: tool_calls: [execute_sql(...)]
Tool: result: [{"user_name": "Hong Gildong", ...}]
Assistant: "The user who purchased the most is Hong Gildong."
"""

# 환경 변수 로드
load_dotenv()
# 모델 이름 설정
# Google Gemini 모델
GEMINI_MODEL_NAME = "gemini-1.5-flash"

# Ollama 로컬 모델들
QWEN_MODEL_NAME = "ollama/qwen2.5-coder:latest"
LLAMA_MODEL_NAME = "ollama/llama3.1:8b"

# LMStudio 로컬 모델 (localhost:1234에서 실행)
LMSTUDIO_QWEN_MODEL_NAME = "lm_studio/qwen/qwen3-8b"  # LMStudio에서 사용할 모델명
# ------------------------------------------------------------------------------
# 클래스: AgentWrapper
# ------------------------------------------------------------------------------
# Google ADK agent와 MCP 도구 세트를 로드하고 관리합니다.
# 다음을 처리합니다:
# - MCP 서버 설정 읽기
# - 해당 서버에 연결
# - 사용 가능한 도구 필터링 및 연결
# - 각 서버에 대한 도구 정보 출력
# ------------------------------------------------------------------------------

class AgentWrapper:
    def __init__(self, tool_filter=None):
        """
        래퍼를 초기화하지만 아직 agent를 빌드하지는 않습니다.
        설정을 완료하려면 이 후에 `await self.build()`를 호출해야 합니다.

        Args:
            tool_filter (list[str] or None): 허용할 도구 이름의 선택적 목록.
                                             지정된 경우 이 도구들만 로드됩니다.
        """
        self.tool_filter = READ_ONLY_TOOLS
        self.agent = None          # 빌드 후 최종 LlmAgent를 보관
        self._toolsets = []        # 빈 리스트로 초기화

    def build(self):
        """
        LlmAgent를 빌드합니다:
        - 설정에 나열된 모든 MCP 서버에 연결
        - 각 서버에서 도구 로드
        - 해당 도구로 ADK agent 초기화

        `self.agent`를 사용하기 전에 호출되어야 합니다.
        """
        toolsets = self._load_toolsets()

        # 로드된 도구세트로 ADK LLM Agent 구성
        # self.agent = LlmAgent(
        #     model=GEMINI_MODEL_NAME,  # agent를 구동할 모델 선택
        #     name="mysql_assistant",
        #     instruction=SYSTEM_PROMPT,
        #     tools=toolsets
        # )
        
        # LiteLlm 클래스를 사용하여 Ollama에서 제공하는 모델을 지정합니다.
        # 'ollama/' 접두사를 사용하고 모델 이름을 명시합니다.
        #local_llama_model = LiteLlm(model=LLAMA_MODEL_NAME)
        #llmodel = LiteLlm(model=QWEN_MODEL_NAME)
        
        # LMStudio를 사용하여 qwen/qwen3-8b 모델을 지정합니다.
        lmstudio_model = LiteLlm(
            model=LMSTUDIO_QWEN_MODEL_NAME,  # LMStudio는 OpenAI 호환 모델명을 사용
            api_base="http://localhost:1234/v1",  # LMStudio 기본 API 엔드포인트
            api_key="not-needed" # API 키가 필요 없음을 명시적으로 표시
        )
        
        self.agent = LlmAgent(
            model=lmstudio_model,  # agent를 구동할 모델 선택
            name="mysql_assistant",
            instruction=ENG_SYSTEM_PROMPT,
            tools=toolsets
        )
        
        
        self._toolsets = toolsets  # 나중에 정리를 위해 도구세트 저장


    def _load_toolsets(self):
        """
        config.json에서 MCP 서버 정보를 읽고 각각에서 도구세트를 로드합니다.

        각 유효한 서버에 대해:
        - HTTP 또는 STDIO를 사용하여 연결
        - 도구 필터링 (해당하는 경우)
        - 사용자를 위해 도구 이름 출력

        Returns:
            agent에서 사용할 준비가 된 MCPToolset 객체 목록.
        """
        config = read_config_json()  # 설정 파일에서 서버 정보 로드
         
        toolsets = []

        for name, server in config.get("mcpServers", {}).items():
            try:
                # 연결 방법 결정
                if server.get("type") == "http":
                    # HTTP 연결 시 인증 설정을 headers로 처리
                    headers = None
                    if server.get("auth"):
                        auth = server["auth"]
                        if auth.get("scheme") == "bearer" and auth.get("token"):
                            headers = {"Authorization": f"Bearer {auth['token']}"}
                        elif auth.get("scheme") == "basic" and auth.get("username") and auth.get("password"):
                            import base64
                            credentials = base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
                            headers = {"Authorization": f"Basic {credentials}"}
                        elif auth.get("scheme") == "header" and auth.get("token"):
                            headers = {auth.get("header_name", "X-API-Key"): auth["token"]}
                    
                    conn = StreamableHTTPServerParams(
                        url=server["url"],
                        headers=headers
                    )

                elif server.get("type") == "stdio":
                    # StdioConnectionParams 사용법이 변경되었을 수 있음
                    # 임시로 주석 처리
                    # conn = StdioConnectionParams(
                    #     command=server["command"],
                    #     args=server["args"],
                    #     timeout=5
                    # )
                    print(f"[yellow]⚠️  STDIO 서버 '{name}'는 현재 지원되지 않습니다.[/yellow]")
                    continue
                else:
                    raise ValueError(f"[red]❌ 설정에서 알 수 없는 서버 유형: '{server['type']}'[/red]")

                # 선택된 연결로 도구세트 생성 및 연결
                toolset = MCPToolset(
                    connection_params=conn,
                    tool_filter=self.tool_filter
                )

                # Fetch tool list and print it nicely
                print(f"[bold green]✅ Tools loaded from server [cyan]'{name}'[/cyan]:[/bold green]")

                toolsets.append(toolset)

            except Exception as e:
                print(f"[bold red]⚠️  오류로 인해 서버 '{name}' 건너뛰기:[/bold red] {e}")

        return toolsets


    async def close(self):
        """
        각 로드된 도구세트를 우아하게 종료합니다.
        남은 백그라운드 작업이나 리소스를 방지하기 위해 중요합니다.
        """
        for toolset in self._toolsets:
            try:
                await toolset.close()  # 각 도구세트의 연결 정리
            except Exception as e:
                print(f"[yellow]⚠️ 도구세트 종료 중 오류:[/yellow] {e}")

        # 취소 및 정리가 완료되도록 작은 지연
        await asyncio.sleep(1.0)
        

agent_wrapper = AgentWrapper()
agent_wrapper.build()
root_agent = agent_wrapper.agent