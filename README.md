# MySQL Hub MCP Server

MySQL 데이터베이스와 자연어 쿼리를 지원하는 MCP(Model Context Protocol) 서버입니다. HTTP 기반 통신과 MCP stdio 프로토콜을 모두 지원합니다.

## 📋 목적

1. Cursor AI에서 MCP를 통해 MySQL DB서버에 연결
2. Cursor AI chat 창에서 MySQL에 자연어로 데이터를 검색
3. HTTP API를 통한 직접적인 데이터베이스 조작
4. 자연어를 SQL로 변환하는 AI 기반 쿼리 시스템

## 🏗️ 프로젝트 구조

```
mysql-hub-mcp/
├── client/                 # HTTP 기반 MCP 클라이언트 애플리케이션
│   ├── client_app.py      # httpx 기반 클라이언트 메인 애플리케이션
│   ├── run_client.py      # 클라이언트 실행 스크립트
│   └── pyproject.toml     # 클라이언트 의존성
├── server/                # MCP 서버 및 HTTP 서버
│   ├── server_app.py      # 서버 메인 애플리케이션
│   ├── mcp_server.py      # MCP 서버 구현
│   ├── http_server.py     # FastAPI 기반 HTTP API 서버
│   ├── database.py        # MySQL 데이터베이스 관리 (UTF-8 처리 포함)
│   ├── ai_provider.py     # AI Provider 관리 (Groq/Ollama)
│   ├── config.py          # 설정 관리
│   ├── run_server.py      # 서버 실행 스크립트
│   ├── env.example        # 환경 설정 예제
│   └── pyproject.toml     # 서버 의존성
├── bridge/                # Cursor MCP Bridge
│   ├── mcp_bridge.py      # Cursor Bridge 구현
│   └── pyproject.toml     # Bridge 의존성
├── docs/                  # 문서
│   └── requirement.md     # 요구사항 문서
├── pyproject.toml         # 프로젝트 루트 설정
└── README.md             # 프로젝트 설명서
```

## 🚀 설치 및 설정

### 1. 의존성 설치

각 컴포넌트별로 의존성을 설치합니다:

```bash
# 서버 의존성 설치
cd server
uv sync

# 클라이언트 의존성 설치
cd ../client
uv sync

# Bridge 의존성 설치
cd ../bridge
uv sync
```

### 2. 환경 설정

서버 디렉토리에 `.env` 파일을 생성하고 설정합니다:

```bash
cd server
cp env.example .env
```

`.env` 파일을 편집하여 다음 설정을 구성합니다:

```env
# MySQL 데이터베이스 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=devuser
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=devdb

# AI Provider 설정 (groq 또는 ollama)
AI_PROVIDER=ollama

# Groq 설정
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192

# Ollama 설정
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# 로깅 설정
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# 서버 설정
SERVER_HOST=localhost
SERVER_PORT=8000
```

## 🎯 사용법

### 1. 서버 실행

#### HTTP 서버만 실행 (권장)
```bash
cd server
uv run run_server.py --mode http
```

#### HTTP 서버와 MCP 서버 동시 실행
```bash
cd server
uv run run_server.py
```

#### MCP 서버만 실행
```bash
cd server
uv run run_server.py --mode mcp
```

### 2. 클라이언트 실행

#### 대화형 모드 (기본값)
```bash
cd client
uv run run_client.py
```

#### 배치 모드 - 자연어 쿼리
```bash
cd client
uv run run_client.py --tool natural_language_query --question "사용자 테이블에서 모든 데이터를 조회해주세요"
```

#### 배치 모드 - SQL 실행
```bash
cd client
uv run run_client.py --tool execute_sql --query "SELECT * FROM users"
```

#### 도구 목록 확인
```bash
cd client
uv run run_client.py --list-tools
```

### 3. Bridge 실행 (테스트용)

```bash
cd bridge
uv run mcp_bridge.py --question "사용자 테이블에서 모든 데이터를 조회해주세요"
```

## 🔧 제공되는 도구

### 1. execute_sql
- **설명**: MySQL 데이터베이스에서 SQL 쿼리를 실행합니다.
- **매개변수**: `query` (실행할 SQL 쿼리)
- **예시**: `SELECT * FROM users WHERE user_name = '홍길동'`

### 2. natural_language_query
- **설명**: 자연어를 SQL 쿼리로 변환하여 실행합니다.
- **매개변수**: `question` (자연어로 된 질문)
- **예시**: 
  - "노트북을 주문한 사용자의 이름과 이메일을 조회해주세요"
  - "가장 많이 주문한 사용자를 찾아주세요"
  - "각 사용자별로 주문한 상품과 금액을 보여주세요"

### 3. get_database_info
- **설명**: 데이터베이스 정보와 테이블 목록을 반환합니다.
- **매개변수**: 없음

### 4. get_table_schema
- **설명**: 특정 테이블의 스키마 정보를 반환합니다.
- **매개변수**: `table_name` (테이블 이름)

## 🌐 HTTP API

서버가 실행되면 다음 HTTP API를 사용할 수 있습니다:

### 기본 엔드포인트
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크

### 데이터베이스 엔드포인트
- `GET /database/info` - 데이터베이스 정보
- `POST /database/execute` - SQL 쿼리 실행
- `POST /database/natural-query` - 자연어 쿼리 실행
- `GET /database/tables` - 테이블 목록
- `POST /database/table-schema` - 테이블 스키마

### AI Provider 엔드포인트
- `GET /ai/provider` - 현재 AI Provider 정보
- `POST /ai/switch-provider` - AI Provider 전환

## 🤖 AI Provider

### Groq
- **특징**: 빠른 응답 속도, 클라우드 기반
- **설정**: `AI_PROVIDER=groq`
- **필요**: API 키 설정

### Ollama
- **특징**: 로컬 실행 가능, 오프라인 사용 가능
- **설정**: `AI_PROVIDER=ollama`
- **필요**: Ollama 서버 실행 (기본: http://localhost:11434)

## 📊 실제 테스트 결과

### 성공적인 자연어 쿼리 예시

```bash
# 기본 조회
질문: "사용자 테이블에서 모든 데이터를 조회해주세요"
생성된 SQL: SELECT * FROM users;
결과: 3명의 사용자 정보 (홍길동, 이순신, 세종대왕)

# 조건부 조회
질문: "노트북을 주문한 사용자의 이름과 이메일을 조회해주세요"
생성된 SQL: SELECT DISTINCT u.user_name, u.email FROM users u JOIN orders o ON u.id = o.user_id WHERE o.product_name = '노트북';
결과: 노트북을 주문한 사용자 정보

# 복잡한 JOIN 쿼리
질문: "가장 비싼 상품을 주문한 사용자의 이름과 상품명을 조회해주세요"
생성된 SQL: SELECT u.user_name, o.product_name FROM orders o JOIN users u ON o.user_id = u.id WHERE o.amount = (SELECT MAX(amount) FROM orders);
결과: 최고가 주문 정보
```

## 🛡️ 오류 처리 및 안정성

### UTF-8 인코딩 처리
- 바이너리 데이터를 16진수 문자열로 자동 변환
- 제어 문자 자동 제거
- 마크다운 코드 블록 자동 제거

### AI 응답 검증
- 오류 메시지 감지 및 차단
- SQL 키워드 검증
- 타임아웃 처리 (60초)

### 데이터베이스 연결
- 연결 풀링 및 자동 재연결
- UTF-8 인코딩 강제 설정
- 쿼리 유효성 검사

## 📝 로깅

로그는 다음 위치에 저장됩니다:
- 콘솔 출력
- `logs/server-YYYYMMDD.log` (서버 로그)
- `logs/client-YYYYMMDD.log` (클라이언트 로그)

### 로그 파일 특징
- **날짜별 분리**: 매일 새로운 로그 파일 생성
- **UTF-8 인코딩**: 한글 로그가 깨지지 않음
- **자동 디렉토리 생성**: logs 폴더가 없으면 자동 생성

로그 레벨은 환경 변수 `LOG_LEVEL`로 설정할 수 있습니다:
- DEBUG: 상세한 디버깅 정보
- INFO: 일반적인 정보 (기본값)
- WARNING: 경고 메시지
- ERROR: 오류 메시지

## 🔗 Cursor AI 연동

Cursor AI에서 이 MCP 서버를 사용하려면:

1. Cursor AI 설정에서 MCP 서버를 추가
2. 서버 경로: `python /path/to/mysql-hub-mcp/server/run_server.py --mode mcp`
3. Cursor AI chat에서 자연어로 데이터베이스 질문 가능

## 🛠️ 개발 환경

- **개발도구**: Cursor IDE
- **개발언어**: Python 3.10+
- **패키지 관리**: uv
- **웹 프레임워크**: FastAPI
- **HTTP 클라이언트**: httpx
- **데이터베이스**: MySQL + SQLAlchemy
- **AI 통합**: Groq API, Ollama
- **대화 언어**: 한국어 (보조적으로 영어 사용 가능)

## 🔧 주요 기술 스택

- **백엔드**: FastAPI, SQLAlchemy, PyMySQL
- **AI/ML**: Groq API, Ollama
- **통신**: HTTP/HTTPS, MCP Protocol
- **로깅**: Python logging
- **UI**: Rich (터미널 UI)
- **설정**: python-dotenv

## 📚 참고 문서

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18/server)
- [MCP Quickstart](https://modelcontextprotocol.io/quickstart/server)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## 🤝 기여

이 프로젝트는 학습 목적으로 개발되었습니다. 개선 사항이나 버그 리포트는 언제든 환영합니다.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
