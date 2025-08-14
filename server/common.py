from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

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

