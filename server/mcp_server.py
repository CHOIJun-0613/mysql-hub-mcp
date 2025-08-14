"""
MCP(Model Context Protocol) 서버 모듈
MCP 프로토콜을 구현하여 클라이언트와 통신합니다.
SSE(Server-Sent Events) 방식으로 HTTP 서버를 제공합니다.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from database import db_manager
from ai_provider import ai_manager
from ai_worker import natural_language_query_work,make_system_prompt, strip_markdown_sql
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
    stateless_http=True,
    log_level="INFO"
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

@mcp.tool(description="사용자의 자연어 쿼리를 실행합니다.", title="자연어 쿼리 실행")
async def natural_language_query(question: str) -> Dict[str, Any]:
    """자연어로 데이터베이스 쿼리를 실행합니다.
    
    Args:
        question: 자연어로 된 쿼리 (예: "사용자 테이블에서 모든 데이터를 가져와줘")
        
    Returns:
        Dict[str, Any]: 쿼리 실행 결과
    """
    try:
        if not question:
            raise ValueError("사용자의 질의 내용이 제공되지 않았습니다.")
        
        if question.isdigit() or len(question.strip()) < 5:
            raise ValueError("질문 내용이 너무 짧거나 수자로만 되어 있어서 모호합니다.")

        response = await natural_language_query_work(question, False)
        
        result = {"data": response.data, "row_count": len(response.data), "sql": response.data.get("sql_query", ""), "status": "success"}
        logger.debug(f"자연어 쿼리 처리 결과: {result}")
        return  result
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 실패: {e}")
        return {"error": str(e), "status": "failed"}

async def _natural_language_query(question: str):
    """기존 방식으로 자연어를 SQL로 변환합니다 (system prompt에 스키마 정보 포함)."""
    try:
        # 데이터베이스 스키마 정보 가져오기
        db_info = db_manager.get_database_info()
        if "error" in db_info:
            logger.error(f"데이터베이스 연결 오류: {db_info['error']}")
            raise ValueError(f"데이터베이스 연결 오류: {db_info['error']}")
        
        # 현재 tools 지원 모델이 없으므로 기존 방식으로 스키마 정보 수집
        schema_info = ""
        # devdb 데이터베이스의 실제 테이블들만 사용     
        user_tables = [table for table in db_info.get("tables", []) 
                      if not table.startswith('INFORMATION_SCHEMA') and 
                         not table.startswith('mysql') and 
                         not table.startswith('performance_schema') and
                         not table.startswith('sys')]
        
        # 모든 사용자 테이블의 스키마 정보를 사용               
        for table_name in user_tables:
            try:
                schema = db_manager.get_table_schema(table_name)
                schema_info += f"\n\n### {table_name} 테이블 스키마\n"
                schema_info += f"```sql\n{schema}\n```\n"
            except Exception as e:      
                logger.error(f"테이블 스키마 조회 실패: {e}")
                continue
        
        # 스키마 정보를 시스템 프롬프트에 포함
        system_prompt = make_system_prompt(
            database_name=db_info.get("database_name", "devdb"),
            schema_info=schema_info,
            question=question,
            use_tools=False
        )
        
        # AI 응답 생성                                  
        response = await ai_manager.generate_response(system_prompt)
        logger.debug(f"AI 생성 결과 SQL: {response}")
        
        sql_query = response
        
        # SQL 키워드가 포함되어 있는지 확인
        sql_keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
        if not any(keyword in sql_query.upper() for keyword in sql_keywords):
            logger.error(f"AI가 SQL 쿼리를 생성하지 못했습니다. 응답: {sql_query}")
            return {"error": f"AI가 SQL 쿼리를 생성하지 못했습니다. 응답: {sql_query}", "status": "failed"}    

        # 마크다운 형식 제거
        clean_sql = strip_markdown_sql(sql_query)
        logger.info(f"원본 SQL: {sql_query}")
        logger.info(f"정리된 SQL: {clean_sql}")
        
        # SQL 쿼리 실행
        try:
            result = db_manager.execute_query(clean_sql)
            return {"data": result, "row_count": len(result), "sql": clean_sql, "status": "success"}
        except Exception as e:
            logger.error(f"SQL 실행 오류: {e}")
            return {"error": f"SQL 실행 오류: {e}", "status": "failed"}  

    except Exception as e:
        logger.error(f"자연어 쿼리 처리 실패: {e}")
        return {"error": str(e), "status": "failed"}    
    
def run_mcp_server():
    """MCP 서버를 실행합니다."""
    logger.info("MySQL Hub MCP 서버를 시작합니다...")
    logger.info(f"MCP 서버 호스트: {config.MCP_SERVER_HOST}")
    logger.info(f"MCP 서버 포트: {config.MCP_SERVER_PORT}")
    
    mcp.run("streamable-http")


if __name__ == "__main__":
    run_mcp_server()
