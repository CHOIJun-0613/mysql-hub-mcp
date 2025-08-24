# MCP/HTTP 서버

이 디렉토리에는 `MySQL Hub MCP` 프로젝트의 핵심 백엔드 서버 코드가 포함되어 있습니다.

## 주요 기능

- **MCP/HTTP 듀얼 프로토콜 지원**: MCP(Model Context Protocol) 표준을 따르는 클라이언트와 통신하는 `mcp_server`와, 일반적인 웹 요청을 처리하는 `http_server`를 모두 지원합니다.
- **데이터베이스 관리**: `database.py`를 통해 MySQL, PostgreSQL, Oracle 등 여러 종류의 데이터베이스 연결 및 쿼리 실행을 관리합니다.
- **AI Provider 연동**: `ai_provider.py`와 `ai_worker.py`를 통해 Ollama, Groq, LM Studio 등 다양한 AI 서비스를 연동하여 자연어 처리 기능을 수행합니다.
- **설정 관리**: `config.py`에서 `.env` 파일의 환경 변수를 읽어와 데이터베이스, AI Provider, 서버 주소 등 애플리케이션의 모든 설정을 관리합니다.

## 주요 파일

- `run_server.py`: 서버 실행의 메인 진입점. `--mode` 인자에 따라 `http` 또는 `mcp` 서버를 실행합니다.
- `http_server.py`: FastAPI를 사용하여 구현된 HTTP 서버. RESTful API 엔드포인트를 정의합니다.
- `mcp_server.py`: MCP 프로토콜을 처리하는 TCP 소켓 기반 서버입니다.
- `database.py`: 데이터베이스 관련 모든 로직(연결, 쿼리, 스키마 조회)을 담당합니다.
- `config.py`: 환경 변수를 로드하고 애플리케이션 설정을 제공합니다.
- `env.example`: 서버 설정에 필요한 환경 변수 목록을 정의한 예제 파일입니다.

## 실행 방법

프로젝트 루트의 `run_cmd` 디렉토리에 있는 배치 파일을 사용하는 것을 권장합니다.

- **HTTP 서버 모드**:
  ```batch
  \run_cmd\1-1.run_http_server.bat
  ```
- **MCP 서버 모드**:
  ```batch
  \run_cmd\2-1.run_mcp_server.bat
  ```