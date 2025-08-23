"""
서버 메인 애플리케이션
HTTP 서버와 MCP 서버를 관리합니다.
"""

import asyncio
import logging
import argparse
import sys
from typing import Optional

from config import config
from database import db_manager
from ai_provider import ai_manager
from mcp_server import run_mcp_server
from http_server import run_http_server
from common import clear_screen, init_environment

#stdout을 clear하고 시작
clear_screen()

logger = logging.getLogger(__name__)


class ServerApp:
    """서버 애플리케이션 클래스"""
    
    def __init__(self):
        self.http_task: Optional[asyncio.Task] = None
        self.mcp_task: Optional[asyncio.Task] = None
    
    async def start_http_server(self):
        """HTTP 서버를 시작합니다."""
        try:

            await run_http_server()
        except Exception as e:
            logger.error(f"HTTP 서버 시작 실패: {e}")
            raise
    
    async def start_mcp_server(self):
        """MCP 서버를 시작합니다."""
        try:
            await run_mcp_server()
        except Exception as e:
            logger.error(f"MCP 서버 시작 실패: {e}")
            raise
    
    async def run_both_servers(self):
        """HTTP 서버와 MCP 서버를 동시에 실행합니다."""
        try:
            # 두 서버를 동시에 실행
            self.http_task = asyncio.create_task(self.start_http_server())
            self.mcp_task = asyncio.create_task(self.start_mcp_server())
            
            logger.info("HTTP 서버와 MCP 서버가 시작되었습니다.")
            logger.info(f"HTTP 서버: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
            logger.info("MCP 서버: stdio 통신 준비 완료")
            
            # 두 서버가 완료될 때까지 대기
            await asyncio.gather(self.http_task, self.mcp_task)
            
        except Exception as e:
            logger.error(f"서버 실행 중 오류: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def run_http_only(self):
        """HTTP 서버만 실행합니다."""
        try:
            logger.info("\n\n🚨===== MySQL Hub HTTP Server 시작 =====\n")
            logger.debug("HTTP 서버만 시작합니다.")
            
            await self.start_http_server()
        except Exception as e:
            logger.error(f"HTTP 서버 실행 중 오류: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def run_mcp_only(self):
        """MCP 서버만 실행합니다."""
        try:
            logger.info("\n\n🚨===== MySQL Hub MCP Server 시작 =====\n")
            logger.debug("MCP 서버만 시작합니다.")
            
            await self.start_mcp_server()
        except Exception as e:
            logger.error(f"MCP 서버 실행 중 오류: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """리소스를 정리합니다."""
        if self.http_task and not self.http_task.done():
            self.http_task.cancel()
        if self.mcp_task and not self.mcp_task.done():
            self.mcp_task.cancel()
        
        logger.info("서버가 종료되었습니다.")

def main():
    """메인 함수"""
   
    parser = argparse.ArgumentParser(description="MySQL Hub MCP Server")
    parser.add_argument(
        "--mode",
        choices=["both", "http", "mcp"],
        default="both",
        help="실행 모드 (기본값: both)"
    )
    parser.add_argument(
        "--config",
        help="설정 파일 경로"
    )
    
    args = parser.parse_args()
    
    try:
        # 로깅 설정
        #config.setup_logging()
        
        # 서버 애플리케이션 생성
        app = ServerApp()
        
        # 모드에 따라 서버 실행
        if args.mode == "both":
            asyncio.run(app.run_both_servers())
        elif args.mode == "http":
            asyncio.run(app.run_http_only())
        elif args.mode == "mcp":
            asyncio.run(app.run_mcp_only())
            

      
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 