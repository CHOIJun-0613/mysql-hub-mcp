"""
HTTP 기반 MCP 클라이언트 애플리케이션
FastAPI 서버와 httpx로 통신합니다.
"""

import asyncio
import argparse
import sys
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import httpx

# 로깅 설정
def setup_logging():
    """클라이언트 로깅을 설정합니다."""
    # 로그 디렉토리 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로그 파일명 (날짜 포함)
    today = datetime.now().strftime("%Y%m%d")
    log_filename = f"logs/client-{today}.log"
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename, encoding='utf-8')  # UTF-8 인코딩 명시
        ]
    )
    
    # 외부 라이브러리의 로그 레벨 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

# 로깅 초기화
setup_logging()
logger = logging.getLogger(__name__)

console = Console()

class HTTPMCPClient:
    """
    HTTP MCP 클라이언트 클래스
    FastAPI 서버와 httpx로 통신하여 데이터베이스를 조작합니다.
    """
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url.rstrip("/")
        self.tools: List[Dict[str, Any]] = [
            {
                "name": "execute_sql",
                "description": "MySQL 데이터베이스에서 SQL 쿼리를 실행합니다.",
                "required": ["query"]
            },
            {
                "name": "natural_language_query",
                "description": "자연어를 SQL 쿼리로 변환하여 실행합니다.",
                "required": ["question"]
            },
            {
                "name": "get_database_info",
                "description": "데이터베이스 정보와 테이블 목록을 반환합니다.",
                "required": []
            },
            {
                "name": "get_table_schema",
                "description": "특정 테이블의 스키마 정보를 반환합니다.",
                "required": ["table_name"]
            },
        ]

    def display_tools(self):
        """사용 가능한 도구 목록을 표시합니다."""
        table = Table(title="사용 가능한 도구 목록")
        table.add_column("번호", style="bold magenta")
        table.add_column("도구명", style="cyan")
        table.add_column("설명", style="white")
        table.add_column("필수 매개변수", style="yellow")
        for i, tool in enumerate(self.tools, 1):
            table.add_row(str(i), tool["name"], tool["description"], ', '.join(tool["required"]))
        console.print(table)

    async def execute_sql(self, client: httpx.AsyncClient, query: str) -> str:
        """SQL 쿼리를 실행합니다."""
        logger.info(f"SQL 쿼리 실행 요청: {query[:100]}...")
        try:
            resp = await client.post(f"{self.server_url}/database/execute", json={"query": query})
            logger.info(f"SQL 쿼리 실행 완료: 상태 코드 {resp.status_code}")
            return self._format_response(resp)
        except Exception as e:
            logger.error(f"SQL 쿼리 실행 실패: {e}")
            raise

    async def natural_language_query(self, client: httpx.AsyncClient, question: str) -> str:
        """자연어 쿼리를 실행합니다."""
        logger.info(f"자연어 쿼리 요청: {question}")
        try:
            resp = await client.post(f"{self.server_url}/database/natural-query", json={"question": question})
            logger.info(f"자연어 쿼리 완료: 상태 코드 {resp.status_code}")
            return self._format_response(resp)
        except httpx.ConnectError as e:
            logger.error(f"서버 연결 실패: {e}")
            return Panel(f"서버 연결 실패: {e}", title="[red]연결 오류[/red]", border_style="red")
        except httpx.TimeoutException as e:
            logger.error(f"요청 시간 초과: {e}")
            return Panel(f"요청 시간 초과: {e}", title="[red]시간 초과[/red]", border_style="red")
        except Exception as e:
            logger.error(f"HTTP 요청 실패: {e}")
            return Panel(f"HTTP 요청 실패: {e}", title="[red]요청 오류[/red]", border_style="red")

    async def get_database_info(self, client: httpx.AsyncClient) -> str:
        """데이터베이스 정보를 조회합니다."""
        resp = await client.get(f"{self.server_url}/database/info")
        return self._format_response(resp)

    async def get_table_schema(self, client: httpx.AsyncClient, table_name: str) -> str:
        """테이블 스키마를 조회합니다."""
        resp = await client.post(f"{self.server_url}/database/table-schema", json={"table_name": table_name})
        return self._format_response(resp)

    def _format_response(self, resp: httpx.Response) -> str:
        """서버 응답을 보기 좋게 포맷합니다."""
        try:
            data = resp.json()
            
            # HTTPException 처리 (400, 500 등 에러 상태 코드)
            if resp.status_code >= 400:
                error_detail = data.get("detail", "알 수 없는 오류")
                return Panel(f"상태 코드: {resp.status_code}\n오류: {error_detail}", title="[red]HTTP 오류[/red]", border_style="red")
            
            # 정상 응답 처리
            if data.get("success"):
                return Panel(str(data.get("data")), title="[green]성공[/green]", border_style="green")
            else:
                return Panel(str(data.get("error")), title="[red]오류[/red]", border_style="red")
        except Exception as e:
            return Panel(f"응답 파싱 오류: {e}\n원본: {resp.text}\n상태 코드: {resp.status_code}", title="[red]파싱 오류[/red]", border_style="red")

    async def interactive_mode(self):
        """대화형 모드를 실행합니다."""
        console.print(Panel.fit(
            "MySQL Hub MCP 클라이언트 - HTTP 대화형 모드\n종료하려면 'quit' 또는 'exit'를 입력하세요.",
            title="[bold blue]환영합니다![/bold blue]"
        ))
        async with httpx.AsyncClient(timeout=60.0) as client:
            while True:
                try:
                    self.display_tools()
                    choice = Prompt.ask(
                        "\n[bold cyan]도구를 선택하세요[/bold cyan]",
                        choices=[str(i+1) for i in range(len(self.tools))] + ['quit', 'exit', 'q']
                    )
                    if choice in ['quit', 'exit', 'q']:
                        console.print("[yellow]클라이언트를 종료합니다.[/yellow]")
                        break
                    tool = self.tools[int(choice)-1]
                    arguments = {}
                    if tool["name"] == "execute_sql":
                        arguments["query"] = Prompt.ask("[bold]SQL 쿼리를 입력하세요[/bold]")
                        coro = self.execute_sql(client, arguments["query"])
                    elif tool["name"] == "natural_language_query":
                        arguments["question"] = Prompt.ask("[bold]자연어 질문을 입력하세요[/bold]")
                        coro = self.natural_language_query(client, arguments["question"])
                    elif tool["name"] == "get_database_info":
                        coro = self.get_database_info(client)
                    elif tool["name"] == "get_table_schema":
                        arguments["table_name"] = Prompt.ask("[bold]테이블 이름을 입력하세요[/bold]")
                        coro = self.get_table_schema(client, arguments["table_name"])
                    else:
                        console.print("[red]알 수 없는 도구입니다.[/red]")
                        continue
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                        task = progress.add_task("도구 실행 중...", total=None)
                        result = await coro
                        progress.update(task, completed=True)
                    console.print(result)
                except KeyboardInterrupt:
                    console.print("\n[yellow]클라이언트를 종료합니다.[/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]오류가 발생했습니다: {e}[/red]")

    async def batch_mode(self, tool_name: str, arguments: Dict[str, Any]):
        """배치 모드로 도구를 실행합니다."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            if tool_name == "execute_sql":
                result = await self.execute_sql(client, arguments["query"])
            elif tool_name == "natural_language_query":
                result = await self.natural_language_query(client, arguments["question"])
            elif tool_name == "get_database_info":
                result = await self.get_database_info(client)
            elif tool_name == "get_table_schema":
                result = await self.get_table_schema(client, arguments["table_name"])
            else:
                result = f"알 수 없는 도구: {tool_name}"
            console.print(result)

async def main():
    """메인 함수"""
    logger.info("MySQL Hub MCP HTTP 클라이언트를 시작합니다.")
    
    parser = argparse.ArgumentParser(description="MySQL Hub MCP HTTP Client")
    parser.add_argument("--tool", help="실행할 도구 이름")
    parser.add_argument("--query", help="SQL 쿼리 (execute_sql 도구와 함께 사용)")
    parser.add_argument("--question", help="자연어 질문 (natural_language_query 도구와 함께 사용)")
    parser.add_argument("--table", help="테이블 이름 (get_table_schema 도구와 함께 사용)")
    parser.add_argument("--list-tools", action="store_true", help="사용 가능한 도구 목록을 표시하고 종료")
    parser.add_argument("--server-url", default="http://localhost:8000", help="서버 URL (기본값: http://localhost:8000)")
    args = parser.parse_args()
    
    logger.info(f"서버 URL: {args.server_url}")
    client = HTTPMCPClient(server_url=args.server_url)
    
    try:
        if args.list_tools:
            logger.info("도구 목록을 표시합니다.")
            client.display_tools()
            return
        if args.tool:
            logger.info(f"배치 모드로 도구 실행: {args.tool}")
            arguments = {}
            if args.tool == "execute_sql":
                if not args.query:
                    console.print("[red]SQL 쿼리가 필요합니다. --query 옵션을 사용하세요.[/red]")
                    sys.exit(1)
                arguments["query"] = args.query
            elif args.tool == "natural_language_query":
                if not args.question:
                    console.print("[red]질문이 필요합니다. --question 옵션을 사용하세요.[/red]")
                    sys.exit(1)
                arguments["question"] = args.question
            elif args.tool == "get_table_schema":
                if not args.table:
                    console.print("[red]테이블 이름이 필요합니다. --table 옵션을 사용하세요.[/red]")
                    sys.exit(1)
                arguments["table_name"] = args.table
            elif args.tool == "get_database_info":
                pass
            else:
                console.print(f"[red]알 수 없는 도구: {args.tool}[/red]")
                sys.exit(1)
            await client.batch_mode(args.tool, arguments)
        else:
            logger.info("대화형 모드를 시작합니다.")
            await client.interactive_mode()
    except Exception as e:
        logger.error(f"클라이언트 실행 중 오류가 발생했습니다: {e}")
        console.print(f"[red]클라이언트 실행 중 오류가 발생했습니다: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 