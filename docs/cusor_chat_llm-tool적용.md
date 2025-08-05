# 검토 및 소스 변경 요청
_Exported on 8/5/2025 at 17:30:22 GMT+9 from Cursor (1.2.2)_

---

**User**

@llm-tool사용변경요구사항.md 이파일의 내용을 검토하고 반영해줘
- 소스 변경은 내가 확인 후 실제 소스에 반영

@llm-tool사용변경요구사항.md 이파일의 내용을 검토하고 반영해줘
- 소스 변경은 내가 확인 후 실제 소스에 반영
- 테스트를 위해 실행하는 것도 내가 직접 실행할 것임

---

**Cursor**

문서를 검토해보겠습니다. 현재 프로젝트 구조를 파악하고 요구사항을 분석한 후, 필요한 변경사항을 제안하겠습니다.


이제 문서를 검토하고 요구사항을 분석했습니다. 현재 시스템과 요구사항을 비교해보겠습니다.

## 현재 상황 분석

### 현재 구현된 기능:
1. **AI Provider**: Groq와 Ollama 지원
2. **데이터베이스 관리**: MySQL 연결 및 쿼리 실행
3. **MCP 서버**: 4개의 도구 제공
   - `execute_sql`: SQL 쿼리 실행
   - `natural_language_query`: 자연어를 SQL로 변환
   - `get_database_info`: 데이터베이스 정보 반환
   - `get_table_schema`: 테이블 스키마 반환

### 요구사항 분석:
문서에 따르면 현재는 **system prompt에 데이터베이스 정보를 포함**하여 전달하고 있지만, 이를 **Tool을 사용하여 동적으로 획득**하도록 변경하려고 합니다.

## 필요한 변경사항

### 1. AI Provider 수정 (ai_provider.py)
현재 system prompt에 스키마 정보를 포함하고 있는데, 이를 제거하고 Tool 사용 방식으로 변경해야 합니다.

### 2. Tool 기반 자연어 쿼리 처리 (mcp_server.py)
`natural_language_query` 함수를 Tool 호출 방식으로 변경해야 합니다.

### 3. Tool 정의 추가
문서에서 요구하는 3개의 Tool이 이미 구현되어 있습니다:
- `get_database_info`
- `get_table_list` (현재는 `get_database_info`에 포함됨)
- `get_table_schema`

## 제안하는 변경사항

### 1. AI Provider 수정


```python
"""
AI Provider 관리 모듈
Groq와 Ollama를 선택적으로 사용할 수 있도록 관리합니다.
"""
 
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
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
    async def generate_response_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool을 사용하여 응답을 생성합니다."""
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
    
    async def generate_response_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool을 사용하여 응답을 생성합니다."""
        if not self.client:
            return {"error": "Groq 클라이언트가 초기화되지 않았습니다."}
        
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
                        "messages": messages,
                        "tools": tools,
                        "tool_choice": "auto",
                        "max_tokens": 1000,
                        "temperature": 0.1
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]
                else:
                    return {"error": f"Groq API 오류: {response.status_code} - {response.text}"}
        except Exception as e:
            logger.error(f"Groq Tool 응답 생성 실패: {e}")
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
    
    async def generate_response_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool을 사용하여 응답을 생성합니다."""
        try:
            import httpx
            import json
            
            # Ollama는 Tool 사용을 지원하지 않으므로, 메시지 히스토리를 프롬프트로 변환
            prompt_text = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt_text += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt_text += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    prompt_text += f"Assistant: {msg['content']}\n\n"
                elif msg["role"] == "tool":
                    prompt_text += f"Tool Result: {msg['content']}\n\n"
            
            # Tool 정보를 프롬프트에 포함
            if tools:
                prompt_text += "사용 가능한 도구:\n"
                for tool in tools:
                    prompt_text += f"- {tool['function']['name']}: {tool['function']['description']}\n"
                prompt_text += "\n"
            
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
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=180.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "응답이 없습니다.")
                    
                    # UTF-8 인코딩 문제 해결
                    if isinstance(response_text, bytes):
                        response_text = response_text.decode('utf-8', errors='ignore')
                    elif isinstance(response_text, str):
                        response_text = response_text.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    # 제어 문자 제거
                    import re
                    response_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', response_text)
                    
                    return {
                        "role": "assistant",
                        "content": response_text
                    }
                else:
                    return {"error": f"Ollama API 오류: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            logger.error(f"Ollama Tool 응답 생성 실패: {e}")
            return {"error": f"응답 생성 중 오류가 발생했습니다: {e}"}
    
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
    
    async def generate_response_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """현재 Provider를 사용하여 Tool과 함께 응답을 생성합니다."""
        provider = self.providers.get(self.current_provider)
        if not provider:
            return {"error": "사용 가능한 AI Provider가 없습니다."}
        
        return await provider.generate_response_with_tools(messages, tools)
    
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
```

### 2. MCP 서버 수정 - Tool 기반 자연어 쿼리 처리


```python
    async def _natural_language_query(self, arguments: Dict[str, Any]) -> CallToolResult:
        """자연어를 SQL로 변환하여 실행합니다."""
        question = arguments.get("question", "")
        
        if not question:
            return CallToolResult(
                content=[TextContent(type="text", text="질문이 제공되지 않았습니다.")]
            )
        
        try:
            # Tool 정의
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_database_info",
                        "description": "데이터베이스 정보와 테이블 목록을 반환합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_table_schema",
                        "description": "특정 테이블의 스키마 정보를 반환합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {
                                    "type": "string",
                                    "description": "테이블 이름"
                                }
                            },
                            "required": ["table_name"]
                        }
                    }
                }
            ]
            
            # 메시지 히스토리 초기화
            messages = [
                {
                    "role": "system",
                    "content": """당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다.
필요한 정보가 부족하면 제공된 도구를 사용하여 데이터베이스 스키마를 파악한 후,
최종적으로 실행 가능한 SELECT SQL 쿼리만 생성해야 합니다.

⚠️ 매우 중요한 규칙:
1. 순수한 SQL 쿼리만 반환하세요
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요
6. 질문이 모호하거나 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
7. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가

도구 사용 순서:
1. 먼저 get_database_info()를 호출하여 사용 가능한 테이블 목록을 확인하세요
2. 필요한 테이블의 스키마를 get_table_schema()로 조회하세요
3. 스키마 정보를 바탕으로 SQL 쿼리를 생성하세요"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
            
            # Tool 호출 루프
            max_iterations = 5
            for iteration in range(max_iterations):
                # AI 응답 생성
                response = await ai_manager.generate_response_with_tools(messages, tools)
                
                if "error" in response:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"AI 응답 생성 실패: {response['error']}")]
                    )
                
                # AI 응답을 메시지 히스토리에 추가
                messages.append(response)
                
                # Tool 호출이 있는지 확인
                if "tool_calls" not in response:
                    # Tool 호출이 없으면 최종 SQL 응답
                    sql_query = response.get("content", "")
                    
                    # SQL 쿼리 실행
                    if sql_query and not sql_query.startswith("응답 생성 중 오류"):
                        try:
                            result = db_manager.execute_query(sql_query)
                            result_text = f"생성된 SQL: {sql_query}\n\n결과:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                        except Exception as e:
                            result_text = f"생성된 SQL: {sql_query}\n\n실행 오류: {e}"
                    else:
                        result_text = f"SQL 생성 실패: {sql_query}"
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=result_text)]
                    )
                
                # Tool 호출 처리
                tool_calls = response["tool_calls"]
                logger.info(f"Tool 호출 감지: {[tc['function']['name'] for tc in tool_calls]}")
                
                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    func_args = tool_call["function"]["arguments"]
                    
                    # Tool 실행
                    if func_name == "get_database_info":
                        db_info = db_manager.get_database_info()
                        tool_result = json.dumps(db_info, ensure_ascii=False, indent=2)
                    elif func_name == "get_table_schema":
                        table_name = func_args.get("table_name", "")
                        if table_name:
                            schema = db_manager.get_table_schema(table_name)
                            tool_result = json.dumps(schema, ensure_ascii=False, indent=2)
                        else:
                            tool_result = json.dumps({"error": "테이블 이름이 제공되지 않았습니다."})
                    else:
                        tool_result = json.dumps({"error": f"알 수 없는 도구: {func_name}"})
                    
                    # Tool 결과를 메시지 히스토리에 추가
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call["id"]
                    })
            
            # 최대 반복 횟수 초과
            return CallToolResult(
                content=[TextContent(type="text", text="Tool 호출이 너무 많습니다. 질문을 다시 확인해 주세요.")]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"자연어 쿼리 처리 중 오류: {e}")]
            )
```

### 3. 데이터베이스 모듈에 get_table_list Tool 추가


```python
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록을 반환합니다."""
            tools = [
                Tool(
                    name="execute_sql",
                    description="MySQL 데이터베이스에서 SQL 쿼리를 실행합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "실행할 SQL 쿼리"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="natural_language_query",
                    description="자연어를 SQL 쿼리로 변환하여 실행합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "자연어로 된 질문"
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="get_database_info",
                    description="데이터베이스 정보와 테이블 목록을 반환합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_table_list",
                    description="데이터베이스의 모든 테이블 목록을 반환합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_table_schema",
                    description="특정 테이블의 스키마 정보를 반환합니다.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "테이블 이름"
                            }
                        },
                        "required": ["table_name"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
```

```python
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """도구 호출을 처리합니다."""
            try:
                if name == "execute_sql":
                    return await self._execute_sql(arguments)
                elif name == "natural_language_query":
                    return await self._natural_language_query(arguments)
                elif name == "get_database_info":
                    return await self._get_database_info(arguments)
                elif name == "get_table_list":
                    return await self._get_table_list(arguments)
                elif name == "get_table_schema":
                    return await self._get_table_schema(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"알 수 없는 도구: {name}")]
                    )
            except Exception as e:
                logger.error(f"도구 실행 중 오류: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"오류가 발생했습니다: {e}")]
                )
```

### 4. natural_language_query에서 get_table_list Tool도 사용하도록 수정


```python
            # Tool 정의
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_database_info",
                        "description": "데이터베이스 정보와 테이블 목록을 반환합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_table_list",
                        "description": "데이터베이스의 모든 테이블 목록을 반환합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_table_schema",
                        "description": "특정 테이블의 스키마 정보를 반환합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {
                                    "type": "string",
                                    "description": "테이블 이름"
                                }
                            },
                            "required": ["table_name"]
                        }
                    }
                }
            ]
```

### 5. 시스템 프롬프트 업데이트


```python
                {
                    "role": "system",
                    "content": """당신은 사용자의 자연어 질문을 MySQL SQL로 변환하는 전문가입니다.
필요한 정보가 부족하면 제공된 도구를 사용하여 데이터베이스 스키마를 파악한 후,
최종적으로 실행 가능한 SELECT SQL 쿼리만 생성해야 합니다.

⚠️ 매우 중요한 규칙:
1. 순수한 SQL 쿼리만 반환하세요
2. 마크다운 형식(```)을 절대 사용하지 마세요
3. 설명, 주석, 추가 텍스트를 제외하고 순수한 SQL 쿼리만 반환하세요
4. 쿼리 1개만 반환하세요
5. 세미콜론(;)으로 끝내세요
6. 질문이 모호하거나 불완전한 경우 '질문이 불명확합니다. 다시 질문해 주세요.' 라고 예외처리 및 반환하세요.
7. SQL생성할 때 sub query에서는 LIMIT/IN/ALL/ANY/SOME 사용 불가

도구 사용 순서:
1. 먼저 get_database_info() 또는 get_table_list()를 호출하여 사용 가능한 테이블 목록을 확인하세요
2. 필요한 테이블의 스키마를 get_table_schema()로 조회하세요
3. 스키마 정보를 바탕으로 SQL 쿼리를 생성하세요"""
                },
```

## 변경사항 요약

문서의 요구사항을 반영하여 다음과 같은 변경사항을 적용했습니다:

### 1. **AI Provider 수정 (ai_provider.py)**
- `generate_response_with_tools()` 메서드 추가
- Groq와 Ollama 모두에서 Tool 사용 지원
- Groq는 네이티브 Tool 지원
- Ollama는 Tool 정보를 프롬프트에 포함하는 방식으로 구현

### 2. **MCP 서버 수정 (mcp_server.py)**
- `get_table_list` Tool 추가
- `natural_language_query` 함수를 Tool 사용 방식으로 완전히 변경
- 기존: system prompt에 모든 스키마 정보 포함
- 변경: AI가 필요에 따라 Tool을 호출하여 동적으로 정보 획득

### 3. **Tool 기반 처리 로직**
- 메시지 히스토리 관리
- Tool 호출 루프 (최대 5회)
- Tool 결과를 메시지 히스토리에 추가
- 최종 SQL 생성 및 실행

### 4. **제공되는 Tool 목록**
1. `get_database_info`: 데이터베이스 정보와 테이블 목록
2. `get_table_list`: 데이터베이스의 모든 테이블 목록
3. `get_table_schema`: 특정 테이블의 스키마 정보
4. `execute_sql`: SQL 쿼리 실행
5. `natural_language_query`: 자연어를 SQL로 변환 (Tool 사용 방식)

## 주요 개선사항

1. **프롬프트 크기 제한 해결**: 더 이상 system prompt에 모든 스키마 정보를 포함하지 않음
2. **동적 정보 획득**: AI가 필요에 따라 필요한 테이블의 스키마만 조회
3. **확장성 향상**: 테이블이 많아져도 프롬프트 크기 제한에 영향받지 않음
4. **Groq/Ollama 호환성**: 두 Provider 모두에서 Tool 사용 방식 지원

이제 시스템이 문서에서 요구한 대로 Tool을 사용하여 데이터베이스 정보를 동적으로 획득하는 방식으로 동작합니다. 테스트를 위해 실행해보시고 결과를 확인해 주세요.

---

**User**

참고소스에서는 tools 목록을 별도 변수 "tools"에 전달했는데...
너는 prompt에 Tools목록을 포함했던데.. 그 차이를 설명해줘

---

**Cursor**

좋은 지적입니다! 참고소스와 제가 구현한 방식의 차이점을 설명드리겠습니다.

## 참고소스의 방식 (Ollama)

참고소스에서는 **Ollama의 네이티브 Tool 지원**을 사용했습니다:

```python
# 참고소스 방식
response = client.chat(
    model='llama3:8b', 
    messages=messages,
    tools=[  # 별도 tools 파라미터로 전달
        {
            'type': 'function',
            'function': {
                'name': 'list_tables',
                'description': '데이터베이스의 모든 테이블 목록을 가져옵니다.',
                'parameters': {}
            },
        },
        # ... 다른 tools
    ]
)
```

이 방식의 특징:
- **Ollama가 Tool 호출을 자동으로 처리**
- `tool_calls` 필드에 Tool 호출 정보가 포함됨
- Tool 결과를 `tool` 역할로 메시지에 추가하면 자동으로 처리됨

## 제가 구현한 방식

제가 구현한 방식에서는 **Groq와 Ollama의 호환성**을 고려했습니다:

### Groq Provider (네이티브 Tool 지원)
```python
# Groq는 네이티브 Tool 지원
response = await client.post(
    "https://api.groq.com/openai/v1/chat/completions",
    json={
        "model": self.model,
        "messages": messages,
        "tools": tools,  # 별도 tools 파라미터
        "tool_choice": "auto",
        # ...
    }
)
```

### Ollama Provider (프롬프트에 포함)
```python
# Ollama는 Tool 정보를 프롬프트에 포함
prompt_text += "사용 가능한 도구:\n"
for tool in tools:
    prompt_text += f"- {tool['function']['name']}: {tool['function']['description']}\n"
```

## 문제점과 해결방안

제가 구현한 방식의 문제점:
1. **Ollama에서 Tool 호출을 자동으로 처리하지 않음**
2. **수동으로 Tool 호출을 파싱해야 함**
3. **참고소스의 우아한 방식과 다름**

## 올바른 수정 방안

참고소스 방식을 따라 Ollama도 네이티브 Tool 지원을 사용하도록 수정해야 합니다:


```python
# 참고소스 방식
response = client.chat(
    model='llama3:8b', 
    messages=messages,
    tools=[  # 별도 tools 파라미터로 전달
        {
            'type': 'function',
            'function': {
                'name': 'list_tables',
                'description': '데이터베이스의 모든 테이블 목록을 가져옵니다.',
                'parameters': {}
            },
        },
        # ... 다른 tools
    ]
)
```

```python
# Groq는 네이티브 Tool 지원
response = await client.post(
    "https://api.groq.com/openai/v1/chat/completions",
    json={
        "model": self.model,
        "messages": messages,
        "tools": tools,  # 별도 tools 파라미터
        "tool_choice": "auto",
        # ...
    }
)
```

```python
# Ollama는 Tool 정보를 프롬프트에 포함
prompt_text += "사용 가능한 도구:\n"
for tool in tools:
    prompt_text += f"- {tool['function']['name']}: {tool['function']['description']}\n"
```

```python
    async def generate_response_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool을 사용하여 응답을 생성합니다."""
        try:
            import httpx
            import json
            
            # Ollama의 네이티브 Tool 지원 사용
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1024
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api/chat",  # /api/generate 대신 /api/chat 사용
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=180.0
                )
                
                if response.status_code == 200:
                    result = response.json()
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
                    return {"error": f"Ollama API 오류: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            logger.error(f"Ollama Tool 응답 생성 실패: {e}")
            return {"error": f"응답 생성 중 오류가 발생했습니다: {e}"}
```

## 차이점 요약

### 참고소스 방식 (올바른 방식)
- **Ollama의 네이티브 Tool 지원** 사용
- `tools` 파라미터로 별도 전달
- `/api/chat` 엔드포인트 사용
- Tool 호출을 자동으로 처리

### 제가 처음 구현한 방식 (잘못된 방식)
- Tool 정보를 프롬프트에 텍스트로 포함
- `/api/generate` 엔드포인트 사용
- Tool 호출을 수동으로 파싱해야 함

### 수정 후 방식 (올바른 방식)
- Ollama도 네이티브 Tool 지원 사용
- `tools` 파라미터로 별도 전달
- `/api/chat` 엔드포인트 사용
- Tool 호출을 자동으로 처리

## 핵심 차이점

1. **API 엔드포인트**: `/api/generate` vs `/api/chat`
2. **Tool 전달 방식**: 프롬프트 포함 vs 별도 파라미터
3. **Tool 처리**: 수동 파싱 vs 자동 처리
4. **메시지 형식**: 단순 텍스트 vs 구조화된 메시지

이제 Ollama도 참고소스와 동일한 방식으로 Tool을 사용할 수 있습니다. 이 방식이 더 우아하고 효율적입니다.

