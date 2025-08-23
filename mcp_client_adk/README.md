# MySQL Hub MCP Agent

MySQL Hub MCP를 위한 Google ADK 기반 AI Agent입니다. 이 agent는 MCP(Model Context Protocol) 서버와 통신하여 MySQL 데이터베이스 관련 작업을 수행할 수 있습니다.

## 🚀 주요 기능

- **Google ADK 기반**: Google의 최신 AI 개발 키트를 사용하여 강력한 LLM Agent 구축
- **다중 AI Provider 지원**: Google Gemini, Groq, LM Studio 중 선택하여 사용
- **MCP 서버 지원**: HTTP 및 STDIO 연결을 통한 MCP 서버 통신
- **도구 필터링**: 보안을 위한 선택적 도구 접근 제어
- **비동기 처리**: asyncio를 사용한 효율적인 비동기 작업 처리
- **세션 관리**: 사용자별 세션 상태 관리 및 리소스 정리

## 📁 프로젝트 구조

```
adk_client/
├── agent.py              # AgentWrapper 클래스 - ADK agent 및 MCP 도구 관리
├── client.py             # MCPClient 클래스 - UI/채팅 인터페이스 연결
├── cmd.py                # 명령줄 채팅 클라이언트 진입점
├── ai_config.py          # AI Provider 설정 관리
├── ai_providers.py       # AI Provider별 LLM 클래스들
├── utilities.py          # 설정 파일 읽기 및 JSON 출력 유틸리티
├── mcp_server_config.json  # MCP 서버 연결 설정
├── pyproject.toml        # 프로젝트 의존성 및 빌드 설정
└── README.md             # 이 파일
```

## 🛠️ 설치 및 설정

### 1. 의존성 설치

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install -e .
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음을 추가하세요:

```env
# AI Provider 설정 (google, groq, lmstudio 중 선택)
AI_PROVIDER=google

# Google Gemini 설정
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash

# Groq 설정
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=qwen/qwen3-32b

# LM Studio 설정
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_QWEN_MODEL_NAME=lm_studio/qwen/qwen3-8b
```

### 3. MCP 서버 설정

`mcp_server_config.json` 파일에서 MCP 서버 정보를 설정하세요:

```json
{
    "mcpServers": {
        "mysql-hub-mcp": {
            "type": "http",
            "url": "http://localhost:8000/mcp/"
        }
    }
}
```

## 🚀 사용 방법

### AI Provider 설정

ADK 클라이언트는 다음 AI Provider를 지원합니다:

#### 1. Google Gemini (기본)
```env
AI_PROVIDER=google
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash
```

#### 2. Groq
```env
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=qwen/qwen3-32b
```

#### 3. LM Studio
```env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_QWEN_MODEL_NAME=lm_studio/qwen/qwen3-8b
```

### 명령줄 채팅 클라이언트 실행

```bash
python cmd.py
```

### 프로그래밍 방식으로 사용

```python
from agent.client import MCPClient

# 클라이언트 생성
client = MCPClient(
    app_name="my_app",
    user_id="user_001",
    session_id="session_001"
)

# 세션 초기화
await client.init_session()

# 사용자 입력 전송
async for event in client.send_task("MySQL 데이터베이스 상태를 확인해주세요"):
    print(event)

# 세션 종료
await client.shutdown()
```

## 🔧 주요 클래스

### AgentWrapper

MCP 서버와의 연결을 관리하고 ADK agent를 구성합니다.

```python
from agent.agent import AgentWrapper

# 도구 필터링과 함께 agent 래퍼 생성
agent_wrapper = AgentWrapper(tool_filter=['mysql_query', 'mysql_schema'])

# agent 빌드
await agent_wrapper.build()

# 리소스 정리
await agent_wrapper.close()
```

### MCPClient

사용자 인터페이스와 ADK agent 간의 연결을 관리합니다.

```python
from agent.client import MCPClient

client = MCPClient(
    app_name="mysql_assistant",
    user_id="user_001",
    session_id="session_001"
)

await client.init_session()
response = await client.send_task("사용자 테이블을 조회해주세요")
await client.shutdown()
```

## 📋 지원되는 MCP 서버 유형

### HTTP 서버
```json
{
    "type": "http",
    "url": "http://localhost:8000/mcp/"
}
```

### STDIO 서버
```json
{
    "type": "stdio",
    "command": "python",
    "args": ["-m", "mcp_server"]
}
```

## 🔒 보안 기능

- **도구 필터링**: `tool_filter` 매개변수를 통해 허용된 도구만 로드
- **세션 격리**: 사용자별 세션 상태 분리
- **연결 타임아웃**: STDIO 연결에 대한 타임아웃 설정

## 🐛 문제 해결

### 일반적인 오류

1. **MCP 서버 연결 실패**
   - 서버가 실행 중인지 확인
   - 설정 파일의 URL/명령어 확인
   - 방화벽 설정 확인

2. **도구 로드 실패**
   - 서버에서 제공하는 도구 목록 확인
   - 도구 필터 설정 확인

3. **ADK 초기화 실패**
   - Google API 키 설정 확인
   - 인터넷 연결 상태 확인

### 로그 확인

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 기여하기

1. 이슈 등록 또는 기능 요청
2. 포크 후 기능 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 있거나 질문이 있으시면 이슈를 등록해 주세요.

---

**참고**: 이 agent는 Google ADK와 MCP 프로토콜을 사용합니다. 사용하기 전에 해당 기술의 요구사항과 제한사항을 확인하세요.
