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
        
        # 쿼리 유효성 검사
        if not db_manager.validate_query(request.query):
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
        if request.query.strip().upper().startswith('SELECT'):
            result = db_manager.execute_query(request.query)
        else:
            affected_rows = db_manager.execute_non_query(request.query)
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
        
        # 모든 사용자 테이블의 스키마 정보를 사용
        for table_name in user_tables:
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
당신은 MySQL 데이터베이스 쿼리 전문가입니다. 자연어를 SQL 쿼리로 변환해주세요.

⚠️ 매우 중요한 규칙:
1. 순수한 SQL 쿼리만 반환하세요
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요

예시 올바른 응답:
SELECT * FROM users;

예시 잘못된 응답:
```sql
SELECT * FROM users;
```
또는
SELECT * FROM users;
### 설명: 사용자 테이블의 모든 데이터를 조회합니다.

=== 추가 정보 ===
MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
-해결 방법: 아래와 같이, 별칭(alias)를 주는 방법으로 사용할 수는 있다
예시:
SELECT * FROM (SELECT * FROM UserInfo WHERE CreateDate >= '2010-01-01' LIMIT 0,10) AS temp_tbl;

데이터베이스: {db_info.get('database_name', 'unknown')}

=== 테이블 스키마 정보 ===
{schema_info}

=== 질문 ===
{request.question}

이제 위 질문에 대한 SQL 쿼리만 반환하세요:
"""
       
        logger.info(f"자연어 쿼리: \n\n[{request.question}]\n")
        logger.debug(f"자연어 쿼리 프롬프트: \n{prompt}\n")
        # AI를 사용하여 SQL 생성
        sql_query = await ai_manager.generate_response(prompt)
        
        # AI 응답 검증
        if not sql_query:
            return Response(
                success=False,
                error="AI 응답이 없습니다."
            )
        
        # 마크다운 코드 블록 및 추가 텍스트 제거
        sql_query = sql_query.strip()
        
        # 마크다운 코드 블록 제거
        if sql_query.startswith("```"):
            # 첫 번째 ``` 제거
            sql_query = sql_query[3:]
            # 언어 식별자 제거 (예: ```sql, ```, ```mysql)
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
            elif sql_query.startswith("mysql"):
                sql_query = sql_query[5:]
            # 마지막 ``` 제거
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
        
        # 설명 텍스트 제거 (###, ##, #, 설명:, 설명 등)
        import re
        # ###, ##, # 로 시작하는 라인 제거
        sql_query = re.sub(r'^#+\s*.*$', '', sql_query, flags=re.MULTILINE)
        # 설명:, 설명, ### 설명 등 제거
        sql_query = re.sub(r'^.*(설명|결과|분석|최종).*$', '', sql_query, flags=re.MULTILINE | re.IGNORECASE)
        # 빈 줄 제거
        sql_query = re.sub(r'\n\s*\n', '\n', sql_query)
        # 앞뒤 공백 제거
        sql_query = sql_query.strip()
        
        # 첫 번째 SQL 문장만 추출 (세미콜론까지)
        if ';' in sql_query:
            sql_query = sql_query[:sql_query.find(';')+1]
        
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
        # SQL 쿼리 pretty 포맷 적용 
        import sqlparse
        try:
            pretty_sql = sqlparse.format(
                sql_query, 
                reindent_aligned=True, 
                use_space_around_operators=True,
                indent_width=2,
                keyword_case='upper',
                output_format='sql'
            )


        except Exception as e:
            logger.warning(f"sqlparse 포매팅 실패: {e}")
            pretty_sql = sql_query
        
        logger.info(f"AI 생성 SQL :\n\n{pretty_sql}\n")

        # SQL 쿼리 실행
        try:
            sql_query = pretty_sql
            result = db_manager.execute_query(sql_query)
            response_data = {
                "generated_sql": sql_query,
                "result": result
            }
            logger.info(f"자연어 쿼리 실행 결과: \n\n{response_data}\n")
            return Response(
                success=True,
                data=response_data
            )
        except Exception as e:
            error_data = {"generated_sql": sql_query}
            logger.debug(f"자연어 쿼리 실행 오류 데이터: {error_data}")
            return Response(
                success=False,
                data=error_data,
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
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level=config.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    run_http_server() 