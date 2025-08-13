
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
from common import Response


async def get_table_list():
    return db_manager.get_table_list()

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
            "description": "데이터베이스 정보와 테이블 목록을 반환합니다.",
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

logger = logging.getLogger(__name__)

async def natural_language_query_work(question: str, use_tools: bool):
    """자연어를 SQL로 변환하여 실행합니다."""
    try:
        # Tool 사용 여부에 따라 분기 처리
        if use_tools:
            # Tool 사용 방식
            return await _run_agentic_query(question)
        else:
            # 기존 방식 - system prompt에 스키마 정보 포함
            return await _natural_language_query_legacy(question)
            
    except Exception as e:
        logger.error(f"자연어 쿼리 처리 중 오류: {e}")
        return Response(
            success=False,
            error=f"자연어 쿼리 처리 중 오류가 발생했습니다: {e}"
        )
        
async def _run_agentic_query(question: str):
    """Tool을 사용하여 자연어를 SQL로 변환합니다."""
    try:
        
        # Tool 사용 모드를 위한 system prompt 구성
        system_prompt = make_system_prompt('', '', question, True)
        
        # 메시지 히스토리 초기화
        # 1. 초기 메시지 설정 (시스템 프롬프트 + 사용자 질문)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user","content": question}
        ]

        logger.debug(f"초기 messages: \n{messages}\n")
        logger.debug(f"tool_definition: \n{tools_definition}\n")
        logger.info(f"자연어 질문: {question}")
        logger.info(f"Tool 방식으로 처리 시작")
        
        # 최대 Tool 호출 횟수 제한 (무한 루프 방지)
        max_tool_calls = 5
        tool_call_count = 0
        
        # 2. 에이전트 루프 시작 (최대 5번의 도구 호출 허용)
        while tool_call_count < max_tool_calls:
            logger.info("\n\n🚨===== AI API 호출 시작...\n")
            # AI 응답 생성
            response = await ai_manager.generate_response_with_tools(messages, tools_definition)
            logger.info(f"\n🚨===== AI 응답(response): \n{response}\n")
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

            response_messages = response.get("messages","")
            logger.debug(f"AI 응답[messages]: \n{response_messages}\n")
            
            if response_messages:
                messages.append(response_messages)
                            
            # 4. LLM이 도구 사용 대신 최종 답변을 한 경우 -> 루프 종료
            if "tool_calls" not in response or not response["tool_calls"]: 
                sql_query = response.get("content", "")
                logger.info(f"\n✅ AI 응답 최종 결과(content): \n{sql_query}\n")
                # AI 응답이 실제 SQL 쿼리인지 더 엄격하게 확인
                if not sql_query:
                    return Response(
                        success=False,
                        error="AI 응답이 비어있습니다."
                    )
                
                # 에러 메시지나 설명 텍스트인지 확인
                error_indicators = [
                    "질문이 불명확합니다",
                    "응답 생성 중 오류",
                    "죄송합니다",
                    "이해할 수 없습니다",
                    "모호합니다",
                    "다시 질문해 주세요"
                ]
                
                if any(indicator in sql_query for indicator in error_indicators):
                    return Response(
                        success=False,
                        error=f"질문이 불명확합니다: {sql_query}"
                    )
                
                # SQL 키워드가 포함되어 있는지 확인
                sql_keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
                if not any(keyword in sql_query.upper() for keyword in sql_keywords):
                    return Response(
                        success=False,
                        error=f"AI가 SQL 쿼리를 생성하지 못했습니다. 응답: {sql_query}"
                    )

                # 마크다운 형식 제거
                clean_sql = strip_markdown_sql(sql_query)
                logger.info(f"원본 SQL: {sql_query}")
                logger.info(f"정리된 SQL: {clean_sql}")
                
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
                
              
            
            # 5. LLM이 도구 사용을 요청한 경우 -> 도구 실행
            tool_calls = response["tool_calls"]
            logger.debug(f"AI 응답[tool_calls]: \n{tool_calls}\n")
            logger.info(f"Tool 호출 감지 (횟수: {tool_call_count + 1}): {[tc['function']['name'] for tc in tool_calls]}")
            
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = tool_call["function"]["arguments"]
                logger.debug(f"Tool 호출 감지 (횟수: {tool_call_count + 1}): {func_name}")
                logger.debug(f"Tool 호출 인자: {func_args}")
                
                if func_name in available_tools:
                    functoin_to_call = available_tools[func_name]
                    logger.debug(f"🧠 LLM 요청: 로컬 함수 {func_name}({json.dumps(func_args, ensure_ascii=False)}) 실행")
                    
                    try:
                        #tool_result = await functoin_to_call(**func_args)
                        if func_name == "get_table_list":
                            tool_result = db_manager.get_table_list()
                        elif func_name == "get_table_schema":
                            table_name = func_args.get("table_name", "")
                            if table_name:
                                tool_result = db_manager.get_table_schema(table_name) 
                            else:
                                tool_result = "테이블 이름이 제공되지 않았습니다."
                              
                        logger.debug(f"🧠 로컬 함수 실행 결과: {tool_result}")
                        messages.append({
                            "role": "tool",
                            #"tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": json.dumps(tool_result),
                        })
                    except Exception as e:
                        logger.error(f"🧠 로컬 함수 실행 오류: {e}")
                        tool_result = f"Tool 실행 중 오류가 발생했습니다: {e}"
                        messages.append({
                            'role': 'tool',
                            #'tool_call_id': tool_call['id'],
                            'name': func_name,
                            'content': json.dumps({"error": str(e)})
                        })
                else:
                    logger.error(f"🧠 알 수 없는 도구 호출출: {func_name}")
                    
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
        
async def _natural_language_query_with_tools(question: str):
    """Tool을 사용하여 자연어를 SQL로 변환합니다."""
    try:
        
        # Tool 사용 모드를 위한 system prompt 구성
        system_prompt = make_system_prompt('', '', question, True)
        
        # 메시지 히스토리 초기화
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]

        logger.debug(f"초기 messages: \n{messages}\n")
        logger.debug(f"tools_definition: \n{tools_definition}\n")
        logger.info(f"자연어 질문: {question}")
        logger.info(f"Tool 방식으로 처리 시작")
        
        # 최대 Tool 호출 횟수 제한 (무한 루프 방지)
        max_tool_calls = 5
        tool_call_count = 0
        
        while tool_call_count < max_tool_calls:
            # AI 응답 생성
            response = await ai_manager.generate_response_with_tools(messages, tools_definition)
            
            if "error" in response:
                logger.error(f"AI 응답 생성 실패: {response['error']}")
                return Response(
                    success=False,
                    error=f"AI 응답 생성 실패: {response['error']}"
                )

            logger.debug(f"AI 응답: \n{response}\n")
            
            # AI 응답 구조 검증
            if not isinstance(response, dict):
                logger.error(f"AI 응답이 올바른 형식이 아닙니다: {type(response)}")
                return Response(
                    success=False,
                    error="AI 응답 형식이 올바르지 않습니다."
                )
            
            logger.debug(f"AI 응답: \n{response}\n")
            
            # Tool 호출이 없고 content도 없는 경우 처리
            if not response.get("tool_calls") and not response.get("content"):
                logger.warning("AI 응답에 Tool 호출과 content가 모두 없습니다. 기존 방식으로 전환")
                return Response(
                    success=False,
                    error="AI 응답에 Tool 호출과 content가 모두 없습니다."
                )
            
            # Tool 호출이 없으면 최종 SQL 응답
            if "tool_calls" not in response or not response["tool_calls"]:
                sql_query = response.get("content", "")
                
                # AI 응답이 실제 SQL 쿼리인지 더 엄격하게 확인
                if not sql_query:
                    return Response(
                        success=False,
                        error="AI 응답이 비어있습니다."
                    )
                
                # 에러 메시지나 설명 텍스트인지 확인
                error_indicators = [
                    "질문이 불명확합니다",
                    "응답 생성 중 오류",
                    "죄송합니다",
                    "이해할 수 없습니다",
                    "모호합니다",
                    "다시 질문해 주세요"
                ]
                
                if any(indicator in sql_query for indicator in error_indicators):
                    return Response(
                        success=False,
                        error=f"질문이 불명확합니다: {sql_query}"
                    )
                
                # SQL 키워드가 포함되어 있는지 확인
                sql_keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
                if not any(keyword in sql_query.upper() for keyword in sql_keywords):
                    return Response(
                        success=False,
                        error=f"AI가 SQL 쿼리를 생성하지 못했습니다. 응답: {sql_query}"
                    )

                # 마크다운 형식 제거
                clean_sql = strip_markdown_sql(sql_query)
                logger.info(f"원본 SQL: {sql_query}")
                logger.info(f"정리된 SQL: {clean_sql}")
                
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
            
            # Tool 호출 처리
            tool_calls = response["tool_calls"]
            
            logger.info(f"Tool 호출 감지 (횟수: {tool_call_count + 1}): {[tc['function']['name'] for tc in tool_calls]}")
            
            # Tool 실행 결과를 메시지 히스토리에 추가
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = tool_call["function"]["arguments"]
                
                try:
                    # Tool 실행
                    if func_name == "get_database_info":
                        db_info = db_manager.get_database_info()
                        tool_result = str(db_info)
                    elif func_name == "get_table_list":
                        table_list = db_manager.get_table_list()
                        tool_result = str(table_list)
                    elif func_name == "get_table_schema":
                        logger.debug(f"func_name:\n----------\n{func_name}\n")
                        # get_table_schema의 arguments가 dict가 아닐 수 있으므로 안전하게 처리
                        if isinstance(func_args, str):
                            import json
                            try:
                                func_args = json.loads(func_args)
                            except Exception as e:
                                logger.error(f"get_table_schema arguments 파싱 오류: {e}")
                                func_args = {}
                        table_name = func_args.get("table_name", "")
                        logger.debug(f"table_name: {table_name}")
                        if table_name:
                            schema = db_manager.get_table_schema(table_name)
                            logger.debug(f"get_table_schema 결과: {schema}")
                            tool_result = str(schema)
                        else:
                            tool_result = "테이블 이름이 제공되지 않았습니다."
                    else:
                        tool_result = f"알 수 없는 도구: {func_name}"
                    
                    # Tool 결과를 메시지 히스토리에 추가
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call["id"]
                    })
                    
                    logger.debug(f"Tool 실행 결과 ({func_name}): {tool_result[:200]}...")
                    
                except Exception as e:
                    logger.error(f"Tool 실행 오류 ({func_name}): {e}")
                    tool_result = f"Tool 실행 중 오류가 발생했습니다: {e}"
                    
                    # Tool 실행 실패 결과도 메시지 히스토리에 추가
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call["id"]
                    })
            
            # Tool 호출 횟수 증가
            tool_call_count += 1
            
            # Tool 호출 후 AI에게 다시 응답 요청하기 전에 로깅
            logger.debug(f"Tool 호출 완료 후 AI에게 재응답 요청 (횟수: {tool_call_count})")
            logger.debug(f"현재 메시지 수: {len(messages)}")
            
            # Tool 호출 후 AI에게 다시 응답 요청
            messages.append({
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": tool_calls
            })
            
            logger.debug(f"Tool 호출 후 AI 응답: \n{response}\n")
            
            # AI 응답이 비어있는 경우 처리
            if not response.get("content"):
                logger.warning(f"AI 응답이 비어있습니다. Tool 호출 횟수: {tool_call_count}")
                
                # get_table_list 호출 후 AI 응답이 비어있으면 강제로 다음 단계 진행
                if tool_call_count >= 1:
                    logger.info("AI 응답이 비어있어 다음 Tool 호출 단계로 진행")
                    
                    # get_table_list가 호출되었다면 AI에게 스키마 정보를 바탕으로 SQL 생성 요청
                    if any("get_table_list" in str(tc) for tc in tool_calls):
                        logger.info("get_table_list 호출 감지, AI에게 SQL 생성 요청")
                        messages.append({
                            "role": "user",
                            "content": "테이블 목록과 스키마 정보를 확인했습니다. 이제 위의 질문에 대한 SQL 쿼리를 생성해주세요."
                        })
                    
                    continue
        
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

async def _natural_language_query_legacy(question: str):
    """기존 방식으로 자연어를 SQL로 변환합니다 (system prompt에 스키마 정보 포함)."""
    try:
        # 데이터베이스 스키마 정보 가져오기
        db_info = db_manager.get_database_info()
        if "error" in db_info:
            raise HTTPException(status_code=500, detail=f"데이터베이스 연결 오류: {db_info['error']}")
        
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
        
        # 시스템 프롬프트 구성 
        database_name=db_info.get('database_name', 'unknown')

        prompt = make_system_prompt(database_name, schema_info, question, False)
       
        logger.info(f"자연어 쿼리: \n\n[{question}]\n")
        logger.debug(f"자연어 쿼리 프롬프트: \n{prompt}\n")
        # AI를 사용하여 SQL 생성 (tools 없이)
        sql_return = await ai_manager.generate_response(prompt)
        
        sql_query = strip_markdown_sql(sql_return)
        
        logger.debug(f"AI 응답 SQL: \n{sql_query}")
        
        # AI 응답이 실제 SQL 쿼리인지 확인
        if not sql_query or sql_query.startswith("응답 생성 중 오류"):
            return Response(
                success=False,
                error=f"SQL 생성 실패: {sql_query}"
            )
        
         
        clean_sql = pretty_format_sql(sql_query)
        
        logger.debug(f"pretty_format_sql: \n{clean_sql}\n")
        
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

def make_system_prompt(database_name: str, schema_info: str, question: str, use_tools: bool) -> str:
    """
    시스템 프롬프트를 생성합니다.
    """
    default_prompt = """
당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다.
"""
    
    default_prompt_with_tools = """
당신은 사용자의 자연어 질문을 분석하여, 도구를 사용해 필요한 정보를 수집하고 최종적으로 완벽한 MySQL 쿼리를 생성하는 AI 에이전트입니다.

## 지시사항
1.  **사고(Thinking) 단계:** 먼저 사용자의 질문을 분석하여 어떤 정보가 필요한지 계획을 세웁니다.
2.  **도구 사용(Tool Use) 단계:** 계획에 따라 필요한 도구를 최소한으로 사용합니다.
    - **1순위:** `get_table_list`를 호출하여 테이블 목록을 파악합니다.
    - **2순위:** 질문과 가장 관련성이 높은 테이블 1~3개를 추론합니다.
    - **3순위:** 모든 해당 테이블에 대해서는 반드시 `get_table_schema`를 호출(필수)하여 테이블 구조를 파악합니다.
    - **4순위:** 모든 정보가 수집되었다고 판단되면, SQL을 생성합니다.
3.  **최종 답변(Final Answer) 단계:**
    - 모든 정보 수집이 완료되면, 분석한 내용을 바탕으로 **순수한 SQL 쿼리 하나만** 생성합니다.
    - 마크다운(```), 설명, 주석 없이 오직 SQL 쿼리만 반환해야 합니다.
    - SQL 쿼리는 반드시 세미콜론(;)으로 끝나야 합니다.
    - 최종 답변은 반드시 순수한 SQL 쿼리만 반환해야 합니다.


"""
    basic_rule_prompt = """
⚠️ 매우 중요한 규칙:
1. 최종 답변은 반드시 순수한 SQL 쿼리만 반환해야 합니다.
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요
6. 질문이 모호하거나 문장구성이 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
- 예시: 'afdksafdsalfj', 'ㅁ렁ㄴ123ㅓ  마ㅣㄹaaghgl'등
7. ID는 시스템에게만 의미있는 값이므로 ID보다는 이름(명) 필드를 SQL의 조회 필드로 사용하세요.
- 예시: user_id 보다는 user_name 필드를 조회 필드로 사용하세요.
- ID가 사용자 질의에 '~id', '~번호' 등으로 표시되어 있는 경우만만 필드로 사용하세요.
8. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가
- MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
- 해결 방법: 아래와 같이, 별칭(alias)를 주는 방법으로 사용할 수는 있다
- 예시: SELECT * FROM (SELECT * FROM UserInfo WHERE CreateDate >= '2010-01-01' LIMIT 0,10) AS temp_tbl;   
"""
    database_prompt = """

=== 데이터베이스: {database_name} 

=== 테이블 스키마 정보 ===
{schema_info}

"""
    
    use_tools_prompt = """

=== 사용할 수 있는 도구 ===
{tool_list}

=== tool 사용 순서 (절대적으로 필수):
🚨 첫 번째 단계: 반드시 get_table_list()를 호출하여 사용 가능한 테이블 목록을 확인하세요
🚨 두 번째 단계: 질문과 가장 관련성이 높은 테이블 1~3개를 추론하고 호출하여
🚨 세 번째 단계: 추론한 테이블들에 대해서 테이블의 스키마를 get_table_schema("테이블명")로 조회하세요
🚨 네 번째 단계: 스키마 정보를 확인한 후에만 SQL 쿼리를 생성하세요

🚫 금지사항:
- 테이블 목록을 확인(get_table_list)하지 않고 SQL을 생성하지 마세요
- 존재하지 않는 테이블 이름을 사용하지 마세요
- 존재하지 않는 컬럼 이름을 사용하지 마세요
- 스키마 정보 없이 SQL을 생성하지 마세요
"""
    close_prompt = """

=== 질문 ===\n{question}

"""
    
    close_prompt_with_tools = """

=== 질문 ===\n{question}

위 질문에 대한 답변을 위해 필요한 도구를 사용하세요. 모든 도구 사용이 완료된 후에만 SQL 쿼리를 생성하세요.
"""

    if use_tools:
        temp_prompt = default_prompt_with_tools +basic_rule_prompt+ use_tools_prompt + close_prompt_with_tools
        prompt = temp_prompt.format(
            tool_list=tools_definition,
            question=question)
    else:
        temp_prompt = default_prompt + basic_rule_prompt + database_prompt + close_prompt
        prompt = temp_prompt.format(
            database_name=database_name,
            schema_info=schema_info,
            question=question)
        
    return prompt

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
        
    return pretty_sql
