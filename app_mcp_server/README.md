# MySQL Hub MCP Server

MySQL, PostgreSQL, Oracle을 지원하는 MCP (Model Context Protocol) 서버입니다.

## 🚀 주요 기능

- **다중 데이터베이스 지원**: MySQL, PostgreSQL, Oracle
- **MCP 프로토콜 지원**: HTTP 및 STDIO 연결
- **AI Provider 통합**: Groq, Ollama, LM Studio 지원
- **자연어 쿼리**: AI를 통한 SQL 쿼리 생성 및 실행

## 🗄️ 지원 데이터베이스

### 1. MySQL
- 기본 포트: 3306
- 드라이버: PyMySQL
- 특별 기능: UTF-8 인코딩 자동 설정

### 2. PostgreSQL
- 기본 포트: 5432
- 드라이버: psycopg2-binary
- 특별 기능: 네이티브 UTF-8 지원

### 3. Oracle
- 기본 포트: 1521
- 드라이버: cx-Oracle
- 특별 기능: SID 및 Service Name 지원

## ⚙️ 설정 방법

### 환경변수 설정

`.env` 파일을 생성하고 다음 설정을 추가하세요:

```env
# 데이터베이스 타입 선택 (mysql, postgresql, oracle)
DATABASE_TYPE=mysql

# MySQL 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=devuser
MYSQL_PASSWORD=devpass
MYSQL_DATABASE=devdb

# PostgreSQL 설정
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=devpass
POSTGRESQL_DATABASE=devdb

# Oracle 설정
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_USER=system
ORACLE_PASSWORD=devpass
ORACLE_SERVICE_NAME=XE
# ORACLE_SID=XE  # SID를 사용하는 경우 주석 해제
```

### 데이터베이스 전환

환경변수 `DATABASE_TYPE`만 변경하면 다른 데이터베이스로 전환할 수 있습니다:

```bash
# MySQL 사용
export DATABASE_TYPE=mysql

# PostgreSQL 사용
export DATABASE_TYPE=postgresql

# Oracle 사용
export DATABASE_TYPE=oracle
```

## 📦 설치

### 필수 패키지

```bash
pip install -r requirements.txt
```

### 데이터베이스별 추가 설치

#### PostgreSQL
```bash
pip install psycopg2-binary
```

#### Oracle
```bash
pip install cx-Oracle
```

**주의**: Oracle 클라이언트 라이브러리가 시스템에 설치되어 있어야 합니다.

## 🚀 실행

### HTTP 서버 실행
```bash
python run_server.py
```

### MCP 서버 실행
```bash
python mcp_server.py
```

## 🔧 주요 클래스

### DatabaseManager
- 데이터베이스 연결 관리
- 쿼리 실행 및 결과 처리
- 테이블 스키마 조회
- 데이터베이스별 메타데이터 조회

### Config
- 환경변수 기반 설정 관리
- 데이터베이스별 연결 URL 생성
- 다중 데이터베이스 설정 통합 관리

## 📊 데이터베이스별 메타데이터 조회

### MySQL
- `INFORMATION_SCHEMA.TABLES` 사용
- `INFORMATION_SCHEMA.COLUMNS` 사용

### PostgreSQL
- `pg_tables`, `pg_class` 사용
- `information_schema.columns` 사용

### Oracle
- `user_tab_comments` 사용
- `user_tab_columns` 사용

## 🛠️ 개발 가이드

### 새로운 데이터베이스 추가

1. `config.py`에 설정 추가
2. `database.py`에 데이터베이스별 메서드 구현
3. `requirements.txt`에 드라이버 패키지 추가
4. `env.example`에 환경변수 예시 추가

## 📝 로그

- 로그 레벨: `LOG_LEVEL` 환경변수로 설정
- 로그 파일: `logs/server-YYYYMMDD.log`
- 콘솔 출력: 기본 활성화

## 🤝 기여하기

1. 이슈 등록 또는 기능 요청
2. 포크 후 기능 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
