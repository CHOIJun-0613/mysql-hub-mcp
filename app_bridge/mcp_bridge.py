#!/usr/bin/env python3
"""
MySQL Hub MCP Bridge Server - HTTP 서버와 Cursor 사이의 중계 서버
"""

import sys
import json
import httpx
import asyncio
import argparse
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP

# Set encoding for proper character handling
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 로깅 설정
def setup_logging():
    """로깅을 설정합니다."""
    # 로그 디렉토리 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로그 파일명 (날짜 포함)
    today = datetime.now().strftime("%Y%m%d")
    log_filename = f"logs/mcp-bridge-{today}.log"
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename, encoding='utf-8')
        ]
    )
    
    # 외부 라이브러리의 로그 레벨 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger("mcp-bridge")

# 로거 초기화
logger = setup_logging()

# 명령행 인수 파싱
parser = argparse.ArgumentParser(description='MySQL Hub MCP Bridge Server')
parser.add_argument('--url', '-u', 
                   default='http://localhost:8000',
                   help='HTTP 서버 URL (기본값: http://localhost:8000)')
args = parser.parse_args()

# HTTP 서버 URL 설정
HTTP_SERVER_URL = args.url

logger.info(f"MySQL Hub MCP Bridge Server 시작 - HTTP 서버 URL: {HTTP_SERVER_URL}")

# Initialize FastMCP server
mcp = FastMCP("mysql-hub-mcp-bridge")

async def call_http_server(endpoint: str, data: Dict[str, Any] = None) -> str:
    """HTTP 서버에 요청을 보내고 응답을 받습니다."""
    logger.debug(f"HTTP 서버 호출 시작: {endpoint}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{HTTP_SERVER_URL}{endpoint}"
            logger.debug(f"HTTP 요청 전송: {url}")
            
            if data:
                response = await client.post(url, json=data)
            else:
                response = await client.get(url)
            
            logger.debug(f"HTTP 응답 상태: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"HTTP 응답 결과: {str(result)[:100]}...")
            
            if result.get("success"):
                return str(result.get("data", "성공"))
            else:
                error_msg = f"오류: {result.get('error', '알 수 없는 오류')}"
                logger.error(error_msg)
                return error_msg
                        
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP 상태 오류: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        return error_msg
    except httpx.RequestError as e:
        error_msg = f"HTTP 요청 오류: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"HTTP 서버 호출 오류: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
async def execute_sql(sql: str) -> str:
    """MySQL 데이터베이스에서 SQL 쿼리를 실행합니다.

    Args:
        sql: 실행할 SQL 쿼리
    """
    logger.info(f"execute_sql 호출됨: {sql[:50]}...")
    result = await call_http_server("/database/execute", {"query": sql})
    logger.debug(f"execute_sql 결과: {result[:100]}...")
    return result

@mcp.tool()
async def natural_language_query(question: str) -> str:
    """자연어를 SQL 쿼리로 변환하여 실행합니다.

    Args:
        question: 자연어로 된 질문
    """
    logger.info(f"natural_language_query 호출됨: {question}")
    result = await call_http_server("/database/natural-query", {"question": question})
    logger.debug(f"natural_language_query 결과: {result[:100]}...")
    return result

@mcp.tool()
async def get_database_info() -> str:
    """데이터베이스 정보와 테이블 목록을 반환합니다."""
    logger.info("get_database_info 호출됨")
    result = await call_http_server("/database/info")
    logger.debug(f"get_database_info 결과: {result[:100]}...")
    return result

@mcp.tool()
async def get_table_schema(table_name: str) -> str:
    """특정 테이블의 스키마 정보를 반환합니다.

    Args:
        table_name: 테이블 이름
    """
    logger.info(f"get_table_schema 호출됨: {table_name}")
    result = await call_http_server("/database/table-schema", {"table_name": table_name})
    logger.debug(f"get_table_schema 결과: {result[:100]}...")
    return result

@mcp.tool()
async def get_table_list() -> str:
    """데이터베이스의 모든 테이블 목록을 반환합니다."""
    logger.info("get_table_list 호출됨")
    result = await call_http_server("/database/tables")
    logger.debug(f"get_table_list 결과: {result[:100]}...")
    return result

@mcp.tool()
async def get_current_ai_provider() -> str:
    """현재 AI Provider 정보를 반환합니다."""
    logger.info("get_current_ai_provider 호출됨")
    result = await call_http_server("/ai/provider")
    logger.debug(f"get_current_ai_provider 결과: {result[:100]}...")
    return result

@mcp.tool()
async def switch_ai_provider(provider: str) -> str:
    """AI Provider를 전환합니다.

    Args:
        provider: 전환할 AI Provider (groq 또는 ollama)
    """
    logger.info(f"switch_ai_provider 호출됨: {provider}")
    result = await call_http_server("/ai/switch-provider", {"provider": provider})
    logger.debug(f"switch_ai_provider 결과: {result[:100]}...")
    return result

if __name__ == "__main__":
    logger.info("MySQL Hub MCP 브리지 서버 시작 중...")
    logger.info(f"HTTP 서버 URL: {HTTP_SERVER_URL}")
    logger.info("사용 가능한 도구:")
    logger.info("  - execute_sql: SQL 쿼리 실행")
    logger.info("  - natural_language_query: 자연어 쿼리")
    logger.info("  - get_database_info: 데이터베이스 정보")
    logger.info("  - get_table_schema: 테이블 스키마")
    logger.info("  - get_table_list: 테이블 목록")
    logger.info("  - get_current_ai_provider: AI Provider 정보")
    logger.info("  - switch_ai_provider: AI Provider 전환")
    logger.info("사용법: python mcp_bridge.py --url <HTTP_SERVER_URL>")
    mcp.run(transport='stdio') 