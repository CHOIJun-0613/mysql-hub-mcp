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
import google.generativeai as genai
from config import config

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """AI Provider 추상 클래스"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
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
    
    async def generate_response(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Groq를 사용하여 응답을 생성합니다."""
        if not self.client:
            return "Groq 클라이언트가 초기화되지 않았습니다."
        
        try:
            
            # 환경변수에 따라 Tool 사용 여부 결정
            if config.USE_LLM_TOOLS and tools:
                # Tool 사용 방식
                request_data = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "tools": tools,
                    "tool_choice": "auto",
                    "max_tokens": 1000,
                    "temperature": 0.1
                }
            else:
                # 기존 방식 - http_server.py에서 전달받은 프롬프트 그대로 사용
                request_data = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.1
                }
            
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
                    message = result["choices"][0]["message"]
                    
                    # Tool 사용 방식인 경우 tool_calls가 있을 수 있음
                    if config.USE_LLM_TOOLS and tools and "tool_calls" in message:
                        # Tool 호출이 있는 경우 처리
                        tool_calls = message.get("tool_calls", [])
                        if tool_calls:
                            # 첫 번째 tool call의 함수 이름 반환 (디버깅용)
                            first_tool = tool_calls[0]
                            func_name = first_tool.get("function", {}).get("name", "unknown")
                            return f"Tool 호출 감지: {func_name} (tools 지원 필요)"
                    
                    return message.get("content", "응답이 없습니다.")
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
    
    async def generate_response(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Ollama를 사용하여 응답을 생성합니다."""
        try:
            
            # 환경변수에 따라 Tool 사용 여부 결정
            if config.USE_LLM_TOOLS and tools:
                # Tool 사용 방식 - Ollama의 네이티브 Tool 지원 사용
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
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
                
                endpoint = "/api/chat"  # Tool 사용시 /api/chat 엔드포인트 사용
            else:
                # 기존 방식 - http_server.py에서 전달받은 프롬프트 그대로 사용
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1024
                    }
                }
                
                endpoint = "/api/generate"  # 기존 방식은 /api/generate 엔드포인트 사용
            
            logger.debug(f"Ollama API 호출 시작: {self.url}{endpoint}")
            logger.debug(f"모델: {self.model}")
            if not config.USE_LLM_TOOLS or not tools:
                logger.debug(f"프롬프트 길이: {len(payload.get('prompt', ''))}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}{endpoint}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=180.0  # 타임아웃을 180초로 설정
                )
                
                logger.debug(f"Ollama API 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if config.USE_LLM_TOOLS and tools:
                        # Tool 사용 방식
                        message = result.get("message", {})
                        response_text = message.get("content", "응답이 없습니다.")
                        
                        # Tool 호출이 있는 경우 처리
                        if "tool_calls" in message:
                            tool_calls = message.get("tool_calls", [])
                            if tool_calls:
                                first_tool = tool_calls[0]
                                func_name = first_tool.get("function", {}).get("name", "unknown")
                                return f"Tool 호출 감지: {func_name} (tools 지원 필요)"
                    else:
                        # 기존 방식
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

class GoogleProvider(AIProvider):
    """Google Gemini AI Provider"""
    
    def __init__(self):
        self.client = None
        self.model = config.GOOGLE_MODEL
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Gemini 클라이언트를 초기화합니다."""
        try:
            if not config.GOOGLE_API_KEY:
                logger.error("Google API 키가 설정되지 않았습니다.")
                return
            
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Google Gemini 클라이언트가 초기화되었습니다. 모델: {self.model}")
        except Exception as e:
            logger.error(f"Google Gemini 클라이언트 초기화 실패: {e}")
    
    async def generate_response(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Google Gemini를 사용하여 응답을 생성합니다."""
        if not self.client:
            return "Google Gemini 클라이언트가 초기화되지 않았습니다."
        
        try:
            # 환경변수에 따라 Tool 사용 여부 결정
            if config.USE_LLM_TOOLS and tools:
                # Tool 사용 방식 - Gemini 1.5 Flash는 Tool 지원
                logger.info("Google Gemini 1.5 Flash의 Tool 사용 기능을 활용합니다.")
                
                # Gemini용 Tool 형식으로 변환
                gemini_tools = self._convert_tools_for_gemini(tools)
                
                # Gemini API 호출 (Tool 사용)
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    prompt,
                    tools=gemini_tools,
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=1024
                    )
                )
                
                # Tool 호출이 있는 경우 처리
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    # Tool 호출 정보 반환
                                    try:
                                        func_name = getattr(part.function_call, 'name', 'unknown_function')
                                        func_args = getattr(part.function_call, 'args', {})
                                        
                                        # Google protobuf 객체를 Python dict로 변환
                                        if hasattr(func_args, 'items'):
                                            # MapComposite 객체를 dict로 변환
                                            args_dict = {}
                                            for key, value in func_args.items():
                                                args_dict[str(key)] = str(value)
                                            func_args = args_dict
                                        else:
                                            # 빈 dict로 설정
                                            func_args = {}
                                        
                                        return f"Tool 호출 감지: {func_name} (tools 지원 필요)"
                                    except Exception as e:
                                        logger.warning(f"Tool 호출 파싱 중 오류: {e}")
                                        return response.text or ""
                        
                        # Tool 호출이 감지되지 않은 경우 일반 응답 반환
                        return response.text or ""
                    
                    # content가 없는 경우 일반 응답 반환
                    return response.text or ""
                
                # candidates가 없는 경우 일반 응답 반환
                return response.text or ""
            else:
                # 기본 방식 - Tool 없이 사용
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=1024
                    )
                )
                
                if response.text:
                    return response.text
                else:
                    return "응답이 없습니다."
                
        except Exception as e:
            logger.error(f"Google Gemini 응답 생성 실패: {e}")
            return f"응답 생성 중 오류가 발생했습니다: {e}"
    
    async def generate_response_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool을 사용하여 응답을 생성합니다."""
        if not self.client:
            return {"error": "Google Gemini 클라이언트가 초기화되지 않았습니다."}
        
        try:
            # Gemini용 Tool 형식으로 변환
            gemini_tools = self._convert_tools_for_gemini(tools)
            
            # 메시지를 Gemini 형식으로 변환
            gemini_messages = self._convert_messages_for_gemini(messages)
            
            # Gemini API 호출 (Tool 사용)
            response = await asyncio.to_thread(
                self.client.generate_content,
                gemini_messages,
                tools=gemini_tools,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1024
                )
            )
            logger.debug(f"Gemini 응답 response: \n{response}\n")
            # Tool 호출이 있는 경우 처리
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                logger.debug(f"Gemini 응답 candidate: {candidate}")
                
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    logger.debug(f"Gemini 응답 content: {content}")
                    
                    if hasattr(content, 'parts') and content.parts:
                        logger.debug(f"Gemini 응답 parts: {content.parts}")
                        
                        for part in content.parts:
                            logger.debug(f"Gemini 응답 part: {part}")
                            logger.debug(f"Part attributes: {dir(part)}")
                            
                            if hasattr(part, 'function_call') and part.function_call:
                                logger.info(f"Tool 호출 감지: {part.function_call}")
                                # Tool 호출 정보 반환
                                try:
                                    # function_call의 내용을 안전하게 추출
                                    func_name = getattr(part.function_call, 'name', 'unknown_function')
                                    func_args = getattr(part.function_call, 'args', {})
                                    
                                    # Google protobuf 객체를 Python dict로 변환
                                    if hasattr(func_args, 'items'):
                                        # MapComposite 객체를 dict로 변환
                                        args_dict = {}
                                        for key, value in func_args.items():
                                            args_dict[str(key)] = str(value)
                                        func_args = args_dict
                                    else:
                                        # 빈 dict로 설정
                                        func_args = {}
                                    
                                    logger.info(f"Tool 호출 파싱 성공: {func_name}, args: {func_args}")
                                    
                                    # Tool 호출 정보 반환
                                    return {
                                        "content": response.text or "",
                                        "tool_calls": [{
                                            "id": f"call_{hash(func_name)}",
                                            "type": "function",
                                            "function": {
                                                "name": func_name,
                                                "arguments": func_args
                                            }
                                        }]
                                    }
                                    
                                except Exception as e:
                                    logger.warning(f"Tool 호출 파싱 중 오류: {e}")
                                    # 파싱 실패 시에도 기본 응답 반환
                                    return {"content": response.text or ""}
                        
                        # Tool 호출이 감지되지 않은 경우 일반 응답 반환
                        return {"content": response.text or ""}
                    
                    # content.parts가 없는 경우 일반 응답 반환
                    return {"content": response.text or ""}
                
                # content가 없는 경우 일반 응답 반환
                return {"content": response.text or ""}
            
            # candidates가 없는 경우 일반 응답 반환
            return {"content": response.text or ""}
                
        except Exception as e:
            logger.error(f"Google Gemini Tool 응답 생성 실패: {e}")
            return {"error": f"응답 생성 중 오류가 발생했습니다: {e}"}
    
    def _convert_tools_for_gemini(self, tools: List[Dict[str, Any]]) -> List[genai.types.Tool]:
        """OpenAI 형식의 Tool을 Gemini 형식으로 변환합니다."""
        gemini_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                func_def = tool.get("function", {})
                
                # Gemini Tool 정의 생성
                gemini_tool = genai.types.Tool(
                    function_declarations=[
                        genai.types.FunctionDeclaration(
                            name=func_def.get("name", ""),
                            description=func_def.get("description", ""),
                            parameters=self._convert_schema_for_gemini(func_def.get("parameters", {}))
                        )
                    ]
                )
                gemini_tools.append(gemini_tool)
        
        return gemini_tools
    
    def _convert_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI 스키마를 Gemini 스키마로 변환합니다."""
        try:
            # 기본 스키마 정보 추출
            schema_type = schema.get("type", "object")
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # Gemini 스키마 생성 (Dict 형태로 반환)
            gemini_schema = {
                "type": schema_type,
                "properties": properties,
                "required": required
            }
            
            return gemini_schema
        except Exception as e:
            logger.warning(f"스키마 변환 중 오류, 기본 스키마 사용: {e}")
            # 기본 스키마 반환
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
    
    def _convert_messages_for_gemini(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """OpenAI 형식의 메시지를 Gemini 형식으로 변환합니다."""
        gemini_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
            elif role == "system":
                # Gemini는 system role을 직접 지원하지 않으므로 user role로 변환
                gemini_messages.append({"role": "user", "parts": [{"text": f"System: {content}"}]})
        
        return gemini_messages
    
    def is_available(self) -> bool:
        """Google Gemini가 사용 가능한지 확인합니다."""
        return self.client is not None and config.GOOGLE_API_KEY is not None

class AIProviderManager:
    """AI Provider 관리자"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {
            "groq": GroqProvider(),
            "ollama": OllamaProvider(),
            "google": GoogleProvider()
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
    
    async def generate_response(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """현재 Provider를 사용하여 응답을 생성합니다."""
        provider = self.providers.get(self.current_provider)
        if not provider:
            return "사용 가능한 AI Provider가 없습니다."
        
        # 환경변수에 따라 Tool 사용 여부 결정
        if config.USE_LLM_TOOLS and tools:
            # Tool 사용 방식
            return await provider.generate_response(prompt, tools)
        else:
            # 기존 방식 - tools 파라미터 없이 호출
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