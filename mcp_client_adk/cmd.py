# ------------------------------------------------------------------------------
# 파일: cmd.py
# ------------------------------------------------------------------------------
# 목적:
# ADK 채팅 클라이언트의 진입점입니다. 사용자가 Google의 ADK를 사용하여
# MCP 도구 서버에 연결된 LLM agent와 상호작용할 수 있게 합니다.
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 임포트
# ------------------------------------------------------------------------------

import asyncio
import logging
import warnings

# Rich 라이브러리에서 컬러 터미널 출력을 위한 print 함수
from rich import print

from .client import MCPClient
from .ai_config import ai_config
# Google ADK의 실험적 기능 경고 숨기기
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*Field name.*shadows an attribute.*", category=UserWarning)
logging.getLogger("google_adk.google.adk.tools.base_authenticated_tool").setLevel(logging.ERROR)


# ------------------------------------------------------------------------------
# 설정 상수
# ------------------------------------------------------------------------------

# ADK 앱 식별자 (세션이나 도구를 등록할 때 사용)
APP_NAME = "mysql_assistant"

# 현재 세션을 위한 고유 사용자 ID
USER_ID = "mysql_assistant_001"

# 고유 세션 ID (여러 세션을 재개하거나 구분하는 데 도움이 됨)
SESSION_ID = "session_001"

# 클라이언트가 사용할 수 있는 도구 세트 정의
# 이들은 하나 이상의 도구 서버에서 올 수 있습니다
READ_ONLY_TOOLS = [
    'execute_sql',
    'natural_language_query',
    'get_database_info',
    'get_table_list',
    'get_table_schema'
]

# ------------------------------------------------------------------------------
# 로깅 설정
# ------------------------------------------------------------------------------

# ERROR 메시지만 표시하도록 로깅 구성 (INFO, DEBUG 등 억제)
logging.basicConfig(level=logging.ERROR)

# ------------------------------------------------------------------------------
# 메인 채팅 루프 함수
# ------------------------------------------------------------------------------

async def chat_loop():
    """
    지속적으로 다음을 수행하는 메인 채팅 루프:
    - 사용자 입력 프롬프트
    - ADK MCP agent에 입력 전송
    - agent 응답 스트리밍 및 표시
    """

    print("\n💬 ADK LLM Agent 채팅이 시작되었습니다. 종료하려면 'quit' 또는 ':q'를 입력하세요.\n")

    # AI Provider 정보 표시
    try:
        provider_info = ai_config.get_provider_info()
        print(f"🤖 AI Provider: {provider_info['provider']}")
        print(f"📱 모델: {provider_info['model']}")
        print(f"✅ 상태: {'사용 가능' if provider_info['available'] else '사용 불가능'}")
    except ImportError:
        print("⚠️ AI Provider 정보를 불러올 수 없습니다.")

    import uuid
    global SESSION_ID
    SESSION_ID = str(uuid.uuid4())
    print(f"🔍 세션 ID: {SESSION_ID}")

    # 앱/사용자/세션 설정으로 ADK MCP 클라이언트 초기화
    client = MCPClient(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        tool_filter=READ_ONLY_TOOLS
    )

    # 도구세트와 세션 설정 (MCP 도구 서버와 협상)
    try:
        await client.init_session()
    except Exception as e:
        print(f"[bold red]⚠️ MCP 서버 연결 실패: {e}[/bold red]")
        print("[bold yellow]MCP 서버가 실행 중인지 확인해주세요.[/bold yellow]")
        print("[bold blue]새 터미널에서 'cd server && python run_server.py'를 실행하세요.[/bold blue]")
        return

    try:
        # 사용자 입력을 받고 agent 응답을 처리하는 연속 루프
        while True:
            user_input = input("\n[You]: ")

            # 종료 명령을 우아하게 처리
            if user_input.strip().lower() in ["quit", ":q", "exit"]:
                print("👋 세션을 종료합니다. 안녕히 가세요!")
                break
            if user_input.strip().__len__() <= 5:
                print("👋 입력이 너무 짧습니다. 5자 이상 입력해주세요.")
                continue
            
            i = 0
            # 입력 작업을 agent에 보내고 응답 스트리밍
            async for event in await client.send_task(user_input):
                i += 1
                                
                # function call 이벤트 감지 및 출력
                function_calls = event.get_function_calls()
                if function_calls:
                    # func_name 외에 function argument도 출력하는 부분 추가
                    for func_call in function_calls:
                        func_name = getattr(func_call, "name", "알수없음")
                        
                        # args 속성은 dict 또는 None일 수 있음
                        func_args = getattr(func_call, "args", None)
                        
                        if func_args:
                            # dict라면 key=value 형태로 출력
                            if isinstance(func_args, dict):
                                args_str = ", ".join(f"{k}={v!r}" for k, v in func_args.items())
                            else:
                                args_str = str(func_args)
                            print(f"📦 이벤트 #{i} : [bold yellow]{func_name} - call[/bold yellow] (args: {args_str})")
                        else:
                            print(f"📦 이벤트 #{i} : [bold yellow]{func_name} - call[/bold yellow] (args: 없음)")
                # function response 이벤트 감지 및 출력
                function_responses = event.get_function_responses()
                if function_responses:
                    # response에서도 argument 출력하는 로직으로 수정
                    if function_responses:
                        for func_response in function_responses:
                            func_name = getattr(func_response, "name", "알수없음")
                            func_args = getattr(func_response, "args", None)
                            if func_args:
                                if isinstance(func_args, dict):
                                    args_str = ", ".join(f"{k}={v!r}" for k, v in func_args.items())
                                else:
                                    args_str = str(func_args)
                                print(f"📦 이벤트 #{i} : [bold green]{func_name} - response[/bold green] (args: {args_str})")
                            else:
                                print(f"📦 이벤트 #{i} : [bold green]{func_name} - response[/bold green] (args: 없음)")
                # 최종 응답을 받으면 출력하고 루프 중단
                if hasattr(event, "is_final_response") and event.is_final_response():
                    print(f"\n🧠 Agent 응답:\n------------------------\n{event.content.parts[0].text}\n")
                    break
    finally:
        # 세션이 종료되고 리소스가 해제되도록 보장
        try:
            await client.shutdown()
        except Exception as e:
            print(f"[yellow]⚠️ 클라이언트 종료 중 오류: {e}[/yellow]")
            # 강제 종료를 위한 짧은 대기
            await asyncio.sleep(0.1)

# ------------------------------------------------------------------------------
# 진입점
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        # asyncio 이벤트 루프를 사용하여 비동기 채팅 루프 시작
        asyncio.run(chat_loop())

    except asyncio.CancelledError:
        # 이 경고는 ADK/MCP의 백그라운드 작업 종료 메커니즘으로 인해
        # 나타날 수 있습니다 (데모/교육용 코드에서는 무시해도 안전)
        print("\n⚠️ 종료 중 CancelledError 억제됨 "
        "(데모/교육용 코드에서는 무시해도 안전).")
    except RuntimeError as e:
        if "cancel scope" in str(e).lower():
            print("\n⚠️ MCP 클라이언트 종료 중 cancel scope 오류 발생")
            print("이는 정상적인 종료 과정에서 발생할 수 있습니다.")
        else:
            raise
    except Exception as e:
        print(f"\n[bold red]❌ 예상치 못한 오류 발생: {e}[/bold red]")
        print("[bold yellow]MCP 서버 상태를 확인해주세요.[/bold yellow]")