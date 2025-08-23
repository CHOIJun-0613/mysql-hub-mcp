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

def setup_logging_immediate():
    """모듈 임포트 시점에 즉시 로깅을 설정합니다."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # 로그 디렉토리 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로그 파일명 (날짜 포함)
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    log_filename = f"logs/server-{today}.log"
    
    # 로깅 설정
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename, encoding='utf-8')
        ]
    )

# 즉시 로깅 설정 실행
setup_logging_immediate()

class Config:
    """설정 클래스"""
    
    # 데이터베이스 타입 선택 (mysql, postgresql, oracle)
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "mysql").lower()
    
    # MySQL 설정
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "")
    
    # PostgreSQL 설정
    POSTGRESQL_HOST: str = os.getenv("POSTGRESQL_HOST", "localhost")
    POSTGRESQL_PORT: int = int(os.getenv("POSTGRESQL_PORT", "5432"))
    POSTGRESQL_USER: str = os.getenv("POSTGRESQL_USER", "postgres")
    POSTGRESQL_PASSWORD: str = os.getenv("POSTGRESQL_PASSWORD", "")
    POSTGRESQL_DATABASE: str = os.getenv("POSTGRESQL_DATABASE", "")
    
    # Oracle 설정
    ORACLE_HOST: str = os.getenv("ORACLE_HOST", "localhost")
    ORACLE_PORT: int = int(os.getenv("ORACLE_PORT", "1521"))
    ORACLE_USER: str = os.getenv("ORACLE_USER", "system")
    ORACLE_PASSWORD: str = os.getenv("ORACLE_PASSWORD", "")
    ORACLE_SERVICE_NAME: str = os.getenv("ORACLE_SERVICE_NAME", "XE")
    ORACLE_SID: str = os.getenv("ORACLE_SID", "")
    
    # AI Provider 설정 (groq, ollama, lmstudio)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")
    
    # LLM Tool 사용 설정
    USE_LLM_TOOLS: bool = os.getenv("USE_LLM_TOOLS", "true").lower() == "true"
    
    # Groq 설정
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    # LM Studio 설정
    LMSTUDIO_BASE_URL: str = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    LMSTUDIO_MODEL: str = os.getenv("LMSTUDIO_MODEL", "qwen/qwen3-8b")
    
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
    def get_database_url(cls) -> str:
        """현재 설정된 데이터베이스 타입에 따른 연결 URL을 반환합니다."""
        if cls.DATABASE_TYPE == "mysql":
            return cls.get_mysql_url()
        elif cls.DATABASE_TYPE == "postgresql":
            return cls.get_postgresql_url()
        elif cls.DATABASE_TYPE == "oracle":
            return cls.get_oracle_url()
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 타입: {cls.DATABASE_TYPE}")
    
    @classmethod
    def get_mysql_url(cls) -> str:
        """MySQL 연결 URL을 반환합니다."""
        charset_params = "charset=utf8mb4&use_unicode=1"
        return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}?{charset_params}"
    
    @classmethod
    def get_postgresql_url(cls) -> str:
        """PostgreSQL 연결 URL을 반환합니다."""
        return f"postgresql://{cls.POSTGRESQL_USER}:{cls.POSTGRESQL_PASSWORD}@{cls.POSTGRESQL_HOST}:{cls.POSTGRESQL_PORT}/{cls.POSTGRESQL_DATABASE}"
    
    @classmethod
    def get_oracle_url(cls) -> str:
        """Oracle 연결 URL을 반환합니다."""
        if cls.ORACLE_SID:
            return f"oracle+cx_oracle://{cls.ORACLE_USER}:{cls.ORACLE_PASSWORD}@{cls.ORACLE_HOST}:{cls.ORACLE_PORT}/{cls.ORACLE_SID}"
        else:
            return f"oracle+cx_oracle://{cls.ORACLE_USER}:{cls.ORACLE_PASSWORD}@{cls.ORACLE_HOST}:{cls.ORACLE_PORT}/?service_name={cls.ORACLE_SERVICE_NAME}"
    
    @classmethod
    def get_current_database_name(cls) -> str:
        """현재 설정된 데이터베이스의 이름을 반환합니다."""
        if cls.DATABASE_TYPE == "mysql":
            return cls.MYSQL_DATABASE
        elif cls.DATABASE_TYPE == "postgresql":
            return cls.POSTGRESQL_DATABASE
        elif cls.DATABASE_TYPE == "oracle":
            return cls.ORACLE_SERVICE_NAME or cls.ORACLE_SID
        else:
            return ""
    
    @classmethod
    def setup_logging(cls):
        """로깅 설정을 초기화합니다. (기존 호환성을 위해 유지)"""
        # 이미 설정되어 있으므로 아무것도 하지 않음
        pass

# 전역 설정 인스턴스
config = Config() 