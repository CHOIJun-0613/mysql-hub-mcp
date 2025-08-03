"""
HTTP 서버 모듈
FastAPI를 사용하여 HTTP API를 제공합니다.
"""

import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import config
from database import db_manager
from ai_provider import ai_manager

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

# Pydantic 모델들
class SQLQueryRequest(BaseModel):
    query: str

class NaturalLanguageRequest(BaseModel):
    question: str

class TableSchemaRequest(BaseModel):
    table_name: str

class AIProviderRequest(BaseModel):
    provider: str

class Response(BaseModel):
    success: bool
    data: Any = None
    error: str = None
    
    def model_dump(self, **kwargs):
        """UTF-8 인코딩 문제를 해결하기 위한 커스텀 model_dump"""
        try:
            return super().model_dump(**kwargs)
        except UnicodeDecodeError as e:
            # UTF-8 인코딩 오류 발생 시 데이터 정리
            logger.warning(f"UTF-8 인코딩 오류 발생, 데이터 정리 중: {e}")
            
            # 데이터 정리
            cleaned_data = self._clean_data(self.data)
            cleaned_error = self._clean_string(self.error) if self.error else None
            
            return {
                "success": self.success,
                "data": cleaned_data,
                "error": cleaned_error
            }
    
    def _clean_data(self, data):
        """데이터에서 UTF-8 문제가 있는 부분을 정리"""
        if isinstance(data, str):
            return self._clean_string(data)
        elif isinstance(data, dict):
            return {k: self._clean_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data(item) for item in data]
        else:
            return data
    
    def _clean_string(self, text):
        """문자열에서 UTF-8 문제가 있는 부분을 정리"""
        if not isinstance(text, str):
            return str(text)
        
        try:
            # UTF-8로 인코딩/디코딩하여 문제 있는 문자 제거
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            # 최후의 수단: ASCII로 변환
            return text.encode('ascii', errors='ignore').decode('ascii')

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
        
        # 쿼리 유효성 검사
        if not db_manager.validate_query(request.query):
            raise HTTPException(status_code=400, detail="잘못된 SQL 쿼리입니다.")
        
        # 쿼리 실행
        if request.query.strip().upper().startswith('SELECT'):
            result = db_manager.execute_query(request.query)
        else:
            affected_rows = db_manager.execute_non_query(request.query)
            result = {"affected_rows": affected_rows}
        
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
        
        # 데이터베이스 스키마 정보 가져오기
        db_info = db_manager.get_database_info()
        if "error" in db_info:
            raise HTTPException(status_code=500, detail=f"데이터베이스 연결 오류: {db_info['error']}")
        
        # AI에게 전달할 프롬프트 구성
        schema_info = ""
        # devdb 데이터베이스의 실제 테이블들만 사용
        user_tables = [table for table in db_info.get("tables", []) 
                      if not table.startswith('INFORMATION_SCHEMA') and 
                         not table.startswith('mysql') and 
                         not table.startswith('performance_schema') and
                         not table.startswith('sys')]
        
        for table_name in user_tables[:5]:  # 최대 5개 테이블만 사용
            try:
                schema = db_manager.get_table_schema(table_name)
                schema_info += f"\n테이블: {table_name}\n"
                for col in schema:
                    col_type = col['DATA_TYPE']
                    col_name = col['COLUMN_NAME']
                    # 바이너리 타입인 경우 표시
                    if 'binary' in col_type.lower() or 'blob' in col_type.lower():
                        schema_info += f"  - {col_name} ({col_type}) [바이너리 데이터]\n"
                    else:
                        schema_info += f"  - {col_name} ({col_type})\n"
            except Exception as e:
                logger.warning(f"테이블 {table_name} 스키마 조회 실패: {e}")
                continue
        
        prompt = f"""
다음 데이터베이스 스키마를 분석하고 자연어 질문을 SQL 쿼리로 변환해주세요.

데이터베이스: {db_info.get('database_name', 'unknown')}

=== 테이블 스키마 정보 ===
{schema_info}

=== 분석 단계 ===
1. 먼저 각 테이블의 구조와 컬럼을 분석하세요
2. 테이블 간의 관계를 파악하세요 (외래키, JOIN 가능한 컬럼)
3. 질문에서 필요한 정보가 어떤 테이블에 있는지 확인하세요
4. 질문에서 언급된 조건(상품명, 날짜, 금액 등)을 WHERE 절에 반드시 포함하세요
5. 적절한 JOIN과 WHERE 조건을 결정하세요
6. 중복 제거가 필요한 경우 DISTINCT를 사용하세요

=== 주의사항 ===
- [바이너리 데이터]로 표시된 컬럼은 바이너리 타입입니다
- 바이너리 컬럼은 HEX() 함수를 사용하여 16진수 문자열로 변환할 수 있습니다
- orders 테이블에는 이미 product_name 컬럼이 포함되어 있습니다
- post 테이블은 게시물 정보를 담고 있으며, orders와 직접적인 관련이 없습니다
- 테이블 간 관계를 정확히 파악하여 JOIN을 사용하세요
- 질문에서 언급된 상품명, 날짜, 금액 등의 조건은 반드시 WHERE 절에 포함해야 합니다
- 예: "노트북을 주문한" → WHERE o.product_name = '노트북'

=== 질문 ===
{request.question}

SQL 쿼리만 반환해주세요. 설명은 포함하지 마세요.
마크다운 형식(```)을 사용하지 말고 순수한 SQL 쿼리만 반환하세요.
"""
        
        # AI를 사용하여 SQL 생성
        sql_query = await ai_manager.generate_response(prompt)
        
        # AI 응답 검증
        if not sql_query:
            return Response(
                success=False,
                error="AI 응답이 없습니다."
            )
        
        # 마크다운 코드 블록 제거
        sql_query = sql_query.strip()
        if sql_query.startswith("```"):
            # 첫 번째 ``` 제거
            sql_query = sql_query[3:]
            # 언어 식별자 제거 (예: ```sql)
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
            # 마지막 ``` 제거
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
        
        # 오류 메시지인지 확인
        error_keywords = [
            "오류", "error", "실패", "fail", "시간 초과", "timeout", 
            "연결", "connection", "API", "호출", "call"
        ]
        
        if any(keyword in sql_query.lower() for keyword in error_keywords):
            return Response(
                success=False,
                error=f"AI 응답 생성 실패: {sql_query}"
            )
        
        # SQL 키워드가 포함되어 있는지 확인
        sql_keywords = ["select", "insert", "update", "delete", "from", "where", "join", "order by", "group by"]
        if not any(keyword in sql_query.lower() for keyword in sql_keywords):
            return Response(
                success=False,
                error=f"유효하지 않은 SQL 쿼리: {sql_query}"
            )
        
        # SQL 쿼리 실행
        try:
            result = db_manager.execute_query(sql_query)
            return Response(
                success=True,
                data={
                    "generated_sql": sql_query,
                    "result": result
                }
            )
        except Exception as e:
            return Response(
                success=False,
                data={"generated_sql": sql_query},
                error=f"SQL 실행 오류: {e}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 실패: {e}")
        return Response(success=False, error=str(e))

@app.get("/database/tables")
async def get_table_list():
    """테이블 목록을 반환합니다."""
    try:
        tables = db_manager.get_table_list()
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
        return Response(success=True, data={"provider": provider})
    except Exception as e:
        logger.error(f"AI Provider 정보 조회 실패: {e}")
        return Response(success=False, error=str(e))

@app.post("/ai/switch-provider")
async def switch_ai_provider(request: AIProviderRequest):
    """AI Provider를 전환합니다."""
    try:
        success = ai_manager.switch_provider(request.provider)
        if success:
            return Response(
                success=True,
                data={"provider": ai_manager.get_current_provider()}
            )
        else:
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
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level=config.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    run_http_server() 