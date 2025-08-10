"""
MCP(Model Context Protocol) 서버 모듈
MCP 프로토콜을 구현하여 클라이언트와 통신합니다.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
)

from database import db_manager
from ai_provider import ai_manager
from config import config

logger = logging.getLogger(__name__)

class MySQLMCPServer:
    """MySQL MCP 서버"""
    
    def __init__(self):
        self.server = Server("mysql-hub-mcp")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """MCP 핸들러들을 설정합니다."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록을 반환합니다."""
            tools = [
                Tool(
                    name="execute_sql",
                    description="MySQL 데이터베이스에서 SQL 쿼리를 실행합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "실행할 SQL 쿼리"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="natural_language_query",
                    description="자연어를 SQL 쿼리로 변환하여 실행합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "자연어로 된 질문"
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="get_database_info",
                    description="데이터베이스 정보와 테이블 목록을 반환합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_table_list",
                    description="데이터베이스의 모든 테이블 목록을 반환합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_table_schema",
                    description="특정 테이블의 스키마 정보를 반환합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "테이블 이름"
                            }
                        },
                        "required": ["table_name"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """도구 호출을 처리합니다."""
            try:
                if name == "execute_sql":
                    return await self._execute_sql(arguments)
                elif name == "natural_language_query":
                    return await self._natural_language_query(arguments)
                elif name == "get_database_info":
                    return await self._get_database_info(arguments)
                elif name == "get_table_list":
                    return await self._get_table_list(arguments)
                elif name == "get_table_schema":
                    return await self._get_table_schema(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"알 수 없는 도구: {name}")]
                    )
            except Exception as e:
                logger.error(f"도구 실행 중 오류: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"오류가 발생했습니다: {e}")]
                )
    
    async def _execute_sql(self, arguments: Dict[str, Any]) -> CallToolResult:
        """SQL 쿼리를 실행합니다."""
        query = arguments.get("query", "")
        
        if not query:
            return CallToolResult(
                content=[TextContent(type="text", text="SQL 쿼리가 제공되지 않았습니다.")]
            )
        
        try:
            # 쿼리 유효성 검사
            if not db_manager.validate_query(query):
                return CallToolResult(
                    content=[TextContent(type="text", text="잘못된 SQL 쿼리입니다.")]
                )
            
            # 쿼리 실행
            if query.strip().upper().startswith('SELECT'):
                result = db_manager.execute_query(query)
                result_text = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                affected_rows = db_manager.execute_non_query(query)
                result_text = f"쿼리가 성공적으로 실행되었습니다. 영향받은 행: {affected_rows}개"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"SQL 실행 중 오류: {e}")]
            )
    
    async def _natural_language_query(self, arguments: Dict[str, Any]) -> CallToolResult:
        """자연어를 SQL로 변환하여 실행합니다."""
        question = arguments.get("question", "")
        
        if not question:
            return CallToolResult(
                content=[TextContent(type="text", text="질문이 제공되지 않았습니다.")]
            )
        
        try:
            # 환경변수에 따라 처리 방식 결정
            if config.USE_LLM_TOOLS:
                # Tool 사용 방식
                return await self._natural_language_query_with_tools(question)
            else:
                # 기존 방식 - system prompt에 스키마 정보 포함
                return await self._natural_language_query_legacy(question)
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"자연어 쿼리 처리 중 오류: {e}")]
            )
    
    async def _natural_language_query_with_tools(self, question: str) -> CallToolResult:
        """Tool을 사용하여 자연어를 SQL로 변환합니다."""
        # Tool 정의
        tools = [
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
        
        # 메시지 히스토리 초기화
        messages = [
            {
                "role": "system",
                "content": """당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다.
필요한 정보가 부족하면 제공된 도구를 사용하여 데이터베이스 스키마를 파악한 후,
최종적으로 실행 가능한 SELECT SQL 쿼리만 생성해야 합니다.

⚠️ 매우 중요한 규칙:
1. 순수한 SQL 쿼리만 반환하세요
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요
6. 질문이 모호하거나 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
7. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가

도구 사용 순서:
1. 먼저 get_database_info() 또는 get_table_list()를 호출하여 사용 가능한 테이블 목록을 확인하세요
2. 필요한 테이블의 스키마를 get_table_schema()로 조회하세요
3. 스키마 정보를 바탕으로 SQL 쿼리를 생성하세요"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        # Tool 호출 루프
        max_iterations = 5
        for iteration in range(max_iterations):
            # AI 응답 생성
            response = await ai_manager.generate_response_with_tools(messages, tools)
            
            if "error" in response:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"AI 응답 생성 실패: {response['error']}")]
                )
            
            # AI 응답을 메시지 히스토리에 추가
            messages.append(response)
            
            # Tool 호출이 있는지 확인
            if "tool_calls" not in response:
                # Tool 호출이 없으면 최종 SQL 응답
                sql_query = response.get("content", "")
                
                # SQL 쿼리 실행
                if sql_query and not sql_query.startswith("응답 생성 중 오류"):
                    try:
                        result = db_manager.execute_query(sql_query)
                        result_text = f"생성된 SQL: {sql_query}\n\n결과:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                    except Exception as e:
                        result_text = f"생성된 SQL: {sql_query}\n\n실행 오류: {e}"
                else:
                    result_text = f"SQL 생성 실패: {sql_query}"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
            
            # Tool 호출 처리
            tool_calls = response["tool_calls"]
            logger.info(f"Tool 호출 감지: {[tc['function']['name'] for tc in tool_calls]}")
            
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = tool_call["function"]["arguments"]
                
                # Tool 실행
                if func_name == "get_database_info":
                    db_info = db_manager.get_database_info()
                    tool_result = json.dumps(db_info, ensure_ascii=False, indent=2)
                elif func_name == "get_table_list":
                    table_list = db_manager.get_table_list()
                    tool_result = json.dumps(table_list, ensure_ascii=False, indent=2)
                elif func_name == "get_table_schema":
                    table_name = func_args.get("table_name", "")
                    if table_name:
                        schema = db_manager.get_table_schema(table_name)
                        tool_result = json.dumps(schema, ensure_ascii=False, indent=2)
                    else:
                        tool_result = json.dumps({"error": "테이블 이름이 제공되지 않았습니다."})
                else:
                    tool_result = json.dumps({"error": f"알 수 없는 도구: {func_name}"})
                
                # Tool 결과를 메시지 히스토리에 추가
                messages.append({
                    "role": "tool",
                    "content": tool_result,
                    "tool_call_id": tool_call["id"]
                })
        
        # 최대 반복 횟수 초과
        return CallToolResult(
            content=[TextContent(type="text", text="Tool 호출이 너무 많습니다. 질문을 다시 확인해 주세요.")]
        )
    
    async def _natural_language_query_legacy(self, question: str) -> CallToolResult:
        """기존 방식으로 자연어를 SQL로 변환합니다 (system prompt에 스키마 정보 포함)."""
        try:
            # 데이터베이스 정보와 테이블 스키마를 가져와서 system prompt에 포함
            db_info = db_manager.get_database_info()
            tables_info = db_info.get("tables", [])
            
            # 스키마 정보 구성
            schema_info = "데이터베이스 스키마 정보:\n"
            for table in tables_info:
                table_name = table.get("name", "")
                if table_name:
                    schema = db_manager.get_table_schema(table_name)
                    schema_info += f"\n테이블: {table_name}\n"
                    schema_info += f"컬럼: {json.dumps(schema.get('columns', []), ensure_ascii=False, indent=2)}\n"
            
            # AI 응답 생성 (기존 방식)
            prompt = f"{schema_info}\n\n질문: {question}"
            sql_query = await ai_manager.generate_response(prompt)
            
            # SQL 쿼리 실행
            if sql_query and not sql_query.startswith("응답 생성 중 오류"):
                try:
                    result = db_manager.execute_query(sql_query)
                    result_text = f"생성된 SQL: {sql_query}\n\n결과:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                except Exception as e:
                    result_text = f"생성된 SQL: {sql_query}\n\n실행 오류: {e}"
            else:
                result_text = f"SQL 생성 실패: {sql_query}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"기존 방식 처리 중 오류: {e}")]
            )
    
    async def _get_database_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """데이터베이스 정보를 반환합니다."""
        try:
            db_info = db_manager.get_database_info()
            info_text = json.dumps(db_info, ensure_ascii=False, indent=2)
            return CallToolResult(
                content=[TextContent(type="text", text=info_text)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"데이터베이스 정보 조회 중 오류: {e}")]
            )
    
    async def _get_table_list(self, arguments: Dict[str, Any]) -> CallToolResult:
        """테이블 목록을 반환합니다."""
        try:
            table_list = db_manager.get_table_list()
            list_text = json.dumps(table_list, ensure_ascii=False, indent=2)
            return CallToolResult(
                content=[TextContent(type="text", text=list_text)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"테이블 목록 조회 중 오류: {e}")]
            )
    
    async def _get_table_schema(self, arguments: Dict[str, Any]) -> CallToolResult:
        """테이블 스키마를 반환합니다."""
        table_name = arguments.get("table_name", "")
        
        if not table_name:
            return CallToolResult(
                content=[TextContent(type="text", text="테이블 이름이 제공되지 않았습니다.")]
            )
        
        try:
            schema = db_manager.get_table_schema(table_name)
            schema_text = json.dumps(schema, ensure_ascii=False, indent=2)
            return CallToolResult(
                content=[TextContent(type="text", text=schema_text)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"테이블 스키마 조회 중 오류: {e}")]
            )
    
    async def run(self):
        """MCP 서버를 실행합니다."""
        async with stdio_server() as (read_stream, write_stream):
            # capabilities를 직접 구성
            capabilities = {
                "tools": {}
            }
            
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mysql-hub-mcp",
                    server_version="0.1.0",
                    capabilities=capabilities,
                ),
            )

# 전역 MCP 서버 인스턴스
mcp_server = MySQLMCPServer() 