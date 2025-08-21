# ------------------------------------------------------------------------------
# 파일: client.py
# ------------------------------------------------------------------------------
# 목적:
# MCPClient를 정의합니다. 이는 UI 또는 채팅 인터페이스를 Google ADK agent에
# 연결하는 래퍼입니다. 세션 상태를 관리하고 사용자 입력을 agent를 통해
# 연결된 MCP 도구세트로 라우팅합니다.
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 임포트
# ------------------------------------------------------------------------------

# Google ADK 콘텐츠/메시지 유형
import logging
import warnings
from google.genai.types import Content, Part

# Runner는 ADK의 인프라를 사용하여 agent로 작업을 실행합니다
from google.adk.runners import Runner

# 메모리 내 세션 서비스는 세션 데이터를 로컬에 저장합니다
from google.adk.sessions import InMemorySessionService
# Google ADK의 실험적 기능 경고 숨기기
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*Field name.*shadows an attribute.*", category=UserWarning)

# ADK agent와 도구를 빌드하고 관리하기 위한 커스텀 래퍼
try:
    from adk_client.agent import AgentWrapper
except ImportError:
    # 상대 import 시도
    try:
        from .agent import AgentWrapper
    except ImportError:
        # 절대 경로 import 시도
        from agent import AgentWrapper

logging.getLogger("google_adk.google.adk.tools.base_authenticated_tool").setLevel(logging.ERROR)
# ------------------------------------------------------------------------------
# 클래스: MCPClient
# ------------------------------------------------------------------------------

class MCPClient:
    """
    채팅 앱이나 UI를 ADK agent에 연결하는 메인 클라이언트 인터페이스입니다.
    다음을 처리합니다:
    - 세션 생성
    - Agent 로딩
    - 사용자 메시지를 agent를 통해 도구세트로 라우팅
    """

    def __init__(self, app_name, user_id, session_id, tool_filter=None):
        """
        MCPClient를 초기화하는 생성자입니다.

        Args:
            app_name (str): 세션 메타데이터에 사용되는 고유 애플리케이션 이름.
            user_id (str): 세션 컨텍스트를 위한 사용자 식별자.
            session_id (str): 여러 채팅 세션을 구분하기 위한 세션 ID.
            tool_filter (list[str] or None): 허용된 도구의 선택적 목록.
        """

        # 앱 메타데이터 (세션 태깅, 로깅 등에 유용)
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id

        # 메모리 내 세션 서비스 사용 (메모리에 저장, 지속적이지 않음)
        self.session_service = InMemorySessionService()



        # 선택적 도구 필터링으로 agent 래퍼 준비
        # 도구 필터링은 이 클라이언트가 사용할 수 있는 도구를 제한합니다
        self.agent_wrapper = AgentWrapper(tool_filter=tool_filter)

        # Runner (작업을 보내고 결과를 받는 메인 엔진)는 나중에 생성됩니다
        self.runner = None


    async def init_session(self):
        """
        클라이언트를 초기화합니다:
        - 세션 생성 (로컬에서, 메모리에)
        - ADK agent와 도구 빌드
        - 사용자 입력을 실행하기 위한 ADK runner 인스턴스화
        """

        # 1단계: 세션 생성 (ADK는 세션 컨텍스트를 요구합니다)
        await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id
        )

        # 2단계: agent 빌드 (도구, 설정 등 로드)
        await self.agent_wrapper.build()

        # 3단계: 빌드된 agent와 세션 서비스를 사용하여 runner 생성
        self.runner = Runner(
            agent=self.agent_wrapper.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )


    async def send_task(self, user_input):
        """
        사용자 메시지를 ADK agent에 보내고 응답을 스트리밍합니다.

        Args:
            user_input (str): 사용자로부터의 원시 입력 (자연어).

        Returns:
            agent로부터 스트리밍 응답 이벤트를 생성하는 비동기 생성기.
        """

        # 사용자 입력을 role="user"인 Content 객체로 래핑
        new_message = Content(role="user", parts=[Part(text=user_input)])
        
        # agent runner를 통해 메시지를 비동기적으로 실행
        return self.runner.run_async(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=new_message
        )


    async def shutdown(self):
        """
        agent와 도구를 우아하게 종료합니다.
        비동기 작업을 정리하기 위해 세션 끝에 호출되어야 합니다.
        """

        await self.agent_wrapper.close()