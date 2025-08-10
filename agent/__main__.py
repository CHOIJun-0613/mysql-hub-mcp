#!/usr/bin/env python3
"""
MySQL Hub MCP Agent 실행 파일
"""

import asyncio
from .agent import AgentWrapper

async def main():
    """메인 함수"""
    try:
        print("🚀 MySQL Hub MCP Agent를 시작합니다...")
        
        # AgentWrapper 인스턴스 생성
        print("📦 AgentWrapper 인스턴스를 생성합니다...")
        agent_wrapper = AgentWrapper()
        
        # Agent 빌드
        print("🔨 Agent를 빌드합니다...")
        await agent_wrapper.build()
        
        print("✅ Agent가 성공적으로 빌드되었습니다!")
        print(f"Agent 이름: {agent_wrapper.agent.name}")
        print(f"사용 가능한 도구 수: {len(agent_wrapper._toolsets)}")
        
        # 여기에 대화형 루프나 다른 로직을 추가할 수 있습니다
        
    except Exception as e:
        print(f"❌ Agent 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 정리
        if 'agent_wrapper' in locals():
            await agent_wrapper.close()

if __name__ == "__main__":
    asyncio.run(main())
