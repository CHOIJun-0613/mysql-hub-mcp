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
                            {"role": "system", "content": """
당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다.
필요한 정보가 부족하면 제공된 도구를 사용하여 데이터베이스 스키마를 파악한 후,
최종적으로 실행 가능한 SELECT SQL 쿼리만 생성해야 합니다. 

⚠️ 매우 중요한 규칙:
1. 순수한 SQL 쿼리만 반환하세요
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요
6. 질문이 모호하거나 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
- 문장구성이 안되어 있는 경우
- 불완전하거나 뜻이 모호한 경우
- 문법적으로 잘못되어 있는 경우
- 의미없는 문장으로 되어 있는 경우우
- 예시: '13213214`3ㄹㅇㄴㅁㄹㅇㄴㅁㄹ', 'afdsafdsjaljfdsla' ,'가나다라마바사앙자차카ㅇ타하하'등 
7. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가
- MySQL doesn't yet support
- 해결 방법: 아래와 같이, 별칭(alias)를 주는 방법으로 사용할 수는 있다
- 잘못된 예시: SELECT *  FROM users WHERE id IN ( SELECT user_id FROM orders ORDER BY order_date DESC LIMIT 1);
- 올바른 예시: SELECT u.* FROM users u JOIN orders o ON u.id = o.user_id ORDER BY o.order_date DESC LIMIT 1;

== 예시 ==
예시 올바른 응답:
SELECT * FROM users;

예시 잘못된 응답:
```sql
SELECT * FROM users;
```
또는
SELECT * FROM users;
### 설명: 사용자 테이블의 모든 데이터를 조회합니다.
"""
                            },
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
                {"role": "system", "content": """
당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다.
필요한 정보가 부족하면 제공된 도구를 사용하여 데이터베이스 스키마를 파악한 후,
최종적으로 실행 가능한 SELECT SQL 쿼리만 생성해야 합니다. 

⚠️ 매우 중요한 규칙:
1. 순수한 SQL 쿼리만 반환하세요
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요
6. 질문이 모호하거나 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
- 문장구성이 안되어 있는 경우
- 불완전하거나 뜻이 모호한 경우
- 문법적으로 잘못되어 있는 경우
- 의미없는 문장으로 되어 있는 경우우
- 예시: '13213214`3ㄹㅇㄴㅁㄹㅇㄴㅁㄹ', 'afdsafdsjaljfdsla' ,'가나다라마바사앙자차카ㅇ타하하'등 
7. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가
- MySQL doesn't yet support
- 해결 방법: 아래와 같이, 별칭(alias)를 주는 방법으로 사용할 수는 있다
- 잘못된 예시: SELECT *  FROM users WHERE id IN ( SELECT user_id FROM orders ORDER BY order_date DESC LIMIT 1);
- 올바른 예시: SELECT u.* FROM users u JOIN orders o ON u.id = o.user_id ORDER BY o.order_date DESC LIMIT 1;

== 예시 ==
예시 올바른 응답:
SELECT * FROM users;

예시 잘못된 응답:
```sql
SELECT * FROM users;
```
또는
SELECT * FROM users;
### 설명: 사용자 테이블의 모든 데이터를 조회합니다.
"""},
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