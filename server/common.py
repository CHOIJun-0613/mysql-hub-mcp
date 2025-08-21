from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import os
import sys
#from database import db_manager
#from ai_provider import ai_manager
#from config import config   

logger = logging.getLogger(__name__)

# Pydantic 모델들
class SQLQueryRequest(BaseModel):
    query: str

class NaturalLanguageRequest(BaseModel):
    question: str

class TableSchemaRequest(BaseModel):
    table_name: str

class AIProviderRequest(BaseModel):
    provider: str = Field(..., description="AI Provider 이름", pattern="^(groq|ollama|google)$")

class Response(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    
    def model_dump(self, **kwargs):
        """UTF-8 인코딩 문제를 해결하기 위한 커스텀 model_dump"""
        try:
            return super().model_dump(**kwargs)
        except UnicodeDecodeError as e:
            # UTF-8 인코딩 오류 발생 시 데이터 정리
            logger.warning(f"UTF-8 인코딩 오류 발생, 데이터 정리 중: {e}")
            
            # 데이터 정리
            cleaned_data = self._clean_data(self.data)
            cleaned_error = self._clean_string(self.error) if self.error else None
            
            return {
                "success": self.success,
                "data": cleaned_data,
                "error": cleaned_error
            }
    
    def _clean_data(self, data):
        """데이터에서 UTF-8 문제가 있는 부분을 정리"""
        if isinstance(data, str):
            return self._clean_string(data)
        elif isinstance(data, dict):
            return {k: self._clean_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data(item) for item in data]
        else:
            return data
    
    def _clean_string(self, text):
        """문자열에서 UTF-8 문제가 있는 부분을 정리"""
        if not isinstance(text, str):
            return str(text)
        
        try:
            # UTF-8로 인코딩/디코딩하여 문제 있는 문자 제거
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            # 최후의 수단: ASCII로 변환
            return text.encode('ascii', errors='ignore').decode('ascii')

def clear_screen():
    """화면을 지우는 함수"""
    if os.name == 'nt':
        # Windows 환경이지만 Git Bash 등에서는 'clear'를 사용해야 함
        if 'MSYSTEM' in os.environ or 'MINGW64' in os.environ or 'MINGW32' in os.environ:
            os.system('clear')
        else:
            os.system('cls')
    else:
        os.system('clear')
        
def init_environment(db_manager, ai_manager):
    """어플리케이션 실행될 수 있도록 DB connection 생성 및 AI Provider 생성"""
    try:
        # 데이터베이스 연결 초기화
        db_manager.constructor()
        
        # AI Provider 초기화
        ai_manager.constructor()
        
        logger.info("환경 초기화가 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"환경 초기화 중 오류가 발생했습니다: {e}")
        raise


def convert_decimal_in_result(obj):
    """결과 데이터에서 Decimal 타입을 float로, date 타입을 문자열로 변환"""
    from decimal import Decimal
    import datetime
    
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_decimal_in_result(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_in_result(item) for item in obj]
    else:
        return obj


def check_init_environment(db_manager, args, ai_manager, config):
        # 데이터베이스 연결 확인
        if not db_manager.is_connected():
            logger.error("데이터베이스에 연결할 수 없습니다.")
            logger.error("환경 변수를 확인하거나 .env 파일을 설정해주세요.")
            sys.exit(1)
        
        logger.info("MySQL Hub Server를 시작합니다.")
        logger.info(f"실행 모드: {args}")
        logger.info(f"AI Provider: {ai_manager.get_current_provider()}")
        logger.info(f"HTTP 서버: http://{config.HTTP_SERVER_HOST}:{config.HTTP_SERVER_PORT}")
        logger.info(f"log level : {config.LOG_LEVEL}")

# json을 입력받아 json format에 맞게 string으로 변환해서 리턴하는 함수
def json_to_pretty_string(data):
    """
    json 객체를 예쁘게 포맷된 문자열로 변환하여 반환합니다.

    Args:
        data (dict or list): JSON 객체

    Returns:
        str: 예쁘게 포맷된 JSON 문자열
    """
    try:
        import json
        from decimal import Decimal
        
        def convert_decimal(obj):
            """Decimal 타입을 float로 변환하는 헬퍼 함수"""
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(item) for item in obj]
            else:
                return obj
        
        # Decimal 타입을 float로 변환
        converted_data = convert_decimal(data)
        
        return json.dumps(converted_data, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception as e:
        return f"JSON 변환 오류: {e}"
