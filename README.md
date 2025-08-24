# Database Hub MCP (Model Context Protocol)

이 프로젝트는 자연어 쿼리를 사용하여 MySQL, PostgreSQL, Oracle 등 다양한 데이터베이스와 상호작용할 수 있는 지능형 데이터베이스 허브입니다. 
MCP(Model Context Protocol)를 기반으로 구축되었으며, 여러 AI Provider(Groq, Ollama, LM Studio, Google Gemini)를 통해 자연어를 SQL로 변환하는 기능을 제공합니다.

## 🚀 주요 기능

- **다중 데이터베이스 지원**: MySQL, PostgreSQL, Oracle 데이터베이스에 연결하고 쿼리를 실행합니다.
- **자연어 쿼리**: 사용자의 자연어 질문을 AI가 이해하고 SQL로 변환하여 데이터베이스에 질의합니다.
- **다중 AI Provider 지원**: Groq, Ollama, LM Studio, Google Gemini 등 다양한 LLM Provider를 선택하여 사용할 수 있습니다.
- **MCP 및 HTTP 서버**: MCP 프로토콜을 지원하는 서버와 테스트 및 연동을 위한 HTTP API 서버를 모두 제공합니다.
- **에이전트 기반 아키텍처**: Google ADK 기반의 AI 에이전트를 통해 확장 가능한 기능을 제공합니다.

## 📂 프로젝트 구조

```
mysql-hub-mcp/
├── app_mcp_server/       # MCP 및 HTTP 서버 애플리케이션
├── app_client/           # 서버 테스트를 위한 클라이언트 (웹, 콘솔)
├── mcp_agents_adk/       # Google ADK 기반 AI 에이전트
├── mcp_bridge/           # Cursor 등 외부 도구와의 연결을 위한 브릿지
├── mcp_client_adk/       # ADK 클라이언트
├── run_cmd/              # 서버 및 클라이언트 실행을 위한 배치 스크립트
├── docs/                 # 프로젝트 요구사항 및 관련 문서
├── requirements.txt      # Python 의존성 목록
└── README.md             # 프로젝트 안내 문서
```

## 🛠️ 설치 및 설정

### 1. 사전 요구사항

- Python 3.9 이상
- Git

### 2. 프로젝트 클론 및 가상환경 설정

```bash
git clone https://github.com/your-repo/mysql-hub-mcp.git
cd mysql-hub-mcp
python -m venv .venv
.venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```
**참고**: 특정 데이터베이스 사용 시 추가 드라이버 설치가 필요할 수 있습니다. (`psycopg2-binary` for PostgreSQL, `cx_Oracle` for Oracle)

### 4. 환경변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 각 컴포넌트의 `.env.example` 파일을 참고하여 아래와 같이 환경 변수를 설정합니다.

**주요 설정 파일:**
- `app_mcp_server/env.example`: 메인 서버(DB, AI Provider) 설정
- `mcp_agents_adk/db_hub_agent/env.example`: AI 에이전트 설정

**`.env` 파일 예시:**
```env
# --- MCP 서버 설정 ---
# 데이터베이스 타입 (mysql, postgresql, oracle)
DATABASE_TYPE=mysql

# MySQL 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

# AI Provider 설정 (groq, ollama, lmstudio)
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder

# 서버 주소
HTTP_SERVER_HOST="127.0.0.1"
SERVER_PORT=9000
MCP_SERVER_HOST="127.0.0.1"
MCP_SERVER_PORT=7000

# --- Agent 설정 ---
# 에이전트용 AI Provider (google, groq, lmstudio)
AGENT_AI_PROVIDER=google
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL_NAME=gemini-1.5-flash
```

## ▶️ 실행 방법

`run_cmd` 디렉토리의 배치 스크립트를 사용하여 각 컴포넌트를 실행할 수 있습니다.

1.  **HTTP 서버 실행** (REST API 테스트용)
    ```batch
    run_cmd\1-1.run_http_server.bat
    ```

2.  **MCP 서버 실행** (MCP 클라이언트 연결용)
    ```batch
    run_cmd\2-1.run_mcp_server.bat
    ```

3.  **MCP 에이전트 실행** (콘솔)
    ```batch
    run_cmd\2-2.run_mcp_agent_cmd.bat
    ```

## ⚙️ 주요 컴포넌트 설명

### 1. `app_mcp_server`
- 프로젝트의 핵심 백엔드 서버입니다.
- **HTTP Server**: RESTful API를 제공하여 외부 애플리케이션과의 연동을 지원합니다. (자연어 쿼리, DB 스키마 조회 등)
- **MCP Server**: MCP 표준을 준수하는 클라이언트(예: Cursor)와 통신합니다.

### 2. `mcp_agents_adk`
- Google Agent Development Kit (ADK)를 사용하여 구현된 AI 에이전트입니다.
- MCP 서버와 통신하며, 설정된 AI Provider(Gemini, Groq 등)를 통해 복잡한 추론 및 작업을 수행합니다.

### 3. `app_client`
- 서버의 기능을 테스트하기 위한 샘플 클라이언트입니다.
- `client_app.py`: 콘솔 기반 클라이언트
- `client_web.py`: 웹 기반 클라이언트 (Streamlit 사용)

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.