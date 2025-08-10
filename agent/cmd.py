# ------------------------------------------------------------------------------
# 파일: cmd.py
# ------------------------------------------------------------------------------
# 목적:
# ADK 채팅 클라이언트의 진입점입니다. 사용자가 Google의 ADK를 사용하여
# MCP 도구 서버에 연결된 LLM agent와 상호작용할 수 있게 합니다.
# ------------------------------------------------------------------------------

import asyncio
import logging
from .client import MCPClient
from .utilities import print_json_response

# ------------------------------------------------------------------------------
# 설정 상수
# ------------------------------------------------------------------------------

# ADK 앱 식별자 (세션이나 도구를 등록할 때 사용)
APP_NAME = "google_adk_gemini_mcp_client"

# 현재 세션을 위한 고유 사용자 ID
USER_ID = "theailanguage_001"

# 고유 세션 ID (여러 세션을 재개하거나 구분하는 데 도움이 됨)
SESSION_ID = "session_001"

# 클라이언트가 사용할 수 있는 도구 세트 정의
# 이들은 하나 이상의 도구 서버에서 올 수 있습니다
READ_ONLY_TOOLS = [
    'add_numbers',
    'subtract_numbers',
    'multiply_numbers',
    'divide_numbers',
    'run_command'
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

    # 앱/사용자/세션 설정으로 ADK MCP 클라이언트 초기화
    client = MCPClient(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        tool_filter=READ_ONLY_TOOLS
    )

    # 도구세트와 세션 설정 (MCP 도구 서버와 협상)
    await client.init_session()

    try:
        # 사용자 입력을 받고 agent 응답을 처리하는 연속 루프
        while True:
            user_input = input("You: ")

            # 종료 명령을 우아하게 처리
            if user_input.strip().lower() in ["quit", ":q", "exit"]:
                print("👋 세션을 종료합니다. 안녕히 가세요!")
                break

            i = 0
            # 입력 작업을 agent에 보내고 응답 스트리밍
            async for event in await client.send_task(user_input):
                i += 1
                print_json_response(event, f"📦 이벤트 #{i}")

                # 최종 응답을 받으면 출력하고 루프 중단
                if hasattr(event, "is_final_response") and event.is_final_response():
                    print(f"\n🧠 Agent 응답:\n------------------------\n{event.content.parts[0].text}\n")
                    break
    finally:
        # 세션이 종료되고 리소스가 해제되도록 보장
        await client.shutdown()

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