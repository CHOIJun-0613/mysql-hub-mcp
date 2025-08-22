"""
AI Provider별 LLM 관리 모듈
각 AI Provider에 맞는 LLM 설정과 연결을 관리합니다.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

# Google ADK 모델들
try:
    from google.adk.models.google_llm import GoogleLlm
except ImportError:
    # GoogleLlm이 없는 경우 문자열로 대체
    GoogleLlm = str

try:
    from google.adk.models.lite_llm import LiteLlm
except ImportError:
    # LiteLlm이 없는 경우 문자열로 대체
    LiteLlm = str

# AI 설정
try:
    from ai_config import ai_config
except ImportError:
    # 상대 import 시도
    try:
        from .ai_config import ai_config
    except ImportError:
        # 절대 경로 import 시도
        from ai_config import ai_config

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    """AI Provider 기본 클래스"""
    
    @abstractmethod
    def create_llm(self) -> Any:
        """LLM 인스턴스를 생성합니다."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Provider가 사용 가능한지 확인합니다."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """모델명을 반환합니다."""
        pass

class GoogleAIProvider(BaseAIProvider):
    """Google Gemini AI Provider"""
    
    def __init__(self):
        self.api_key = ai_config.google_api_key
        self.model_name = ai_config.gemini_model_name
    
    def create_llm(self) -> GoogleLlm:
        """Google Gemini LLM을 생성합니다."""
        if not self.is_available():
            raise ValueError("Google API 키가 설정되지 않았습니다.")
        
        # 환경변수 설정 (GoogleLlm이 자동으로 읽음)
        os.environ["GOOGLE_API_KEY"] = self.api_key
        
        return GoogleLlm(
            model_name=self.model_name,
            temperature=0.1
        )
    
    def is_available(self) -> bool:
        """Google Gemini가 사용 가능한지 확인합니다."""
        return self.api_key is not None
    
    def get_model_name(self) -> str:
        """모델명을 반환합니다."""
        return self.model_name

class GroqAIProvider(BaseAIProvider):
    """Groq AI Provider"""
    
    def __init__(self):
        self.api_key = ai_config.groq_api_key
        self.model_name = ai_config.groq_model_name
    
    def create_llm(self) -> LiteLlm:
        """Groq LLM을 생성합니다."""
        if not self.is_available():
            raise ValueError("Groq API 키가 설정되지 않았습니다.")
        
        # LiteLlm을 통해 Groq 연결
        return LiteLlm(
            model=f"groq/{self.model_name}",
            api_key=self.api_key,
            temperature=0.1
        )
    
    def is_available(self) -> bool:
        """Groq가 사용 가능한지 확인합니다."""
        return self.api_key is not None
    
    def get_model_name(self) -> str:
        """모델명을 반환합니다."""
        return self.model_name

class LMStudioAIProvider(BaseAIProvider):
    """LM Studio AI Provider"""
    
    def __init__(self):
        self.base_url = ai_config.lmstudio_base_url
        self.model_name = ai_config.lmstudio_qwen_model_name
    
    def create_llm(self) -> LiteLlm:
        """LM Studio LLM을 생성합니다."""
        if not self.is_available():
            raise ValueError("LM Studio가 설정되지 않았습니다.")
        
        # LiteLlm을 통해 LM Studio 연결
        return LiteLlm(
            model=self.model_name,
            base_url=self.base_url,
            temperature=0.1
        )
    
    def is_available(self) -> bool:
        """LM Studio가 사용 가능한지 확인합니다."""
        # LM Studio는 로컬에서 실행되므로 항상 사용 가능하다고 가정
        return True
    
    def get_model_name(self) -> str:
        """모델명을 반환합니다."""
        return self.model_name

class AIProviderManager:
    """AI Provider 관리자"""
    
    def __init__(self):
        self.providers = {
            "google": GoogleAIProvider(),
            "groq": GroqAIProvider(),
            "lmstudio": LMStudioAIProvider()
        }
        self.current_provider_name = ai_config.get_current_provider()
    
    def get_current_provider(self) -> BaseAIProvider:
        """현재 설정된 Provider를 반환합니다."""
        provider = self.providers.get(self.current_provider_name)
        if not provider:
            logger.warning(f"알 수 없는 AI Provider: {self.current_provider_name}, Google로 기본 설정")
            return self.providers["google"]
        return provider
    
    def create_llm(self):
        """현재 Provider에 맞는 LLM을 생성합니다."""
        provider = self.get_current_provider()
        
        if not provider.is_available():
            logger.warning(f"현재 Provider '{self.current_provider_name}'가 사용 불가능합니다.")
            # Google으로 폴백
            fallback_provider = self.providers["google"]
            if fallback_provider.is_available():
                logger.info("Google Gemini로 폴백합니다.")
                return fallback_provider.create_llm()
            else:
                raise ValueError("사용 가능한 AI Provider가 없습니다.")
        
        logger.info(f"AI Provider '{self.current_provider_name}' 사용, 모델: {provider.get_model_name()}")
        return provider.create_llm()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """현재 Provider 정보를 반환합니다."""
        provider = self.get_current_provider()
        return {
            "provider": self.current_provider_name,
            "model": provider.get_model_name(),
            "available": provider.is_available()
        }

# 전역 AI Provider Manager 인스턴스
ai_provider_manager = AIProviderManager()
