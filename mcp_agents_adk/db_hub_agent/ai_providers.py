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
    from google.adk.models.google_llm import Gemini
    GOOGLE_LLM_AVAILABLE = True
except ImportError as e:
    # Gemini가 없는 경우 플래그로 관리
    Gemini = None
    GOOGLE_LLM_AVAILABLE = False

try:
    from google.adk.models.lite_llm import LiteLlm
    LITE_LLM_AVAILABLE = True
except ImportError as e:
    # LiteLlm이 없는 경우 플래그로 관리
    LiteLlm = None
    LITE_LLM_AVAILABLE = False

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

# import 상태 로깅
logger.info(f"Gemini 모듈 import 상태: {'성공' if GOOGLE_LLM_AVAILABLE else '실패'}")
logger.info(f"LiteLlm 모듈 import 상태: {'성공' if LITE_LLM_AVAILABLE else '실패'}")

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
    
    def create_llm(self):
        """Google Gemini LLM을 생성합니다."""
        if not self.is_available():
            raise ValueError("Google API 키가 설정되지 않았습니다.")
        
        if not GOOGLE_LLM_AVAILABLE:
            raise ImportError("Gemini 모듈을 사용할 수 없습니다. google-adk 패키지를 설치해주세요.")
        
        # 환경변수 설정 (Gemini이 자동으로 읽음)
        os.environ["GOOGLE_API_KEY"] = self.api_key
        
        return Gemini(
            model_name=self.model_name,
            temperature=0.1
        )
    
    def is_available(self) -> bool:
        """Google Gemini가 사용 가능한지 확인합니다."""
        logger.debug(f"GoogleAIProvider.is_available() - api_key: {self.api_key}, GOOGLE_LLM_AVAILABLE: {GOOGLE_LLM_AVAILABLE}")
        return self.api_key is not None and GOOGLE_LLM_AVAILABLE
    
    def get_model_name(self) -> str:
        """모델명을 반환합니다."""
        return self.model_name

class GroqAIProvider(BaseAIProvider):
    """Groq AI Provider"""
    
    def __init__(self):
        self.api_key = ai_config.groq_api_key
        self.model_name = ai_config.groq_model_name
    
    def create_llm(self):
        """Groq LLM을 생성합니다."""
        if not self.is_available():
            raise ValueError("Groq API 키가 설정되지 않았습니다.")
        
        if not LITE_LLM_AVAILABLE:
            raise ImportError("LiteLlm 모듈을 사용할 수 없습니다. lite-llm 패키지를 설치해주세요.")
        
        # LiteLlm을 통해 Groq 연결
        return LiteLlm(
            model=f"groq/{self.model_name}",
            api_key=self.api_key,
            temperature=0.1
        )
    
    def is_available(self) -> bool:
        """Groq가 사용 가능한지 확인합니다."""
        return self.api_key is not None and LITE_LLM_AVAILABLE
    
    def get_model_name(self) -> str:
        """모델명을 반환합니다."""
        return self.model_name

class LMStudioAIProvider(BaseAIProvider):
    """LM Studio AI Provider"""
    
    def __init__(self):
        self.base_url = ai_config.lmstudio_base_url
        self.model_name = ai_config.lmstudio_qwen_model_name
    
    def create_llm(self):
        """LM Studio LLM을 생성합니다."""
        if not self.is_available():
            raise ValueError("LM Studio가 설정되지 않았습니다.")
        
        if not LITE_LLM_AVAILABLE:
            raise ImportError("LiteLlm 모듈을 사용할 수 없습니다. lite-llm 패키지를 설치해주세요.")
        
        # LiteLlm을 통해 LM Studio 연결
        return LiteLlm(
            model=self.model_name,
            base_url=self.base_url,
            temperature=0.1
        )
    
    def is_available(self) -> bool:
        """LM Studio가 사용 가능한지 확인합니다."""
        return LITE_LLM_AVAILABLE
    
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
        logger.debug(f"현재 Provider: {self.current_provider_name}, provider 객체: {provider}")
        logger.debug(f"Provider 사용 가능 여부: {provider.is_available()}")
        
        try:
            if not provider.is_available():
                logger.warning(f"현재 Provider '{self.current_provider_name}'가 사용 불가능합니다.")
                # Google으로 폴백
                fallback_provider = self.providers["google"]
                logger.debug(f"폴백 Provider 사용 가능 여부: {fallback_provider.is_available()}")
                if fallback_provider.is_available():
                    logger.info("Google Gemini로 폴백합니다.")
                    return fallback_provider.create_llm()
                else:
                    raise ValueError("사용 가능한 AI Provider가 없습니다.")
            
            logger.info(f"AI Provider '{self.current_provider_name}' 사용, 모델: {provider.get_model_name()}")
            return provider.create_llm()
            
        except ImportError as e:
            logger.error(f"AI Provider 초기화 실패: {e}")
            # Google으로 폴백 시도
            fallback_provider = self.providers["google"]
            if fallback_provider.is_available():
                try:
                    logger.info("Google Gemini로 폴백합니다.")
                    return fallback_provider.create_llm()
                except ImportError:
                    raise ImportError("Google Gemini도 초기화할 수 없습니다. Google ADK가 설치되어 있는지 확인하세요.")
            else:
                raise ImportError("사용 가능한 AI Provider가 없습니다.")
        except Exception as e:
            logger.error(f"AI Provider 초기화 중 예상치 못한 오류: {e}")
            raise
    
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

# 디버깅을 위한 환경변수 로그
logger.info(f"환경변수 상태 - GOOGLE_API_KEY: {'설정됨' if os.getenv('GOOGLE_API_KEY') else '설정되지 않음'}")
logger.info(f"AI_CONFIG 상태 - google_api_key: {'설정됨' if ai_config.google_api_key else '설정되지 않음'}")
logger.info(f"GOOGLE_LLM_AVAILABLE: {GOOGLE_LLM_AVAILABLE}")
logger.info(f"LITE_LLM_AVAILABLE: {LITE_LLM_AVAILABLE}")
