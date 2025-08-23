# MySQL Hub MCP Agent

MySQL Hub MCP를 위한 Google ADK 기반 AI Agent입니다.

## 🚀 주요 기능

- **Google ADK 기반**: Google의 최신 AI 개발 키트를 사용하여 강력한 LLM Agent 구축
- **다중 AI Provider 지원**: Google Gemini, Groq, LM Studio 중 선택하여 사용
- **MCP 서버 지원**: HTTP 및 STDIO 연결을 통한 MCP 서버 통신

## 📁 프로젝트 구조

```
adk_agents/
├── mysql_hub_agent/
│   ├── agent.py              # AgentWrapper 클래스 - ADK agent 및 MCP 도구 관리
│   ├── ai_config.py          # AI Provider 설정 관리
│   ├── ai_providers.py       # AI Provider별 LLM 클래스들
│   ├── utilities.py          # 설정 파일 읽기 및 JSON 출력 유틸리티
│   ├── mcp_server_config.json  # MCP 서버 연결 설정
│   └── env.example           # 환경변수 설정 예시
├── main.py                   # 메인 실행 파일
└── README.md                 # 이 파일
```

## 🛠️ 설치 및 설정

### 1. 환경 변수 설정

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

## 🚀 사용 방법

### AI Provider 설정

ADK Agent는 다음 AI Provider를 지원합니다:

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

### 실행

```bash
python main.py
```

## 🔧 주요 클래스

### AIConfig
환경변수를 통해 AI Provider와 모델을 설정하고 관리합니다.

### AIProviderManager
모든 AI Provider를 통합 관리하고 현재 설정된 Provider에 맞는 LLM을 생성합니다.

### AgentWrapper
MCP 서버와의 연결을 관리하고 ADK agent를 구성합니다.

## 📋 지원하는 AI Provider

- **Google Gemini**: `gemini-1.5-flash` (기본값)
- **Groq**: `qwen/qwen3-32b`
- **LM Studio**: `lm_studio/qwen/qwen3-8b`

## 🤝 기여하기

1. 이슈 등록 또는 기능 요청
2. 포크 후 기능 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
