# FastMCP SSE 서버 엔드포인트 가이드

## 🌐 서버 접속 정보

### 기본 설정
- **프로토콜**: HTTP/HTTPS
- **통신 방식**: SSE (Server-Sent Events)
- **기본 포트**: 8000 (환경변수 SSE_PORT로 변경 가능)

### 환경변수 설정
```bash
# .env 파일
SSE_URL=localhost      # 또는 0.0.0.0 (모든 인터페이스)
SSE_PORT=8001         # 원하는 포트 번호
```

## 📡 MCP 프로토콜 엔드포인트

### 1. **MCP 통신 엔드포인트**
```
http://localhost:8000/mcp
```
- **용도**: MCP 프로토콜을 통한 클라이언트-서버 통신
- **방식**: Server-Sent Events (SSE)
- **프로토콜**: MCP (Model Context Protocol)

### 2. **도구 목록 조회**
```
http://localhost:8000/tools
```
- **용도**: 사용 가능한 MCP 도구 목록 확인
- **응답**: JSON 형태의 도구 정보

### 3. **서버 상태 확인**
```
http://localhost:8000/health
```
- **용도**: 서버 상태 및 헬스 체크
- **응답**: 서버 상태 정보

## 🛠️ 사용 가능한 MCP 도구

### 1. **get_database_info()**
- **기능**: 데이터베이스 정보 및 연결 상태 조회
- **매개변수**: 없음
- **반환값**: 데이터베이스 정보 (연결 상태, 데이터베이스명, 테이블 수 등)

### 2. **get_table_list()**
- **기능**: 데이터베이스의 모든 테이블 목록 조회
- **매개변수**: 없음
- **반환값**: 테이블 이름 목록

### 3. **get_table_schema(table_name)**
- **기능**: 특정 테이블의 스키마 정보 조회
- **매개변수**: `table_name` (테이블 이름)
- **반환값**: 테이블 스키마 정보 (컬럼명, 타입, 제약조건 등)

### 4. **execute_sql(sql)**
- **기능**: SQL 쿼리 직접 실행
- **매개변수**: `sql` (실행할 SQL 쿼리)
- **반환값**: 쿼리 실행 결과 (데이터, 행 수, 실행 시간 등)

### 5. **natural_language_query(query)**
- **기능**: 자연어를 SQL로 변환하여 실행
- **매개변수**: `query` (자연어로 된 쿼리)
- **반환값**: 쿼리 실행 결과

## 📱 클라이언트 접속 방법

### 1. **MCP 클라이언트 접속**
```bash
# MCP 프로토콜을 지원하는 클라이언트
mcp://localhost:8000/mcp
```

### 2. **웹 브라우저에서 확인**
```bash
# 도구 목록 확인
curl http://localhost:8000/tools

# 서버 상태 확인
curl http://localhost:8000/health
```

### 3. **Cursor IDE에서 사용**
```json
// Cursor 설정 파일
{
  "mcpServers": {
    "mysql-hub": {
      "command": "python",
      "args": ["-m", "mcp.server.fastmcp", "sse"],
      "env": {
        "SSE_URL": "localhost",
        "SSE_PORT": "8000"
      }
    }
  }
}
```

## 🔧 서버 실행 방법

### 1. **직접 실행**
```bash
cd server
python mcp_server.py
```

### 2. **환경변수와 함께 실행**
```bash
SSE_URL=0.0.0.0 SSE_PORT=8001 python mcp_server.py
```

### 3. **Docker로 실행**
```dockerfile
# Dockerfile 예시
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "mcp_server.py"]
```

## 📊 로그 확인

### 서버 시작 시 로그
```
🔗 MCP SSE 서버 엔드포인트 정보
============================================================
🌐 서버 URL: http://localhost:8000
📡 MCP 프로토콜 엔드포인트:
   • /mcp - MCP 프로토콜 통신
   • /tools - 사용 가능한 도구 목록
   • /health - 서버 상태 확인

🛠️  사용 가능한 도구:
   • get_database_info() - 데이터베이스 정보 조회
   • get_table_list() - 테이블 목록 조회
   • get_table_schema(table_name) - 테이블 스키마 조회
   • execute_sql(sql) - SQL 쿼리 실행
   • natural_language_query(query) - 자연어 쿼리

📱 클라이언트 접속 방법:
   • MCP 클라이언트: http://localhost:8000/mcp
   • 웹 브라우저: http://localhost:8000/tools
============================================================
```

## 🚨 문제 해결

### 1. **포트 충돌**
```bash
# 포트 사용 중인 프로세스 확인
netstat -tulpn | grep :8000

# 다른 포트로 변경
SSE_PORT=8001 python mcp_server.py
```

### 2. **접속 불가**
```bash
# 방화벽 설정 확인
# Windows: Windows Defender 방화벽
# Linux: ufw 또는 iptables
# macOS: 시스템 환경설정 > 보안 및 개인정보보호
```

### 3. **권한 문제**
```bash
# 관리자 권한으로 실행
sudo python mcp_server.py

# 또는 포트 1024 이상 사용
SSE_PORT=8000 python mcp_server.py
```

## 📚 추가 리소스

- [MCP 프로토콜 공식 문서](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MySQL Hub MCP 프로젝트](../README.md)
