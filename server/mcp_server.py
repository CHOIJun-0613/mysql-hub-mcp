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
            # 데이터베이스 스키마 정보 가져오기
            db_info = db_manager.get_database_info()
            if "error" in db_info:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"데이터베이스 연결 오류: {db_info['error']}")]
                )
            
            # AI에게 전달할 프롬프트 구성
            schema_info = ""
            # 모든 테이블의 스키마 정보를 포함하도록 수정
            for table_name in db_info.get("tables", []):
                try:
                    schema = db_manager.get_table_schema(table_name)
                    schema_info += f"\n테이블: {table_name}\n"
                    for col in schema:
                        schema_info += f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})\n"
                except Exception:
                    continue
            prompt = f"""
다음 데이터베이스 스키마를 참고하여 자연어 질문을 SQL 쿼리로 변환해주세요.
SQL은 가장 정확하다고 판단되는 쿼리 1개만 반환해주세요.
SQL 쿼리만 반환해주세요. 설명이나 코멘트는 포함하지 마세요.

데이터베이스: {db_info.get('database_name', 'unknown')}
스키마 정보:
{schema_info}

질문: {question}

"""
            
            # AI를 사용하여 SQL 생성
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
                content=[TextContent(type="text", text=f"자연어 쿼리 처리 중 오류: {e}")]
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