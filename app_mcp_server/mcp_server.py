"""
MCP(Model Context Protocol) 서버 모듈
MCP 프로토콜을 구현하여 클라이언트와 통신합니다.
SSE(Server-Sent Events) 방식으로 HTTP 서버를 제공합니다.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from database import db_manager
from ai_provider import ai_manager
from ai_worker import natural_language_query_work,make_system_prompt, strip_markdown_sql
from config import config
from common import clear_screen, init_environment, json_to_pretty_string, convert_for_json_serialization

from rag_integration import get_tables_from_rag, get_schema_from_rag

logger = logging.getLogger(__name__)
host = config.MCP_SERVER_HOST
port = config.MCP_SERVER_PORT

# 전역 변수로 서버 인스턴스 저장
mcp_server = None

mcp = FastMCP(
    "mysql-hub-mcp-server",
    "0.1.0",
    host=host,
    port=port,
    mount_path = "/",
    message_path= "/messages/",
    streamable_http_path= "/mcp",
    stateless_http=True,
    log_level="WARNING"
)

def signal_handler(signum, frame):
    """시그널 핸들러: Ctrl+C 등의 시그널을 처리합니다."""
    logger.info(f"시그널 {signum}을 받았습니다. 서버를 안전하게 종료합니다...")
    
    # 데이터베이스 연결 정리
    try:
        if hasattr(db_manager, 'close_connection'):
            db_manager.close_connection()
            logger.info("데이터베이스 연결이 정리되었습니다.")
    except Exception as e:
        logger.warning(f"데이터베이스 연결 정리 중 오류: {e}")
    
    # AI 매니저 정리
    try:
        if hasattr(ai_manager, 'cleanup'):
            ai_manager.cleanup()
            logger.info("AI 매니저가 정리되었습니다.")
    except Exception as e:
        logger.warning(f"AI 매니저 정리 중 오류: {e}")
    
    logger.info("\n\n🚨=====[MCP] 서버가 안전하게 종료되었습니다.\n\n")
    sys.exit(0)

@mcp.tool(description="데이터베이스 정보를 조회한다.", title="데이터베이스 정보 조회")
async def get_database_info() -> Dict[str, Any]:
    """데이터베이스 정보를 반환합니다.
    
    Returns:
        Dict[str, Any]: 데이터베이스 정보 (연결 상태, 데이터베이스명, 테이블 수 등)
    """
    try:
        info = db_manager.get_database_info()
        # info를 정렬된 json 형태로 출력
        import json
        logger.info(f"🚨=====[MCP] 데이터베이스 정보 조회 결과:\n{json_to_pretty_string(info)}\n")
        return info
    except Exception as e:
        logger.error(f"🚨=====[MCP] 데이터베이스 정보 조회 실패: {e}")
        return {"error": str(e), "status": "failed"}
    
@mcp.tool(description="테이블 목록을 조회한다.", title="테이블 목록록 조회")
async def get_table_list() -> List[Dict[str, Any]]:
    """테이블 목록을 반환합니다.
    
    Returns:
        List[Dict[str, Any]]: 테이블 목록[{"table_name": "테이블 이름", "table_comment": "테이블 코멘트"}]
    """
    try:
        # 환경변수에 따라 DB 또는 RAG에서 조회
        if config.DATA_SOURCE == "RAG":
            tables = get_tables_from_rag()
            logger.info(f"🚨=====[MCP] RAG에서 테이블 목록 조회 결과: \n{json_to_pretty_string(tables)}\n")
        else:
            tables = db_manager.get_table_list()
            logger.info(f"🚨=====[MCP] DB에서 테이블 목록 조회 결과: \n{json_to_pretty_string(tables)}\n")
        
        return tables
    except Exception as e:
        logger.error(f"🚨=====[MCP] 테이블 목록 조회 실패: {e}")
        return []

@mcp.tool(description="테이블의 Schema 정보를 조회한다.", title="테이블 Schema 조회")
async def get_table_schema(table_name: str) -> Dict[str, Any]:
    """테이블 스키마를 반환합니다.
    
    Args:
        table_name (str): 테이블 이름
        
    Returns:
        Dict[str, Any]: 테이블 스키마 정보
    """
    try:
        # 환경변수에 따라 DB 또는 RAG에서 조회
        if config.DATA_SOURCE == "RAG":
            schema = get_schema_from_rag(table_name)
            logger.info(f"🚨=====[MCP] RAG에서 테이블 '{table_name}' 스키마 조회 결과: \n{json_to_pretty_string(schema)}\n")
        else:
            schema = db_manager.get_table_schema(table_name)
            logger.info(f"🚨=====[MCP] DB에서 테이블 '{table_name}' 스키마 조회 결과: \n{json_to_pretty_string(schema)}\n")
        
        return schema
    except Exception as e:
        logger.error(f"🚨=====[MCP] 테이블 '{table_name}' 스키마 조회 실패: {e}")
        return {"error": str(e)}

@mcp.tool(description="입력받은 SQL 쿼리를 실행합니다.", title="SQL 쿼리 실행")
async def execute_sql(sql: str) -> Dict[str, Any]:
    """SQL 쿼리를 실행합니다.
    
    Args:
        sql: 실행할 SQL 쿼리
        
    Returns:
        Dict[str, Any]: 쿼리 실행 결과 (데이터, 행 수, 실행 시간 등)
    """
    try:
        if not sql:
            raise ValueError("SQL 쿼리가 제공되지 않았습니다.")
        
        # 데이터베이스 매니저에서 SQL 실행 메서드 호출
        result = db_manager.execute_query(sql)
        
        # JSON 직렬화를 위해 데이터 타입 변환
        converted_result = convert_for_json_serialization(result)
        
        result = {"data": converted_result, "row_count": len(converted_result), "sql": sql, "status": "success"}
        logger.info(f"🚨=====[MCP] SQL 실행 결과: \n{json_to_pretty_string(result)}\n")
        return result
    except Exception as e:
        logger.error(f"🚨=====[MCP] SQL 실행 실패: {e}")
        return {"error": str(e), "status": "failed"}

@mcp.tool(description="사용자의 자연어 쿼리를 실행합니다.", title="자연어 쿼리 실행")
async def natural_language_query(question: str) -> Dict[str, Any]:
    """자연어로 데이터베이스 쿼리를 실행합니다.
    
    Args:
        question: 자연어로 된 쿼리 (예: "사용자 테이블에서 모든 데이터를 가져와줘")
        
    Returns:
        Dict[str, Any]: 쿼리 실행 결과
    """
    try:
        if not question:
            raise ValueError("사용자의 질의 내용이 제공되지 않았습니다.")
        
        if question.isdigit() or len(question.strip()) < 5:
            raise ValueError("질문 내용이 너무 짧거나 수자로만 되어 있어서 모호합니다.")

        response = await natural_language_query_work(question, False)
        
        # JSON 직렬화를 위해 데이터 타입 변환
        converted_data = convert_for_json_serialization(response.data)
        
        result = {"data": converted_data, "row_count": len(converted_data), "sql": converted_data.get("sql_query", ""), "status": "success"}
        logger.info(f"🚨=====[MCP] 자연어 쿼리 처리 결과 완료: \n{json_to_pretty_string(result)}\n")
        
        return result
    except Exception as e:
        logger.error(f"🚨=====[MCP] 자연어 쿼리 처리 실패: {e}")
        return {"error": str(e), "status": "failed"}

   
async def run_mcp_server():
    """MCP 서버를 실행합니다."""
    global mcp_server
    
    # stdout을 clear하고 시작
    #clear_screen()
    init_environment(db_manager, ai_manager)
    logger.info("MySQL Hub MCP 서버를 시작합니다...")
    logger.info(f"MCP 서버 호스트: {config.MCP_SERVER_HOST}")
    logger.info(f"MCP 서버 포트: {config.MCP_SERVER_PORT}")
    
    # Windows 환경에서 asyncio 이벤트 루프 정책 설정
    if sys.platform == "win32":
        try:
            import asyncio
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            logger.info("Windows 환경에 맞는 이벤트 루프 정책을 설정했습니다.")
            
            # Windows 환경에서 연결 오류를 무시하는 예외 핸들러 설정
            def handle_connection_error(loop, context):
                if isinstance(context.get('exception'), ConnectionResetError):
                    # ConnectionResetError는 무시 (일반적인 클라이언트 연결 끊김)
                    logger.debug(f"클라이언트 연결이 끊어졌습니다: {context.get('exception')}")
                else:
                    # 다른 예외는 로깅
                    logger.error(f"이벤트 루프 오류: {context}")
            
            # 현재 이벤트 루프에 예외 핸들러 설정
            try:
                loop = asyncio.get_event_loop()
                loop.set_exception_handler(handle_connection_error)
                logger.info("Windows 환경에 맞는 예외 핸들러를 설정했습니다.")
            except RuntimeError:
                # 이벤트 루프가 아직 생성되지 않은 경우
                pass
                
        except Exception as e:
            logger.warning(f"Windows 이벤트 루프 정책 설정 실패: {e}")
    
    # 종료 이벤트를 위한 asyncio.Event
    shutdown_event = asyncio.Event()
    
    # 시그널 핸들러를 비동기적으로 처리
    def signal_handler_async():
        logger.info("🚨=====[MCP] 종료 시그널을 받았습니다. 서버를 안전하게 종료합니다...")
        shutdown_event.set()
    
    # 시그널 핸들러 등록
    import signal
    signal.signal(signal.SIGINT, lambda signum, frame: signal_handler_async())
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, lambda signum, frame: signal_handler_async())
    
    try:
        # FastMCP의 run() 메서드를 별도 스레드에서 실행
        import concurrent.futures
        import threading
        
        def run_mcp_in_thread():
            try:
                # FastMCP 서버를 실행하되, 종료 시그널을 처리할 수 있도록 설정
                mcp.run("streamable-http")
            except KeyboardInterrupt:
                logger.info("MCP 서버 스레드에서 KeyboardInterrupt를 받았습니다.")
            except Exception as e:
                logger.error(f"MCP 서버 스레드에서 오류 발생: {e}")
        
        # 스레드 풀에서 MCP 서버 실행
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_mcp_in_thread)
            
            # 종료 이벤트 또는 완료 대기
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=None)
                logger.info("🚨=====[MCP] 종료 시그널을 받았습니다. MCP 서버를 중지합니다...")
                
                # future를 취소하여 MCP 서버 스레드 종료
                future.cancel()
                try:
                    # 더 짧은 타임아웃으로 먼저 시도
                    future.result(timeout=2)
                    logger.info("MCP 서버 스레드가 취소되었습니다.")
                except concurrent.futures.CancelledError:
                    logger.info("MCP 서버 스레드가 취소되었습니다.")
                except concurrent.futures.TimeoutError:
                    logger.warning("MCP 서버 스레드 종료 시간 초과, 강제 종료 시도...")
                    
                    # 강제 종료를 위해 executor를 종료
                    executor.shutdown(wait=False, cancel_futures=True)
                    logger.info("MCP 서버 executor가 강제 종료되었습니다.")
                    
                    # MCP_SERVER_PORT를 사용하는 프로세스를 직접 종료
                    try:
                        import subprocess
                        import platform
                        
                        if platform.system() == "Windows":
                            # Windows에서 MCP_SERVER_PORT를 사용하는 프로세스 찾기 및 종료
                            # netstat으로 포트를 사용하는 PID 찾기
                            result = subprocess.run(['netstat', '-aon'], capture_output=True, text=True)
                            lines = result.stdout.split('\n')
                            
                            for line in lines:
                                if f':{config.MCP_SERVER_PORT}' in line and 'LISTENING' in line:
                                    parts = line.split()
                                    if len(parts) >= 5:
                                        pid = parts[-1]
                                        try:
                                            # 해당 PID 프로세스 종료
                                            subprocess.run(['taskkill', '/f', '/pid', pid], capture_output=True)
                                            logger.info(f"Windows에서 PID {pid} 프로세스 강제 종료 완료")
                                        except Exception as e:
                                            logger.error(f"PID {pid} 프로세스 종료 실패: {e}")
                                        break
                        else:
                            # Linux/Mac에서 MCP_SERVER_PORT를 사용하는 프로세스 찾기 및 종료
                            cmd = f"lsof -ti:{config.MCP_SERVER_PORT} | xargs kill -9"
                            subprocess.run(cmd, shell=True, capture_output=True)
                            logger.info(f"Linux/Mac에서 포트 {config.MCP_SERVER_PORT} 프로세스 강제 종료 완료")
                            
                    except Exception as e:
                        logger.error(f"포트 {config.MCP_SERVER_PORT} 프로세스 강제 종료 실패: {e}")
                        
            except asyncio.TimeoutError:
                logger.info("MCP 서버가 정상적으로 완료되었습니다.")
            except Exception as e:
                logger.error(f"MCP 서버 실행 중 오류 발생: {e}")
                
    except KeyboardInterrupt:
        logger.info("🚨=====[MCP] Ctrl+C를 받았습니다. 서버를 종료합니다...")
    except asyncio.exceptions.CancelledError:
        logger.info("🚨=====[MCP] 서버 작업이 취소되었습니다. 정상적인 종료입니다.")
    except Exception as e:
        logger.error(f"🚨=====[MCP] 서버 실행 중 오류 발생: {e}")
    finally:
        # 정리 작업 수행
        _cleanup_resources()
        logger.info("🚨=====[MCP] 서버가 완전히 종료되었습니다.")


def _cleanup_resources():
    """리소스 정리 작업을 수행합니다."""
    logger.info("리소스 정리 작업을 시작합니다...")
    
    # 데이터베이스 연결 정리
    try:
        if hasattr(db_manager, 'close_connection'):
            db_manager.close_connection()
            logger.info("데이터베이스 연결이 정리되었습니다.")
    except Exception as e:
        logger.warning(f"데이터베이스 연결 정리 중 오류: {e}")
    
    # AI 매니저 정리
    try:
        if hasattr(ai_manager, 'cleanup'):
            ai_manager.cleanup()
            logger.info("AI 매니저가 정리되었습니다.")
    except Exception as e:
        logger.warning(f"AI 매니저 정리 중 오류: {e}")
    
    # 로깅 정리
    try:
        logging.shutdown()
        logger.info("로깅 시스템이 정리되었습니다.")
    except Exception as e:
        logger.warning(f"로깅 시스템 정리 중 오류: {e}")
    
    logger.info("모든 리소스 정리 작업이 완료되었습니다.")


if __name__ == "__main__":
    try:
        # Windows 환경에서 asyncio 이벤트 루프 정책 설정
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                
                # Windows 환경에서 연결 오류를 무시하는 예외 핸들러 설정
                def handle_connection_error(loop, context):
                    if isinstance(context.get('exception'), ConnectionResetError):
                        # ConnectionResetError는 무시 (일반적인 클라이언트 연결 끊김)
                        logger.debug(f"클라이언트 연결이 끊어졌습니다: {context.get('exception')}")
                    else:
                        # 다른 예외는 로깅
                        logger.error(f"이벤트 루프 오류: {context}")
                
                # asyncio.run() 실행 후 이벤트 루프에 예외 핸들러 설정
                def run_with_exception_handler():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.set_exception_handler(handle_connection_error)
                    return loop
                
                # 커스텀 이벤트 루프로 실행
                loop = run_with_exception_handler()
                try:
                    loop.run_until_complete(run_mcp_server())
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.warning(f"Windows 이벤트 루프 정책 설정 실패: {e}")
                # 기본 방식으로 실행
                asyncio.run(run_mcp_server())
        else:
            # Windows가 아닌 환경에서는 기본 방식으로 실행
            asyncio.run(run_mcp_server())
    except KeyboardInterrupt:
        logger.info("🚨=====[MCP] 메인 스레드에서 Ctrl+C를 받았습니다.")
        _cleanup_resources()
    except Exception as e:
        logger.error(f"🚨=====[MCP] 예상치 못한 오류 발생: {e}")
        _cleanup_resources()
        sys.exit(1)
