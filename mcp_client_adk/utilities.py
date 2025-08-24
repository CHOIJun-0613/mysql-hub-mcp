# utilities.py
# 유틸리티 함수들을 포함하는 모듈
import os
import json
import sys
import logging
from rich import print as rprint
from rich.syntax import Syntax
from dotenv import load_dotenv

# 환경 변수 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)
logger = logging.getLogger(__name__)

def read_config_json():
    """
    MCP 서버 설정 파일을 읽어서 반환합니다.
    
    Returns:
        dict: MCP 서버 설정 정보
        
    Raises:
        SystemExit: 설정 파일을 읽을 수 없는 경우
    """
    # 환경 변수에서 설정 파일 경로를 가져오거나 기본값 사용
    config_path = os.getenv("MCP_CONFIG_PATH") or os.path.join(os.path.dirname(__file__), "mcp_server_config.json")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"설정 파일 JSON 파싱 오류: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"설정 파일 읽기 실패: {e}")
        sys.exit(1)

def print_json_response(response, title: str):
    """
    응답 객체를 JSON 형태로 예쁘게 출력합니다.
    
    Args:
        response: 출력할 응답 객체
        title (str): 출력 제목
    """
    print(f"\n=== {title} ===")
    try:
        # 응답 객체의 구조에 따라 데이터 추출
        if hasattr(response, "root"):
            data = response.root.model_dump(mode="json", exclude_none=True)
        else:
            data = response.model_dump(mode="json", exclude_none=True)
        
        # JSON을 예쁘게 포맷팅하여 출력
        syntax = Syntax(
            json.dumps(data, indent=2, ensure_ascii=False), 
            "json", 
            theme="monokai", 
            line_numbers=False
        )
        rprint(syntax)
    except Exception as e:
        rprint(f"[red bold]JSON 출력 오류:[/red bold] {e}")
        rprint(repr(response))