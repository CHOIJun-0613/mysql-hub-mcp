# MySQL Hub MCP

MySQL 데이터베이스와 자연어 쿼리를 지원하는 MCP 서버입니다.

## 기능

- MySQL 데이터베이스 연결 및 쿼리 실행
- 자연어를 SQL로 변환
- AI Provider 지원 (Groq, Ollama)
- Tool 지원 LLM을 통한 지능형 데이터베이스 쿼리

## 설치 및 설정

### 1. 환경 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# MySQL 데이터베이스 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

# AI Provider 설정 (groq 또는 ollama)
AI_PROVIDER=ollama

# Groq 설정
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192

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
cd server
pip install -r requirements.txt

# 클라이언트 의존성 설치
cd ../client
pip install -r requirements.txt
```

### 3. Ollama Tool 지원 모델 설정

**qwen2.5-coder 모델 사용 (권장):**
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

## 라이선스

MIT License
