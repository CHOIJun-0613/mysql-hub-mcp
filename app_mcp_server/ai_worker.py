
import re
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config
from database import db_manager
from ai_provider import ai_manager
from prompt import make_system_prompt
from common import Response


async def get_table_list(database_name: str = None):
    return db_manager.get_table_list(database_name)

async def get_table_schema(table_name: str):
    return db_manager.get_table_schema(table_name)

# LLM이 반환한 함수 이름(문자열)을 실제 실행할 Python 함수와 연결합니다.
available_tools = {
    "get_table_list": get_table_list,
    "get_table_schema": get_table_schema,
}

# Tool 정의
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_database_info",
            "description": "데이터베이스 정보를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_list",
            "description": "테이블 목록을 반환합니다. SQL 생성 전에 테이블 존재 여부를 확인하는 데 사용됩니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "테이블 목록을 조회할 데이터베이스 이름 (선택사항, 기본값은 현재 연결된 데이터베이스)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_schema",
            "description": "특정 테이블의 스키마 정보를 반환합니다. 이 함수는 SQL 생성 전에 반드시 호출되어야 하며, 테이블 구조와 컬럼 정보를 파악하는 데 사용됩니다. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "스키마를 조회할 테이블 이름 (반드시 제공해야 함)"
                    }
                },
                "required": ["table_name"]
            }
        }
    }
]

logger = logging.getLogger(__name__)

async def natural_language_query_work(question: str, use_tools: bool):
    """자연어를 SQL로 변환하여 실행합니다."""
    try:
        # Tool 사용 여부에 따라 분기 처리
        if use_tools:
            # Tool 사용 방식
            response = await _natural_language_query_with_tools(question)
            logger.info(f"\n\n🚨===== LLM + Tool 사용 처리 결과: \n{response}\n")
            return response
        else:
            # 기존 방식 - system prompt에 스키마 정보 포함
            response = await _natural_language_query_legacy(question)
            logger.info(f"\n\n🚨===== LLM + Tool 비사용 처리 결과: \n{response}\n")
            return response
            
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 중 오류: {e}")
        return Response(
            success=False,
            error=f"자연어 쿼리 처리 중 오류가 발생했습니다: {e}"
        )
async def make_clear_sql(response: Dict[str, Any]) :
    # AI 응답이 실제 SQL 쿼리인지 더 엄격하게 확인
    if not response:
        logger.error(f"\n>>> make_clear_sql() response is None")
        return Response(
            success=False,
            error=" make_clear_sql() response is None"
        )
    logger.debug(f"\n>>> make_clear_sql(response): \n{response}\n")
    content = ""

    # sql_return이 딕셔너리인지 확인
    if isinstance(response, dict) and "content" in response:
        content = response["content"]
    else:
        content = str(response)
    
    import re
    if "<think>" in content:
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    # 에러 메시지나 설명 텍스트인지 확인
    error_indicators = [
        "질문이 불명확합니다",
        "응답 생성 중 오류",
        "죄송합니다",
        "이해할 수 없습니다",
        "모호합니다",
        "다시 질문해 주세요"
    ]
    
    if any(indicator in content for indicator in error_indicators):
        return Response(
            success=False,
            error=f"질문이 불명확합니다: {content}"
        )
    
    # SQL 키워드가 포함되어 있는지 확인
    sql_keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
    if not any(keyword in content.upper() for keyword in sql_keywords):
        return Response(
            success=False,
            error=f"AI가 SQL 쿼리를 생성하지 못했습니다. 응답: {content}"
        )

    
    sql_query = strip_markdown_sql(content)
    
    if not sql_query or sql_query.startswith("응답 생성 중 오류"):
        return Response(
            success=False,
            error=f"SQL 생성 실패: {sql_query}"
        )
        
    clean_sql = pretty_format_sql(sql_query)
    
    logger.debug(f"pretty_format_sql: \n{clean_sql}\n")
    
    logger.debug(f"\n>>> make_clear_sql(clean_sql): \n{clean_sql}\n")
    return Response(
        success=True,
        data={
            "sql_query": clean_sql
        }
    )
async def _natural_language_query_with_tools(question: str):
    """Tool을 사용하여 자연어를 SQL로 변환합니다."""
    try:
        
        # Tool 사용 모드를 위한 system prompt 구성
        system_prompt = make_system_prompt('', '', question, True)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        logger.debug(f"시스템 프롬프트: \n{system_prompt}\n")
        logger.debug(f"사용자 질문: {question}")
        logger.info(f"Tool 방식으로 처리 시작")
        
        # Tool 결과를 별도로 수집
        tool_results = []
        
        # 최대 Tool 호출 횟수 제한
        max_tool_calls = 10
        tool_call_count = 0
        
        # 3. 에이전트 루프 시작
        while tool_call_count < max_tool_calls:
            if config.AI_PROVIDER in ["groq"] and tool_call_count > 0:
                import time
                time.sleep(30)
                
            logger.info(f"\n\n🚨===== AI API 호출 시작... (Provider: {config.AI_PROVIDER})\n")
            # Tool 결과가 있으면 추가
            if tool_results:
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result.get("tool_call_id"),
                        "name": result.get("name"),
                        "content": result.get("content")
                    })
            logger.debug(f"\n>>> messages: \n{messages}\n")
            
            import time
            start_time = time.time()
            # AI 응답 생성 
            response = await ai_manager.generate_response(
                messages,  
                tools_definition
            )
            elapsed_time = time.time() - start_time
                        
            logger.info(f"\n🚨===== AI 응답(시간:{elapsed_time:.2f}초), \n>>> response:\n{response}\n")
                        
            # response에 'content'가 있고 '<think>...</think>'이 포함되어 있으면 제거 후 다시 할당
            if "content" in response and isinstance(response["content"], str):
                import re
                if "<think>" in response["content"]:
                    response["content"] = re.sub(r'<think>.*?</think>', '', response["content"], flags=re.DOTALL).strip()
            
            if "error" in response:
                logger.error(f"AI 응답 생성 실패: {response['error']}")
                return Response(
                    success=False,
                    error=f"AI 응답 생성 실패: {response['error']}"
                )

            # AI 응답 구조 검증
            if not isinstance(response, dict):
                logger.error(f"AI 응답이 올바른 형식이 아닙니다: {type(response)}")
                return Response(
                    success=False,
                    error="AI 응답 형식이 올바르지 않습니다."
                )
            
            if "tool_calls" not in response or not response["tool_calls"]: 
                logger.debug(f"\n>>> 최종 답변 감지: \n")
                # 4. LLM이 도구 사용 대신 최종 답변을 한 경우 -> 루프 종료
                return await _finalize_sql_response(response)
            elif "tool_calls" in response:
                # tool_calls가 빈 리스트인 경우 (최종 답변)
                if isinstance(response["tool_calls"], list) and len(response["tool_calls"]) == 0:
                    logger.debug(f"\n>>> tool_calls가 빈 리스트([])입니다. 최종 답변으로 처리합니다.\n")
                    return await _finalize_sql_response(response)
                # tool_calls에 값이 채워져 있는 경우 (도구 호출)
                elif isinstance(response["tool_calls"], list) and len(response["tool_calls"]) > 0:
                    logger.debug(f"\n>>> 도구 호출 감지: \n{(tool_call_count+1)} 회차\n")
                    result = await _exec_tool_response(response)
                    if "error" in result:
                        return Response(
                            success=False,
                            error=f"Tool 실행 오류: {result['error']}"
                        )
                    # result가 리스트이므로, 각 결과를 tool_results에 append
                    for r in result:
                        tool_results.append(r)
                    
                    tool_call_count += 1
                else:
                    # tool_calls가 리스트가 아닌 경우 등 비정상 응답
                    logger.error(f"AI 응답의 tool_calls 필드가 올바르지 않습니다: {response['tool_calls']}")
                    return Response(
                        success=False,
                        error="AI 응답의 tool_calls 필드가 올바르지 않습니다."
                    )
            else:
                # 잘못된 응답 (tool_calls 필드가 없음)
                logger.error(f"AI 응답에 tool_calls 필드가 없습니다: {response}")
                return Response(
                    success=False,
                    error="AI 응답에 tool_calls 필드가 없습니다."
                )
        # 최대 Tool 호출 횟수 초과
        return Response(
            success=False,
            error=f"Tool 호출 횟수가 최대 제한({max_tool_calls})을 초과했습니다. 질문을 더 구체적으로 작성해주세요."
        )
        
    except Exception as e:
        logger.error(f"Tool 방식 처리 중 오류: {e}")
        return Response(
            success=False,
            error=f"Tool 방식 처리 중 오류가 발생했습니다: {e}"
        )

async def _finalize_sql_response(response: Dict[str, Any]) :
    if not response:
        logger.error(f"\n>>> _finalize_sql_response() response is None")
        return Response(
            success=False,
            error=" _finalize_sql_response() response is None"
        )
    logger.debug(f"\n>>> _finalize_sql_response(response): \n{response}\n")
    content = response.get("content", "")
    # content가 '```json\n{\n' 또는 '{"name"'으로 시작하면 tool_calls와 동일하게 처리 (루프 계속)
    if content.strip().startswith("```json\n{\n") or content.strip().startswith('{"name"'):
        logger.debug("content가 tool_calls와 동일한 JSON 함수 호출 형식입니다. 루프를 계속 진행합니다.")
    else:
        # AI 응답 정리 -> SQL 쿼리 추출
        result_sql = await make_clear_sql(response)
        logger.debug(f"\n>>> result_sql: \n{result_sql}\n")
        # result_sql이 Response 객체인지 확인
        if hasattr(result_sql, 'success') and not result_sql.success:
            return result_sql  # 에러가 있으면 그대로 반환
        
        # 성공한 경우 data에서 sql_query 추출
        clean_sql = result_sql.data.get("sql_query", "")
        logger.info(f"\n✅ AI 응답 최종 결과(content): \n{clean_sql}\n")
        # SQL 쿼리 실행
        try:
            result = db_manager.execute_query(clean_sql)
            sql_query_result = Response(
                success=True,
                data={
                    "sql_query": clean_sql,
                    "result": result
                }
            )
            logger.info(f"\n\n=====✅ 쿼리 실행 결과: \n{sql_query_result.data}\n")
            return sql_query_result
        except Exception as e:
            return Response(
                success=False,
                error=f"SQL 실행 오류: {e}"
            )
           
async def _exec_tool_response(response: Dict[str, Any]) -> Dict[str, Any]:
    tool_results = []
    if not response:
        logger.error(f"\n>>> _exec_tool_response() response is None")
        return Response(
            success=False,
            error=" _exec_tool_response() response is None"
        )
    logger.debug(f"\n>>> _exec_tool_response(response): \n{response}\n")
    
    #LLM이 도구 사용을 요청한 경우 -> 도구 실행
    parsed_tool_calls = _parse_tool_calls(response)                
    logger.debug(f"AI 응답[tool_calls]: \n{parsed_tool_calls}\n")

    for tool_call in parsed_tool_calls:
        func_name = tool_call["name"]
        func_args = tool_call["arguments"]
        tool_call_id = tool_call["tool_call_id"]
        logger.debug(f"Tool 호출 감지: {func_name}({json.dumps(func_args, ensure_ascii=False)})")
        
        if func_name in available_tools:
            functoin_to_call = available_tools[func_name]
            logger.debug(f"🧠 LLM 요청: 로컬 함수 {func_name}, ({json.dumps(func_args, ensure_ascii=False)}) 실행")
            try:
                tool_result = await functoin_to_call(**func_args)
                logger.debug(f"🧠 로컬 함수 실행 결과: {tool_result}")
                
                # Tool 실행 결과를 tool_results에 추가 (메시지 히스토리에 추가하지 않음)
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "name": func_name,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
            except Exception as e:
                logger.error(f"🧠 로컬 함수 실행 오류: {e}")
                tool_result = f"Tool 실행 중 오류가 발생했습니다: {e}"
                tool_results.append({
                    'tool_call_id': tool_call_id,
                    'name': func_name,
                    'content': json.dumps({"error": str(e)}, ensure_ascii=False)
                })
        else:
            logger.error(f"🧠 알 수 없는 도구 호출: {func_name}")
    return tool_results

async def get_table_list_and_schema()-> Dict[str, Any]:
    response = db_manager.get_database_info()
    if "error" in response:
        return Response(
            success=False,
            error=f"데이터베이스 연결 오류: {response['error']}"
        )
    database_name = response.get("database_name", "unknown")

    schema_info = ""
    table_list = db_manager.get_table_list(database_name)
    # table_list에서 시스템 테이블(INFORMATION_SCHEMA, mysql, performance_schema, sys)로 시작하는 테이블 제외
    if isinstance(table_list, list):
        user_tables = [table for table in table_list 
                        if not table.get("TABLE_NAME", "").startswith("INFORMATION_SCHEMA")
                        and not table.get("TABLE_NAME", "").startswith("mysql")
                        and not table.get("TABLE_NAME", "").startswith("performance_schema")
                        and not table.get("TABLE_NAME", "").startswith("sys")]
    else:
        user_tables = []

    # 테이블별 스키마 정보를 리스트 형태로 생성
    table_schemas = []
    for table_info in user_tables:
        try:
            schema = db_manager.get_table_schema(table_info.get("TABLE_NAME", ""))
            logger.debug(f"테이블 {table_info.get('TABLE_NAME', '')} 스키마: \n{schema}\n")
            table_schemas.append(schema)
        except Exception as e:
            logger.warning(f"테이블 {table_info.get('TABLE_NAME', '')} 스키마 조회 실패: {e}")
            continue

    schema_info = json.dumps(table_schemas, ensure_ascii=False)
    logger.debug(f"테이블 스키마 정보: \n{schema_info}\n")
    return Response(
        success=True,
        data={
            "database_name": database_name,
            "table_list": table_list,
            "table_schemas": table_schemas
        }
    )

async def _natural_language_query_legacy(question: str):
    """기존 방식으로 자연어를 SQL로 변환합니다 (system prompt에 스키마 정보 포함)."""
    try:
        # 테이블 목록과 스키마 정보 가져오기
        result = await get_table_list_and_schema()
        if "error" in result:
            return Response(
                success=False,
                error=f"테이블 스키마 조회 실패: {result['error']}"
            )
        # result는 Response 객체이므로, result.data.get("database_name", "")로 가져와야 합니다.
        database_name = result.data.get("database_name", "")
        table_schemas = result.data.get("table_schemas", [])
        if len(table_schemas) == 0:
            return Response(
                success=False,
                error=f"테이블 스키마 조회 실패: {result['error']}"
            )
        schema_info = json.dumps(table_schemas, ensure_ascii=False)
        system_prompt = make_system_prompt(database_name, schema_info, question, False)
       
        logger.info(f"자연어 쿼리: \n\n[{question}]\n")
       
        # AI를 사용하여 SQL 생성 (tools 없이)
        # 기존 방식은 system과 user 메시지를 분리하여 전달
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        logger.info(f"\n\n🚨===== AI API 호출 시작... (Provider: {config.AI_PROVIDER})\n")
        logger.debug(f"\n>>> messages: \n{messages}\n")
        
        import time
        start_time = time.time()
        #AI API 호출
        response = await ai_manager.generate_response(messages)
        elapsed_time = time.time() - start_time
                        
        logger.info(f"\n🚨===== AI 응답(시간:{elapsed_time:.2f}초), \n>>> response:\n{response}\n")
        
        # AI 응답 정리 -> SQL 쿼리 추출
        result_sql = await make_clear_sql(response)
        
        # result_sql이 Response 객체인지 확인
        if hasattr(result_sql, 'success') and not result_sql.success:
            return result_sql  # 에러가 있으면 그대로 반환
        
        # 성공한 경우 data에서 sql_query 추출
        clean_sql = result_sql.data.get("sql_query", "")
        
        # SQL 쿼리 실행
        try:
            result = db_manager.execute_query(clean_sql)
            return Response(
                success=True,
                data={
                    "sql_query": clean_sql,
                    "result": result
                }
            )
        except Exception as e:
            return Response(
                success=False,
                error=f"SQL 실행 오류: {e}"
            )
            
    except Exception as e:
        logger.error(f"기존 방식 처리 중 오류: {e}")
        return Response(
            success=False,
            error=f"기존 방식 처리 중 오류가 발생했습니다: {e}"
        )



def strip_markdown_sql(sql_query: str) -> str:
    """
    SQL 쿼리에서 마크다운 형식을 제거합니다.
    ```sql\n...\n``` 형태의 마크다운을 제거하고 순수 SQL만 반환합니다.
    """
    if not sql_query:
        return sql_query
    
    # ```sql\n...\n``` 패턴 제거
    sql_pattern = r'```sql\s*\n(.*?)\n```'
    match = re.search(sql_pattern, sql_query, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # ```...``` 패턴 제거 (sql 태그가 없는 경우)
    generic_pattern = r'```\s*\n(.*?)\n```'
    match = re.search(generic_pattern, sql_query, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # ```...``` 패턴 제거 (한 줄인 경우)
    single_line_pattern = r'```(.*?)```'
    match = re.search(single_line_pattern, sql_query)
    if match:
        return match.group(1).strip()
    
    return sql_query.strip()

def pretty_format_sql(sql_query: str) -> str:
    """
    SQL문을 입력받아 보기 좋게 정렬된(pretty) SQL 문자열을 반환합니다.
    - 키워드 기준 줄바꿈 및 들여쓰기 적용
    - 세미콜론, 괄호 등도 적절히 처리
    """
    if not sql_query or not isinstance(sql_query, str):
        return sql_query
    
    # SQL 쿼리 pretty 포매팅 적용 
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
        
    return pretty_sql

def _parse_tool_calls(response: Dict[str, Any]) -> list:
    """
    tool_calls 리스트를 파싱하여 필요한 정보를 추출합니다.
    """
    if not response:
        return []
    
    if "tool_calls" not in response and "content" not in response:
        return []
    
    parsed_tool_calls = []
    
    if "tool_calls" in response:    
        for tool_call in response["tool_calls"]:
            try:
                function_info = tool_call.get('function', {})
                name = function_info.get('name')
                tool_call_id = tool_call.get('id', None)
                index = function_info.get('index', 1)
                arguments = function_info.get('arguments')  
                
                # arguments가 문자열이면 json 파싱 시도
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except Exception:
                        pass
                
                # arguments가 빈 dict일 수 있음
                if arguments is None:
                    arguments = {}
                
                parsed_tool_calls.append({
                    'tool_call_id': tool_call_id,
                    'name': name,
                    'index': index,
                    'arguments': arguments
                })
            except Exception as e:
                logger.warning(f"Tool call 파싱 중 오류: {e}")
                continue
    
    if "tool_calls" not in response and "content" in response:
        content = response['content']
        if content.strip().startswith("```json\n{\n"):
            # '```json'과 '```' 사이의 JSON 부분 추출
            import re
            
            match = re.search(r'```json\s*([\s\S]+?)\s*```', content)
            if match:
                json_str = match.group(1)
                try:
                    function_info = json.loads(json_str)
                    name = function_info.get('name')
                    arguments = function_info.get('arguments')
                    tool_call_id = None
                    index = 1
                    parsed_tool_calls.append({
                        'name': name,
                        'tool_call_id': tool_call_id,
                        'index': index,
                        'arguments': arguments
                    })
                except Exception as e:
                    print(f"content에서 JSON 파싱 실패: {e}")        
        elif content.strip().startswith('{"name"'):
            function_info = json.loads(content)
            name = function_info.get('name')
            arguments = function_info.get('arguments')
            tool_call_id = None
            index = 1
            parsed_tool_calls.append({
                'name': name,
                'tool_call_id': tool_call_id,
                'index': index,
                'arguments': arguments
            })
        else:
            logger.warning("content가 tool_calls와 동일한 JSON 함수 호출 형식이 아닙니다.")
            return []
    
    return parsed_tool_calls
        
