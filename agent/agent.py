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
from agent.utilities import read_config_json


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
        self.tool_filter = tool_filter
        self.agent = None          # 빌드 후 최종 LlmAgent를 보관
        self._toolsets = []        # 나중에 정리를 위해 모든 로드된 도구세트 저장


    async def build(self):
        """
        LlmAgent를 빌드합니다:
        - 설정에 나열된 모든 MCP 서버에 연결
        - 각 서버에서 도구 로드
        - 해당 도구로 ADK agent 초기화

        `self.agent`를 사용하기 전에 호출되어야 합니다.
        """
        toolsets = await self._load_toolsets()

        # 로드된 도구세트로 ADK LLM Agent 구성
        # self.agent = LlmAgent(
        #     model="gemini-2.0-flash",  # agent를 구동할 모델 선택
        #     name="enterprise_assistant",
        #     instruction="Assist the user with filesystem and MCP server tasks.",
        #     tools=toolsets
        # )
        
       # LiteLlm 클래스를 사용하여 Ollama에서 제공하는 모델을 지정합니다.
        # 'ollama/' 접두사를 사용하고 모델 이름을 명시합니다.
        local_llama_model = LiteLlm(model="ollama/llama3.1:8b")
        
        self.agent = LlmAgent(
            model=local_llama_model,  # agent를 구동할 모델 선택
            name="mysql_assistant",
            instruction="당신은 사용자의 질문에 친절하게 답변하는 AI 비서입니다. MySQL 데이터베이스 관련 작업을 도와드립니다.",
            tools=toolsets
        )
        self._toolsets = toolsets  # 나중에 정리를 위해 도구세트 저장


    async def _load_toolsets(self):
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
                    conn = StreamableHTTPServerParams(url=server["url"])

                elif server.get("type") == "stdio":
                    conn = StdioConnectionParams(
                        command=server["command"],
                        args=server["args"],
                        timeout=5
                    )
                else:
                    raise ValueError(f"[red]❌ 설정에서 알 수 없는 서버 유형: '{server['type']}'[/red]")

                # 선택된 연결로 도구세트 생성 및 연결
                toolset = MCPToolset(
                    connection_params=conn,
                    tool_filter=self.tool_filter
                )

                # 도구 목록 가져오기 및 깔끔하게 출력
                tools = await toolset.get_tools()
                tool_names = [tool.name for tool in tools]
                print(f"[bold green]✅ 서버 [cyan]'{name}'[/cyan]에서 로드된 도구:[/bold green] {tool_names}")

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