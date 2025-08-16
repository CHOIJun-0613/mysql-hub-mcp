"""
AI Provider 관리 모듈
Groq와 Ollama를 선택적으로 사용할 수 있도록 관리합니다.
"""
 
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import asyncio
import openai
import groq
import httpx

from config import config

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """AI Provider 추상 클래스"""
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """메시지와 도구를 사용하여 응답을 생성합니다."""
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
    
    async def generate_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Groq를 사용하여 응답을 생성합니다."""
        if not self.client:
            return {"error": "Groq 클라이언트가 초기화되지 않았습니다."}
        
        try:
            # 기본 요청 데이터
            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.1,
                "reasoning_format": "hidden"
            }
            
            # Tool이 있으면 추가
            if tools:
                request_data["tools"] = tools
                request_data["tool_choice"] = "auto"
            
            # httpx를 사용하여 timeout 설정
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]
                else:
                    return {"error": f"Groq API 오류: {response.status_code} - {response.text}"}
        except Exception as e:
            logger.error(f"Groq 응답 생성 실패: {e}")
            return {"error": f"응답 생성 중 오류가 발생했습니다: {e}"}
    
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
    
    async def generate_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Ollama를 사용하여 응답을 생성합니다."""
        try:
            # 기본 요청 데이터
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4096
                }
            }
            
            # Tool이 있으면 /api/chat, 없으면 /api/generate 사용
            if tools:
                payload["tools"] = tools
                endpoint = "/api/chat"
            else:
                # 기존 방식과의 호환성을 위해 system과 user 메시지를 하나의 prompt로 결합
                if messages and len(messages) > 0:
                    prompt_parts = []
                    for message in messages:
                        if message.get("role") == "system":
                            prompt_parts.append(f"시스템 지시사항:\n{message.get('content', '')}")
                        elif message.get("role") == "user":
                            prompt_parts.append(f"사용자 질문:\n{message.get('content', '')}")
                    
                    if prompt_parts:
                        payload["prompt"] = "\n\n".join(prompt_parts)
                        del payload["messages"]
                endpoint = "/api/generate"
            
            logger.debug(f"Ollama API 호출 시작: {self.url}{endpoint}")
            logger.debug(f"모델: {self.model}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}{endpoint}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=300.0
                )
                
                logger.debug(f"Ollama API 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if tools:
                        # Tool 사용 방식
                        message = result.get("message", {})
                        
                        # UTF-8 인코딩 문제 해결
                        if "content" in message and isinstance(message["content"], str):
                            content = message["content"]
                            if isinstance(content, bytes):
                                content = content.decode('utf-8', errors='ignore')
                            elif isinstance(content, str):
                                content = content.encode('utf-8', errors='ignore').decode('utf-8')
                            
                            # 제어 문자 제거
                            import re
                            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
                            message["content"] = content
                        
                        return message
                    else:
                        # 기존 방식
                        response_text = result.get("response", "응답이 없습니다.")
                        
                        # UTF-8 인코딩 문제 해결
                        try:
                            if isinstance(response_text, bytes):
                                response_text = response_text.decode('utf-8', errors='ignore')
                            elif isinstance(response_text, str):
                                response_text = response_text.encode('utf-8', errors='ignore').decode('utf-8')
                            
                            # 제어 문자 제거
                            import re
                            response_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', response_text)
                            return {"content": response_text}
                        except Exception as e:
                            logger.error(f"응답 텍스트 정리 중 오류: {e}")
                            return {"error": "SQL 쿼리 생성 중 오류가 발생했습니다."}
                else:
                    error_msg = f"Ollama API 오류: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {"error": error_msg}
                    
        except httpx.TimeoutException:
            error_msg = "Ollama API 호출 시간 초과"
            logger.error(error_msg)
            return {"error": error_msg}
        except httpx.ConnectError:
            error_msg = "Ollama 서버에 연결할 수 없습니다"
            logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Ollama 응답 생성 실패: {e}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def is_available(self) -> bool:
        """Ollama가 사용 가능한지 확인합니다."""
        try:
            
            # 간단한 연결 테스트
            async def test_connection():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.url}/api/tags", timeout=5.0)
                        if response.status_code == 200:
                            data = response.json()
                            models = data.get("models", [])
                            available_models = [model.get("name", "") for model in models]
                            logger.info(f"사용 가능한 Ollama 모델[{self.model}]: {available_models}")
                           
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
                # 현재 이벤트 루프가 있는지 확인
                try:
                    loop = asyncio.get_running_loop()
                    # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, test_connection())
                        return future.result()
                except RuntimeError:
                    # 실행 중인 루프가 없으면 직접 실행
                    return asyncio.run(test_connection())
            except Exception as e:
                logger.error(f"이벤트 루프 실행 오류: {e}")
                return False
                
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
    
    async def generate_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """현재 Provider를 사용하여 응답을 생성합니다."""
        provider = self.providers.get(self.current_provider)
        if not provider:
            return {"error": "사용 가능한 AI Provider가 없습니다."}
        
        return await provider.generate_response(messages, tools)
    
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