"""
HTTP 서버 모듈
FastAPI를 사용하여 HTTP API를 제공합니다.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import config
from database import db_manager
from ai_provider import ai_manager
from ai_worker import strip_markdown_sql, natural_language_query_work
from common import SQLQueryRequest, NaturalLanguageRequest, TableSchemaRequest, AIProviderRequest, Response


logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="MySQL Hub MCP Server",
    description="MySQL 데이터베이스와 자연어 쿼리를 지원하는 MCP 서버",
    version="0.1.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger.info("HTTP 서버가 시작되었습니다.")
    
    # 로깅 설정
    config.setup_logging()
    
    # 데이터베이스 연결 확인
    if not db_manager.is_connected():
        logger.error("데이터베이스에 연결할 수 없습니다.")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "MySQL Hub MCP Server",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    db_status = db_manager.is_connected()
    ai_status = ai_manager.get_current_provider()
    
    return {
        "status": "healthy",
        "database": "connected" if db_status else "disconnected",
        "ai_provider": ai_status
    }

@app.get("/database/info")
async def get_database_info():
    """데이터베이스 정보를 반환합니다."""
    try:
        info = db_manager.get_database_info()
        logger.debug(f"데이터베이스 정보 조회 결과: {info}")
        return Response(success=True, data=info)
    except Exception as e:
        logger.error(f"데이터베이스 정보 조회 실패: {e}")
        return Response(success=False, error=str(e))

@app.post("/database/execute")
async def execute_sql(request: SQLQueryRequest):
    """SQL 쿼리를 실행합니다."""
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="SQL 쿼리가 제공되지 않았습니다.")
        
        # 마크다운 형식 제거
        clean_query = strip_markdown_sql(request.query)
        logger.info(f"원본 SQL: {request.query}")
        logger.info(f"정리된 SQL: {clean_query}")
        
        # SQL 키워드가 포함되어 있는지 확인
        sql_keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
        if not any(keyword.lower() in clean_query.lower() for keyword in sql_keywords):
            raise HTTPException(status_code=400, detail="유효한 SQL 쿼리가 아닙니다.")
        
        # 쿼리 유효성 검사
        if not db_manager.validate_query(clean_query):
            # 더 자세한 오류 메시지 제공
            error_detail = "잘못된 SQL 쿼리입니다."
            
            # 예약어 관련 오류인지 확인
            query_lower = request.query.lower()
            reserved_words = ['order', 'group', 'select', 'from', 'where', 'having', 'limit', 'offset']
            
            for word in reserved_words:
                if f" {word} " in query_lower or query_lower.startswith(word + " ") or query_lower.endswith(" " + word):
                    if word in ['order', 'group']:
                        error_detail = f"'{word}'는 MySQL 예약어입니다. 백틱(`)으로 감싸주세요. 예: `{word}`"
                    break
            
            raise HTTPException(status_code=400, detail=error_detail)
        
        # 쿼리 실행
        if clean_query.strip().upper().startswith('SELECT'):
            result = db_manager.execute_query(clean_query)
        else:
            affected_rows = db_manager.execute_non_query(clean_query)
            result = {"affected_rows": affected_rows}
        
        logger.debug(f"SQL 실행 결과: {result}")
        return Response(success=True, data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL 실행 실패: {e}")
        return Response(success=False, error=str(e))

@app.post("/database/natural-query")
async def natural_language_query(request: NaturalLanguageRequest):
    """자연어를 SQL로 변환하여 실행합니다."""
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="질문이 제공되지 않았습니다.")
        # 질문이 수자로만 되어 있거나 글자수가 5 미만인 경우 예외 처리
        if request.question.isdigit() or len(request.question.strip()) < 5:
            raise HTTPException(status_code=400, detail="질문 내용이 너무 짧거나 수자로만 되어 있어서 모호합니다.")
        
        return await natural_language_query_work(request.question, config.USE_LLM_TOOLS)
            
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 중 오류: {e}")
        return Response(
            success=False,
            error=f"자연어 쿼리 처리 중 오류가 발생했습니다: {e}"
        )

@app.get("/database/tables")
async def get_table_list():
    """테이블 목록을 반환합니다."""
    try:
        tables = db_manager.get_table_list()
        logger.debug(f"테이블 목록 조회 결과: {tables}")
        return Response(success=True, data=tables)
    except Exception as e:
        logger.error(f"테이블 목록 조회 실패: {e}")
        return Response(success=False, error=str(e))

@app.post("/database/table-schema")
async def get_table_schema(request: TableSchemaRequest):
    """테이블 스키마를 반환합니다."""
    try:
        if not request.table_name:
            raise HTTPException(status_code=400, detail="테이블 이름이 제공되지 않았습니다.")
        
        schema = db_manager.get_table_schema(request.table_name)
        logger.debug(f"테이블 스키마 조회 결과: {schema}")
        return Response(success=True, data=schema)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 스키마 조회 실패: {e}")
        return Response(success=False, error=str(e))

@app.get("/ai/provider")
async def get_current_ai_provider():
    """현재 AI Provider 정보를 반환합니다."""
    try:
        provider = ai_manager.get_current_provider()
        provider_data = {"provider": provider}
        logger.debug(f"AI Provider 정보 조회 결과: {provider_data}")
        return Response(success=True, data=provider_data)
    except Exception as e:
        logger.error(f"AI Provider 정보 조회 실패: {e}")
        return Response(success=False, error=str(e))

@app.post("/ai/switch-provider")
async def switch_ai_provider(request: AIProviderRequest):
    """AI Provider를 전환합니다."""
    try:
        success = ai_manager.switch_provider(request.provider)
        if success:
            provider_data = {"provider": ai_manager.get_current_provider()}
            logger.debug(f"AI Provider 전환 성공 결과: {provider_data}")
            return Response(
                success=True,
                data=provider_data
            )
        else:
            logger.debug(f"AI Provider 전환 실패: {request.provider}")
            return Response(
                success=False,
                error=f"Provider 전환 실패: {request.provider}"
            )
    except Exception as e:
        logger.error(f"AI Provider 전환 실패: {e}")
        return Response(success=False, error=str(e))
    
def run_http_server():
    """HTTP 서버를 실행합니다."""
    uvicorn.run(
        app,
        host=config.HTTP_SERVER_HOST,
        port=config.HTTP_SERVER_PORT,
        log_level="DEBUG"
        
    )

if __name__ == "__main__":
    run_http_server() 