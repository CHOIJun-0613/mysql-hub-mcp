# MySQL Hub MCP

MySQL, PostgreSQL, Oracle 데이터베이스와 자연어 쿼리를 지원하는 MCP 서버입니다.

## 기능

- **다중 데이터베이스 지원**: MySQL, PostgreSQL, Oracle
- 데이터베이스 연결 및 쿼리 실행
- 자연어를 SQL로 변환
- AI Provider 지원 (Groq, Ollama, LM Studio)
- Tool 지원 LLM을 통한 지능형 데이터베이스 쿼리

## 설치 및 설정

### 1. 환경 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# 데이터베이스 타입 선택 (mysql, postgresql, oracle)
DATABASE_TYPE=mysql

# MySQL 데이터베이스 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

# PostgreSQL 데이터베이스 설정
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_DATABASE=your_database

# Oracle 데이터베이스 설정
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_USER=system
ORACLE_PASSWORD=your_password
ORACLE_SERVICE_NAME=XE
# ORACLE_SID=XE  # SID를 사용하는 경우 주석 해제

# AI Provider 설정 (groq, ollama, lmstudio)
AI_PROVIDER=ollama

# Groq 설정
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192

# LM Studio 설정
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=qwen/qwen3-8b

# Ollama 설정
# Tool 지원 모델: qwen2.5-coder, llama3.1:8b, codellama:7b 등
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder

# 로깅 설정
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# 서버 설정
SERVER_HOST=localhost
SERVER_PORT=8000
```

### 2. 의존성 설치

```bash
# 서버 의존성 설치
cd app_mcp_server
pip install -r requirements.txt

# 클라이언트 의존성 설치
cd ../app_client
pip install -r requirements.txt
```

#### 데이터베이스별 추가 패키지

**PostgreSQL 사용 시:**
```bash
pip install psycopg2-binary
```

**Oracle 사용 시:**
```bash
pip install cx-Oracle
```
**주의**: Oracle 클라이언트 라이브러리가 시스템에 설치되어 있어야 합니다.

### 3. AI Provider 설정

#### LM Studio 설정 (권장)

**LM Studio 설치 및 실행:**
1. [LM Studio 공식 사이트](https://lmstudio.ai/)에서 다운로드
2. LM Studio 실행 후 "qwen/qwen3-8b" 모델 다운로드
3. 모델 실행 (Local Server 탭에서 Start Server 클릭)
4. 기본 포트는 1234이며, API는 `http://localhost:1234/v1`에서 접근 가능

**환경 변수 설정:**
```env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=qwen/qwen3-8b
```

**연결 테스트:**
```bash
# 사용 가능한 모델 확인
curl http://localhost:1234/v1/models

# 간단한 쿼리 테스트
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3-8b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

#### Ollama Tool 지원 모델 설정

**qwen2.5-coder 모델 사용:**
```bash
# qwen2.5-coder 모델 다운로드
ollama pull qwen2.5-coder

# 모델 실행 테스트
ollama run qwen2.5-coder "Hello, can you help me with coding?"
```

**다른 Tool 지원 모델들:**
- `llama3.1:8b` - Meta의 최신 Llama 모델
- `codellama:7b` - 코드 생성에 특화된 모델
- `deepseek-coder:6.7b` - 코드 이해에 강점이 있는 모델

**Tool 지원 확인:**
```bash
# 모델이 tool을 지원하는지 확인
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder",
    "messages": [{"role": "user", "content": "Hello"}],
    "tools": [{"type": "function", "function": {"name": "test", "description": "test"}}]
  }'
```

#### Groq 설정

**API 키 설정:**
```env
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3-32b
```

## 사용법

### 1. 서버 실행

```bash
# 서버 실행
cd server
python run_server.py

# 또는 HTTP 서버만 실행
python run_http_server.py
```

### 2. HTTP API를 통한 Tool 지원 쿼리

**자연어 쿼리 (Tool 지원):**
```bash
curl -X POST http://localhost:8000/database/natural-query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "사용자 테이블의 모든 데이터를 보여줘"
  }'
```

**데이터베이스 정보 조회:**
```bash
curl http://localhost:8000/database/info
```

**테이블 스키마 조회:**
```bash
curl -X POST http://localhost:8000/database/table-schema \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "users"
  }'
```

**직접 SQL 실행:**
```bash
curl -X POST http://localhost:8000/database/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users LIMIT 5"
  }'
```

### 3. Tool 지원 기능

HTTP API는 다음과 같은 tool들을 지원합니다:

1. **get_database_info**: 데이터베이스 정보와 테이블 목록 조회
2. **get_table_schema**: 특정 테이블의 스키마 정보 조회  
3. **execute_sql**: SQL 쿼리 실행

AI 모델이 자연어 질문을 분석하여 필요한 tool을 순차적으로 호출하여 답변을 생성합니다.

### 4. 클라이언트 실행

```bash
# 웹 클라이언트 실행
cd client
python run_web_client.py

# 또는 일반 클라이언트 실행
python run_client.py
```

## API 엔드포인트

### 데이터베이스 관련
- `GET /database/info` - 데이터베이스 정보 조회
- `GET /database/tables` - 테이블 목록 조회
- `POST /database/table-schema` - 테이블 스키마 조회
- `POST /database/execute` - SQL 쿼리 실행
- `POST /database/natural-query` - 자연어 쿼리 (Tool 지원)

### AI Provider 관련
- `GET /ai/provider` - 현재 AI Provider 정보
- `POST /ai/switch-provider` - AI Provider 전환

### 시스템
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크

## 로깅

로그는 `server/logs/` 디렉토리에 저장됩니다. 로그 레벨은 `.env` 파일의 `LOG_LEVEL`로 설정할 수 있습니다.

## 문제 해결

### Tool 지원이 작동하지 않는 경우

#### LM Studio 문제 해결

1. **LM Studio 서버 상태 확인:**
   ```bash
   curl http://localhost:1234/v1/models
   ```

2. **모델 실행 상태 확인:**
   - LM Studio에서 Local Server 탭 확인
   - 모델이 실행 중인지 확인
   - 포트 1234가 사용 가능한지 확인

3. **환경 변수 확인:**
   ```env
   AI_PROVIDER=lmstudio
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LMSTUDIO_MODEL=qwen/qwen3-8b
   ```

#### Ollama 문제 해결

1. **Ollama 모델 확인:**
   ```bash
   ollama list
   ```

2. **Tool 지원 테스트:**
   ```bash
   curl -X POST http://localhost:11434/api/chat \
     -H "Content-Type: application/json" \
     -d '{
       "model": "qwen2.5-coder",
       "messages": [{"role": "user", "content": "Hello"}],
       "tools": [{"type": "function", "function": {"name": "test", "description": "test"}}]
     }'
   ```

3. **로그 확인:**
   ```bash
   tail -f server/logs/server.log
   ```

### 데이터베이스 연결 오류

1. MySQL 서비스가 실행 중인지 확인
2. `.env` 파일의 데이터베이스 설정 확인
3. 사용자 권한 확인

### AI Provider 전환

**Provider 전환 API 사용:**
```bash
# LM Studio로 전환
curl -X POST http://localhost:8000/ai/switch-provider \
  -H "Content-Type: application/json" \
  -d '{"provider": "lmstudio"}'

# Ollama로 전환
curl -X POST http://localhost:8000/ai/switch-provider \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama"}'

# Groq로 전환
curl -X POST http://localhost:8000/ai/switch-provider \
  -H "Content-Type: application/json" \
  -d '{"provider": "groq"}'
```

**현재 Provider 확인:**
```bash
curl http://localhost:8000/ai/provider
```

## 라이선스

MIT License
