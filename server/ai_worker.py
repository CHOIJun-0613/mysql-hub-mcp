
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
                "properties": {}
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
        
        # 1. 시스템 프롬프트는 한 번만 전달
        system_message = {"role": "system", "content": system_prompt}
        
        # 2. 사용자 질문도 한 번만 전달
        user_message = {"role": "user", "content": question}

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
            if config.AI_PROVIDER == "groq" and tool_call_count > 0:
                import time
                time.sleep(30)
                
            logger.info("\n\n🚨===== AI API 호출 시작...\n")
            
            # 4. 핵심 개선: 시스템 프롬프트는 한 번만, Tool 결과만 누적
            current_messages = [
                system_message,  # 시스템 프롬프트 (한 번만)
                user_message,    # 사용자 질문 (한 번만)
            ]
            
            # Tool 결과가 있으면 추가
            if tool_results:
                for result in tool_results:
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": result.get("tool_call_id"),
                        "name": result.get("name"),
                        "content": result.get("content")
                    })
            
            # AI 응답 생성 (시스템 프롬프트는 한 번만, Tool 결과만 누적)
            response = await ai_manager.generate_response_with_tools(
                current_messages,  # 현재 상태의 메시지들
                tools_definition,
                None  # tool_results 파라미터는 사용하지 않음
            )
            
            logger.info(f"\n🚨===== AI 응답(response): \n{response}\n")
            
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

            # 4. LLM이 도구 사용 대신 최종 답변을 한 경우 -> 루프 종료
            if "tool_calls" not in response or not response["tool_calls"]: 
                content = response.get("content", "")
                # content가 '```json\n{\n' 또는 '{"name"'으로 시작하면 tool_calls와 동일하게 처리 (루프 계속)
                if content.strip().startswith("```json\n{\n") or content.strip().startswith('{"name"'):
                    logger.debug("content가 tool_calls와 동일한 JSON 함수 호출 형식입니다. 루프를 계속 진행합니다.")
                else:
                    sql_query = content
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
            parsed_tool_calls = _parse_tool_calls(response)                
            logger.debug(f"AI 응답[tool_calls]: \n{parsed_tool_calls}\n")
            logger.info(f"Tool 호출 감지 (횟수: {tool_call_count + 1}): {[tc['name'] for tc in parsed_tool_calls]}")

            for tool_call in parsed_tool_calls:
                func_name = tool_call["name"]
                func_args = tool_call["arguments"]
                tool_call_id = tool_call["tool_call_id"]
                logger.debug(f"Tool 호출 감지 (횟수: {tool_call_count + 1}): {func_name}")
                logger.debug(f"Tool 호출 인자: {func_args}")
                
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
                        
                        # Tool 호출 횟수 증가
                        tool_call_count += 1
                        
                    except Exception as e:
                        logger.error(f"🧠 로컬 함수 실행 오류: {e}")
                        tool_result = f"Tool 실행 중 오류가 발생했습니다: {e}"
                        tool_results.append({
                            'tool_call_id': tool_call_id,
                            'name': func_name,
                            'content': json.dumps({"error": str(e)}, ensure_ascii=False)
                        })
                        
                        # Tool 호출 횟수 증가
                        tool_call_count += 1
                else:
                    logger.error(f"🧠 알 수 없는 도구 호출: {func_name}")
                    # 알 수 없는 도구 호출도 횟수에 포함
                    tool_call_count += 1
        
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

## 🚨 매우 중요한 규칙
**절대로 도구를 사용하지 않고 SQL을 생성하지 마세요!**
**반드시 다음 순서를 따라야 합니다:**

## 지시사항
1.  **사고(Thinking) 단계:** 먼저 사용자의 질문을 분석하여 어떤 정보가 필요한지 계획을 세웁니다.
2.  **도구 사용(Tool Use) 단계:** 계획에 따라 필요한 도구를 반드시 사용해야 합니다.
    - **1순위:** `get_table_list()`를 반드시 호출하여 테이블 목록을 파악합니다.
    - **2순위:** 질문과 관련성이 높은 데이터베이스 테이블 들을 추론합니다. 
    - **3순위:** 해당 테이블들에 대해서는 모두두 `get_table_schema("table_name")`를 호출(필수)하여 테이블 구조를 파악합니다. table_name은 반드시 영문으로 전달합닏다다.
    - **4순위:** 모든 정보가 수집되었다고 판단되면, SQL을 생성합니다.
3.  **최종 답변(Final Answer) 단계:**
    - 모든 정보 수집이 완료되면, 분석한 내용을 바탕으로 **순수한 SQL 쿼리 하나만** 생성합니다.
    - <think> ~~ </think>와 같은 사고 과정의 내용은 절대 포함하지 마세요.
    - 마크다운(```), 설명, 주석 없이 오직 SQL 쿼리만 반환해야 합니다.
    - SQL 쿼리는 반드시 세미콜론(;)으로 끝나야 합니다.
    - 최종 답변은 반드시 순수한 SQL 쿼리만 반환해야 합니다.

## ⚠️ 금지사항
- 도구를 사용하지 않고 바로 SQL을 생성하는 것은 절대 금지
- 테이블 목록을 확인하지 않고 SQL을 생성하는 것은 절대 금지
- 존재하지 않는 테이블이나 컬럼을 사용하는 것은 절대 금지
- 스키마 정보 없이 SQL을 생성하는 것은 절대 금지


## 📝 올바른 사용 예시
**올바른 순서:**
1. `get_table_list()` 호출 → 테이블 목록 확인
2. 관련 테이블들에 대해서 모두 `get_table_schema("table_name")` 호출(테이블 수만큼 반복) → 각 테이블들의 구조 확인
3. SQL 쿼리 생성

**잘못된 순서 (절대 금지):**
- 바로 SQL 쿼리 생성 ❌
- 테이블 목록 확인 없이 SQL 생성 ❌
- 스키마 정보 없이 SQL 생성 ❌
"""
    
    basic_rule_prompt = """
⚠️ 매우 중요한 규칙:
**1. "따옴표(Quote) 내용 절대 보존 원칙"**
  - 작은따옴표(' ') 또는 큰따옴표(" ")로 감싸인 모든 단어나 문장은 **어떠한 경우에도 번역하거나 변형하지 마세요.**
  - 주어진 그대로, 문자 그대로(as-is, literal) 출력에 포함시켜야 합니다. 이는 주로 SQL의 값(value)이나 특정 식별자에 해당합니다.
 ✅ **올바른 예시:**
  - 입력: '노트북'을 구매한 사용자 검색
  - SQL: `WHERE product_name = '노트북'`

  - 입력: 사용자가 'Laptop'을 구매했을 때
  - SQL: `WHERE product_name = 'Laptop'`

 ❌ **잘못된 예시:**
  - 입력: '노트북'을 구매한 사용자 검색
  - SQL: `WHERE product_name = 'notebook'` (오역)
**2. "영어 단어 및 기술 용어 보존 원칙"**
  - 따옴표가 없더라도, 영어로 된 기술 용어, 제품명, 고유명사는 한국어로 번역하지 말고 원문 그대로 사용하세요.
  - 예: `Database`, `Table`, `Primary Key`, `SELECT` 등
**3. 최종 답변은 반드시 순수한 SQL 쿼리만 반환해야 합니다.
**4. SQL 쿼리 1개만 반환하세요
**5. 마크다운 형식(```)을 절대 사용하지 마세요
**6. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
**7. 세미콜론(;)으로 끝내세요
**8. 질문이 모호하거나 문장구성이 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
  - 예시: 'afdksafdsalfj', 'ㅁ렁ㄴ123ㅓ  마ㅣㄹaaghgl'등.
**9. ID는 시스템에게만 의미있는 값이므로 ID보다는 이름(명) 필드를 SQL의 조회 필드로 사용하세요.
  - 예시: user_id 보다는 user_name 필드를 조회 필드로 사용하세요.
  - ID가 사용자 질의에 '~id', '~번호' 등으로 표시되어 있는 경우에만 필드로 사용하세요.
**10.. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가
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
- get_table_list()
- get_table_schema("table_name")

=== 🚨 tool 사용 순서 (절대적으로 필수): ===
🚨 첫 번째 단계: 반드시 get_table_list()를 호출하여 사용 가능한 테이블 목록을 확인하세요
🚨 두 번째 단계: 질문과 가장 관련성이 높은 테이블 1~3개를 추론하고 
🚨 세 번째 단계: 추론한 테이블들에 대해서 테이블의 스키마를 get_table_schema("테이블명")로 조회하세요
🚨 네 번째 단계: 스키마 정보를 확인한 후에만 SQL 쿼리를 생성하세요

🚫 절대 금지사항:
- 테이블 목록을 확인(get_table_list)하지 않고 SQL을 생성하지 마세요
- 존재하지 않는 테이블 이름을 사용하지 마세요
- 존재하지 않는 컬럼 이름을 사용하지 마세요
- 스키마 정보 없이 SQL을 생성하지 마세요
- 도구를 사용하지 않고 바로 SQL을 생성하지 마세요
"""
    
    close_prompt = """

=== 질문 ===\n{question}

"""

    if use_tools:
        temp_prompt = default_prompt_with_tools +basic_rule_prompt+ use_tools_prompt + close_prompt
        prompt = temp_prompt.format(
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
        
