#!/usr/bin/env python3
"""
Google Gemini Provider 테스트 스크립트 (Tool 사용 기능 포함)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_provider import ai_manager
from config import config

async def test_google_provider():
    """Google Gemini Provider를 테스트합니다."""
    print("=== Google Gemini Provider 테스트 ===")
    
    # 설정 확인
    print(f"AI Provider: {config.AI_PROVIDER}")
    print(f"Google API Key: {'설정됨' if config.GOOGLE_API_KEY else '설정되지 않음'}")
    print(f"Google Model: {config.GOOGLE_MODEL}")
    
    # Google Provider로 전환
    if ai_manager.switch_provider("google"):
        print("✅ Google Provider로 전환 성공")
    else:
        print("❌ Google Provider로 전환 실패")
        return
    
    # Provider 상태 확인
    current_provider = ai_manager.get_current_provider()
    print(f"현재 Provider: {current_provider}")
    
    # 간단한 테스트 프롬프트
    test_prompt = "안녕하세요. 간단한 인사말을 해주세요."
    
    print(f"\n테스트 프롬프트: {test_prompt}")
    
    try:
        # 응답 생성
        response = await ai_manager.generate_response(test_prompt)
        print(f"✅ 응답 생성 성공:")
        print(f"응답: {response}")
        
    except Exception as e:
        print(f"❌ 응답 생성 실패: {e}")
    
    # Tool 사용 테스트
    print(f"\n=== Tool 사용 테스트 ===")
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_table_list",
                    "description": "데이터베이스의 모든 테이블 목록을 반환합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_schema",
                    "description": "특정 테이블의 스키마 정보를 반환합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "테이블 이름"
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            }
        ]
        
        # Tool을 사용한 응답 생성 테스트
        response_with_tools = await ai_manager.generate_response_with_tools(
            [{"role": "user", "content": "사용 가능한 테이블을 보여줘"}], 
            tools
        )
        print(f"✅ Tool 사용 응답 생성 성공:")
        print(f"응답: {response_with_tools}")
        
        # Tool 호출이 감지되었는지 확인
        if isinstance(response_with_tools, dict) and "tool_calls" in response_with_tools:
            print("🎯 Tool 호출이 성공적으로 감지되었습니다!")
            for tool_call in response_with_tools["tool_calls"]:
                func_name = tool_call["function"]["name"]
                print(f"   - 호출된 함수: {func_name}")
        elif isinstance(response_with_tools, dict) and "content" in response_with_tools:
            print("📝 일반 응답이 생성되었습니다.")
            print(f"   - 응답 내용: {response_with_tools['content']}")
        
    except Exception as e:
        print(f"❌ Tool 사용 응답 생성 실패: {e}")
    
    # 복잡한 Tool 체인 테스트
    print(f"\n=== 복잡한 Tool 체인 테스트 ===")
    try:
        complex_prompt = "사용자 테이블의 구조를 파악하고 간단한 SELECT 쿼리를 생성해줘"
        
        response_complex = await ai_manager.generate_response(complex_prompt, tools)
        print(f"✅ 복잡한 Tool 체인 테스트 성공:")
        print(f"응답: {response_complex}")
        
        # Tool 호출이 감지되었는지 확인
        if "Tool 호출 감지:" in response_complex:
            print("🎯 Tool 체인이 성공적으로 작동했습니다!")
        else:
            print("📝 직접 응답이 생성되었습니다.")
        
    except Exception as e:
        print(f"❌ 복잡한 Tool 체인 테스트 실패: {e}")

def main():
    """메인 함수"""
    try:
        asyncio.run(test_google_provider())
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
