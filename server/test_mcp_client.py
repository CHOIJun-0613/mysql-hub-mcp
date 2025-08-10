#!/usr/bin/env python3
"""
MCP 서버 테스트용 클라이언트
"""

import asyncio
import aiohttp
import json

async def test_mcp_server():
    """MCP 서버를 테스트합니다."""
    
    # MCP 서버 URL
    base_url = "http://127.0.0.1:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 서버 상태 확인
            print("1. 서버 상태 확인...")
            async with session.get(f"{base_url}/") as response:
                print(f"   상태 코드: {response.status}")
                if response.status == 200:
                    print("   ✅ 서버가 정상적으로 실행 중입니다")
                else:
                    print(f"   ❌ 서버 오류: {response.status}")
            
            # 2. MCP 세션 생성 (SSE)
            print("\n2. MCP 세션 생성 (SSE)...")
            headers = {
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
            
            # 세션 생성 요청
            session_data = {
                "jsonrpc": "2.0",
                "id": "session-init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with session.post(
                f"{base_url}/messages/",
                json=session_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                print(f"   세션 생성 상태 코드: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ 세션 생성 성공: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    text = await response.text()
                    print(f"   ❌ 세션 생성 실패: {text}")
                    return
            
            # 3. 도구 목록 조회
            print("\n3. 도구 목록 조회...")
            tools_request = {
                "jsonrpc": "2.0",
                "id": "tools-list",
                "method": "tools/list",
                "params": {}
            }
            
            async with session.post(
                f"{base_url}/messages/",
                json=tools_request,
                headers={'Content-Type': 'application/json'}
            ) as response:
                print(f"   도구 목록 조회 상태 코드: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ 도구 목록: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    text = await response.text()
                    print(f"   ❌ 도구 목록 조회 실패: {text}")
            
            # 4. 데이터베이스 정보 조회
            print("\n4. 데이터베이스 정보 조회...")
            db_info_request = {
                "jsonrpc": "2.0",
                "id": "db-info",
                "method": "tools/call",
                "params": {
                    "name": "get_database_info",
                    "arguments": {}
                }
            }
            
            async with session.post(
                f"{base_url}/messages/",
                json=db_info_request,
                headers={'Content-Type': 'application/json'}
            ) as response:
                print(f"   데이터베이스 정보 조회 상태 코드: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ 데이터베이스 정보: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    text = await response.text()
                    print(f"   ❌ 데이터베이스 정보 조회 실패: {text}")
                    
        except aiohttp.ClientConnectorError:
            print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("MCP 서버 테스트를 시작합니다...")
    print("=" * 50)
    asyncio.run(test_mcp_server())
