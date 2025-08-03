"""
AI Provider 관리 모듈
Groq와 Ollama를 선택적으로 사용할 수 있도록 관리합니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import openai
import groq
from config import config

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """AI Provider 추상 클래스"""
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """프롬프트에 대한 응답을 생성합니다."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Provider가 사용 가능한지 확인합니다."""
        pass

class GroqProvider(AIProvider):
    """Groq AI Provider"""
    
    def __init__(self):
        self.client = None
        self.model = config.GROQ_MODEL
        self._initialize_client()
    
    def _initialize_client(self):
        """Groq 클라이언트를 초기화합니다."""
        try:
            if not config.GROQ_API_KEY:
                logger.error("Groq API 키가 설정되지 않았습니다.")
                return
            
            self.client = groq.Groq(api_key=config.GROQ_API_KEY)
            logger.info(f"Groq 클라이언트가 초기화되었습니다. 모델: {self.model}")
        except Exception as e:
            logger.error(f"Groq 클라이언트 초기화 실패: {e}")
    
    async def generate_response(self, prompt: str) -> str:
        """Groq를 사용하여 응답을 생성합니다."""
        if not self.client:
            return "Groq 클라이언트가 초기화되지 않았습니다."
        
        try:
            import httpx
            
            # httpx를 사용하여 timeout 설정
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "당신은 MySQL 데이터베이스 쿼리 전문가입니다. 자연어를 SQL 쿼리로 변환해주세요."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.1
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"Groq API 오류: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"Groq 응답 생성 실패: {e}")
            return f"응답 생성 중 오류가 발생했습니다: {e}"
    
    def is_available(self) -> bool:
        """Groq가 사용 가능한지 확인합니다."""
        return self.client is not None and config.GROQ_API_KEY is not None

class OllamaProvider(AIProvider):
    """Ollama AI Provider"""
    
    def __init__(self):
        self.url = config.OLLAMA_URL
        self.model = config.OLLAMA_MODEL
        self._initialize_client()
    
    def _initialize_client(self):
        """Ollama 클라이언트를 초기화합니다."""
        try:
            logger.info(f"Ollama 클라이언트가 초기화되었습니다. 모델: {self.model}")
        except Exception as e:
            logger.error(f"Ollama 클라이언트 초기화 실패: {e}")
    
    async def generate_response(self, prompt: str) -> str:
        """Ollama를 사용하여 응답을 생성합니다."""
        try:
            import httpx
            import json
            
            # 메시지를 프롬프트로 변환
            messages = [
                {"role": "system", "content": "당신은 MySQL 데이터베이스 쿼리 전문가입니다. 자연어를 SQL 쿼리로 변환해주세요."},
                {"role": "user", "content": prompt}
            ]
            
            # 프롬프트 구성
            prompt_text = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt_text += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt_text += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    prompt_text += f"Assistant: {msg['content']}\n\n"
            
            # 프롬프트 길이 제한
            if len(prompt_text) > 4000:
                prompt_text = prompt_text[:4000] + "\n\n[Content truncated due to length]"
            
            payload = {
                "model": self.model,
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1024
                }
            }
            
            logger.debug(f"Ollama API 호출 시작: {self.url}/api/generate")
            logger.debug(f"모델: {self.model}")
            logger.debug(f"프롬프트 길이: {len(prompt_text)}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=180.0  # 타임아웃을 180초로 설정
                )
                
                logger.debug(f"Ollama API 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "응답이 없습니다.")
                    
                    # UTF-8 인코딩 문제 해결
                    try:
                        # 응답 텍스트를 UTF-8로 정리
                        if isinstance(response_text, bytes):
                            response_text = response_text.decode('utf-8', errors='ignore')
                        elif isinstance(response_text, str):
                            # 특수 문자나 인코딩 문제가 있는 문자 제거
                            response_text = response_text.encode('utf-8', errors='ignore').decode('utf-8')
                        
                        # 제어 문자 제거
                        import re
                        response_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', response_text)
                        
                        logger.debug(f"Ollama 응답 (정리됨): {response_text[:200]}...")
                        return response_text
                    except Exception as e:
                        logger.error(f"응답 텍스트 정리 중 오류: {e}")
                        return "SQL 쿼리 생성 중 오류가 발생했습니다."
                else:
                    error_msg = f"Ollama API 오류: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return error_msg
                    
        except httpx.TimeoutException:
            error_msg = "Ollama API 호출 시간 초과"
            logger.error(error_msg)
            return error_msg
        except httpx.ConnectError:
            error_msg = "Ollama 서버에 연결할 수 없습니다"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Ollama 응답 생성 실패: {e}"
            logger.error(error_msg)
            return error_msg
    
    def is_available(self) -> bool:
        """Ollama가 사용 가능한지 확인합니다."""
        try:
            import httpx
            import asyncio
            
            # 간단한 연결 테스트
            async def test_connection():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.url}/api/tags", timeout=5.0)
                        if response.status_code == 200:
                            data = response.json()
                            models = data.get("models", [])
                            available_models = [model.get("name", "") for model in models]
                            logger.info(f"사용 가능한 Ollama 모델: {available_models}")
                            if self.model in available_models:
                                return True
                            else:
                                logger.warning(f"요청한 모델 '{self.model}'을 찾을 수 없습니다.")
                                return False
                        else:
                            logger.error(f"Ollama API 응답 오류: {response.status_code}")
                            return False
                except Exception as e:
                    logger.error(f"Ollama 연결 테스트 중 오류: {e}")
                    return False
            
            # 동기적으로 실행
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(test_connection())
                return result
            except Exception as e:
                logger.error(f"이벤트 루프 실행 오류: {e}")
                return False
            finally:
                try:
                    loop.close()
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Ollama 연결 테스트 실패: {e}")
            return False

class AIProviderManager:
    """AI Provider 관리자"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {
            "groq": GroqProvider(),
            "ollama": OllamaProvider()
        }
        self.current_provider = config.AI_PROVIDER.lower()
        
        # 현재 Provider가 사용 불가능한 경우 다른 Provider로 자동 전환
        if not self.providers[self.current_provider].is_available():
            self._switch_to_available_provider()
    
    def _switch_to_available_provider(self):
        """사용 가능한 Provider로 전환합니다."""
        for provider_name, provider in self.providers.items():
            if provider.is_available():
                self.current_provider = provider_name
                logger.info(f"AI Provider가 {provider_name}로 전환되었습니다.")
                return
        
        logger.error("사용 가능한 AI Provider가 없습니다.")
    
    async def generate_response(self, prompt: str) -> str:
        """현재 Provider를 사용하여 응답을 생성합니다."""
        provider = self.providers.get(self.current_provider)
        if not provider:
            return "사용 가능한 AI Provider가 없습니다."
        
        return await provider.generate_response(prompt)
    
    def get_current_provider(self) -> str:
        """현재 사용 중인 Provider 이름을 반환합니다."""
        return self.current_provider
    
    def switch_provider(self, provider_name: str) -> bool:
        """Provider를 전환합니다."""
        if provider_name.lower() in self.providers:
            provider = self.providers[provider_name.lower()]
            if provider.is_available():
                self.current_provider = provider_name.lower()
                logger.info(f"AI Provider가 {provider_name}로 전환되었습니다.")
                return True
            else:
                logger.warning(f"{provider_name} Provider가 사용 불가능합니다.")
                return False
        else:
            logger.error(f"알 수 없는 Provider: {provider_name}")
            return False

# 전역 AI Provider Manager 인스턴스
ai_manager = AIProviderManager() 