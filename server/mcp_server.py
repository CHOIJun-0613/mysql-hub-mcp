"""
MCP(Model Context Protocol) 서버 모듈
MCP 프로토콜을 구현하여 클라이언트와 통신합니다.
SSE(Server-Sent Events) 방식으로 HTTP 서버를 제공합니다.
"""

import logging
import os
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from database import db_manager
from config import config

logger = logging.getLogger(__name__)
host = config.MCP_SERVER_HOST
port = config.MCP_SERVER_PORT

mcp = FastMCP(
    "mysql-hub-mcp-server",
    "0.1.0",
    host=host,
    port=port,
    mount_path = "/",
    message_path= "/messages/",
    streamable_http_path= "/mcp",
    stateless_http=True
)

@mcp.tool(description="데이터베이스 정보를 조회한다.", title="데이터베이스 정보 조회")
async def get_database_info() -> Dict[str, Any]:
    """데이터베이스 정보를 반환합니다.
    
    Returns:
        Dict[str, Any]: 데이터베이스 정보 (연결 상태, 데이터베이스명, 테이블 수 등)
    """
    try:
        info = db_manager.get_database_info()
        logger.debug(f"데이터베이스 정보 조회 결과: {info}")
        return info
    except Exception as e:
        logger.error(f"데이터베이스 정보 조회 실패: {e}")
        return {"error": str(e), "status": "failed"}
    
@mcp.tool(description="테이블 목록을 조회한다.", title="테이블 목록록 조회")
async def get_table_list() -> List[str]:
    """테이블 목록을 반환합니다.
    
    Returns:
        List[str]: 테이블 목록
    """
    try:
        tables = db_manager.get_table_list()
        logger.debug(f"테이블 목록 조회 결과: {tables}")
        return tables
    except Exception as e:
        logger.error(f"테이블 목록 조회 실패: {e}")
        return []

@mcp.tool(description="테이블의 Schema 정보를 조회한다.", title="테이블 Schema 조회")
async def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """테이블 스키마를 반환합니다.
    
    Args:
        table_name: 스키마를 조회할 테이블 이름
        
    Returns:
        List[Dict[str, Any]]: 테이블 스키마 정보 (컬럼명, 타입, 제약조건 등)
    """
    try:
        if not table_name:
            raise ValueError("테이블 이름이 제공되지 않았습니다.")
        
        schema = db_manager.get_table_schema(table_name)
        logger.debug(f"테이블 스키마 조회 결과: {schema}")
        return schema
    except Exception as e:
        logger.error(f"테이블 스키마 조회 실패: {e}")
        return []

@mcp.tool(description="입력받은 SQL 쿼리를 실행합니다.", title="SQL 쿼리 실행")
async def execute_sql(sql: str) -> Dict[str, Any]:
    """SQL 쿼리를 실행합니다.
    
    Args:
        sql: 실행할 SQL 쿼리
        
    Returns:
        Dict[str, Any]: 쿼리 실행 결과 (데이터, 행 수, 실행 시간 등)
    """
    try:
        if not sql:
            raise ValueError("SQL 쿼리가 제공되지 않았습니다.")
        
        # 데이터베이스 매니저에서 SQL 실행 메서드 호출
        result = db_manager.execute_query(sql)
        logger.debug(f"SQL 실행 결과: {result}")
        return {"data": result, "row_count": len(result), "sql": sql, "status": "success"}
    except Exception as e:
        logger.error(f"SQL 실행 실패: {e}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def natural_language_query(query: str) -> Dict[str, Any]:
    """자연어로 데이터베이스 쿼리를 실행합니다.
    
    Args:
        query: 자연어로 된 쿼리 (예: "사용자 테이블에서 모든 데이터를 가져와줘")
        
    Returns:
        Dict[str, Any]: 쿼리 실행 결과
    """
    try:
        if not query:
            raise ValueError("자연어 쿼리가 제공되지 않았습니다.")
        
        # AI를 통한 자연어 쿼리 처리 (향후 구현)
        # result = ai_manager.process_natural_language_query(query)
        
        # 임시로 직접 SQL 실행 (실제로는 AI가 SQL을 생성해야 함)
        result = {"message": "자연어 쿼리 기능은 현재 개발 중입니다.", "query": query}
        logger.debug(f"자연어 쿼리 처리 결과: {result}")
        return result
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 실패: {e}")
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    
    logger.info("MySQL Hub MCP 서버를 시작합니다...")
    logger.info(f"MCP 서버 호스트: {config.MCP_SERVER_HOST}")
    logger.info(f"MCP 서버 포트: {config.MCP_SERVER_PORT}")
    
    mcp.run("streamable-http")