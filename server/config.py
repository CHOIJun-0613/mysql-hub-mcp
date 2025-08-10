"""
설정 관리 모듈
환경 변수와 설정값을 관리합니다.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """설정 클래스"""
    
    # MySQL 설정
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "")
    
    # AI Provider 설정
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq")
    
    # LLM Tool 사용 설정
    USE_LLM_TOOLS: bool = os.getenv("USE_LLM_TOOLS", "true").lower() == "true"
    
    # Groq 설정
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    # Ollama 설정
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # 서버 설정
    HTTP_SERVER_HOST: str = os.getenv("HTTP_SERVER_HOST", "localhost")
    HTTP_SERVER_PORT: int = int(os.getenv("HTTP_SERVER_PORT", "9000"))
   
    # MCP 서버 설정
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    @classmethod
    def get_mysql_url(cls) -> str:
        """MySQL 연결 URL을 반환합니다."""
        # UTF-8 인코딩 설정 추가
        charset_params = "charset=utf8mb4&use_unicode=1"
        return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}?{charset_params}"
    
    @classmethod
    def setup_logging(cls):
        """로깅 설정을 초기화합니다."""
        import os
        from datetime import datetime
        
        # 로그 디렉토리 생성
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 로그 파일명 (날짜 포함)
        today = datetime.now().strftime("%Y%m%d")
        log_filename = f"logs/server-{today}.log"
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=cls.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_filename, encoding='utf-8')  # UTF-8 인코딩 명시
            ]
        )
        
        # 외부 라이브러리의 로그 레벨 조정
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# 전역 설정 인스턴스
config = Config() 