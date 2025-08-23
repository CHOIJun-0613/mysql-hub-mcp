"""
다중 데이터베이스 관리 모듈
MySQL, PostgreSQL, Oracle 데이터베이스 연결과 쿼리 실행을 관리합니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pymysql
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import config

logger = logging.getLogger(__name__)

class DatabaseProvider(ABC):
    """데이터베이스 Provider 추상 클래스"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
    
    @abstractmethod
    def _initialize_connection(self):
        """데이터베이스 연결을 초기화합니다."""
        pass
    
    @abstractmethod
    def _setup_connection(self, conn):
        """데이터베이스별 연결 설정을 수행합니다."""
        pass
    
    @abstractmethod
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """테이블 스키마 정보를 반환합니다."""
        pass
    
    @abstractmethod
    def get_table_list(self, database_name: str = None) -> List[Dict[str, str]]:
        """데이터베이스의 모든 테이블 목록을 반환합니다."""
        pass
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """데이터베이스 정보를 반환합니다."""
        pass
    
    def constructor(self):
        """데이터베이스 연결을 초기화합니다."""
        self._initialize_connection()
    
    def is_connected(self) -> bool:
        """데이터베이스 연결 상태를 확인합니다."""
        return self.engine is not None
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """SQL 쿼리를 실행하고 결과를 반환합니다."""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # 결과를 딕셔너리 리스트로 변환
                columns = result.keys()
                rows = []
                
                for row in result.fetchall():
                    # 각 행의 데이터를 UTF-8로 정리
                    cleaned_row = {}
                    for col, value in zip(columns, row):
                        cleaned_row[col] = self._clean_value(value)
                    rows.append(cleaned_row)
                
                # 1~100번째 행만 출력, 101번째는 '...' 출력
                logger.debug("쿼리 실행 결과: \n")
                max_log_rows = 100
                for idx, row in enumerate(rows):
                    if idx < max_log_rows:
                        if(idx < len(rows) - 1):
                            logger.debug(f"[{idx+1:03}] {row}")
                        else:
                            logger.debug(f"[{idx+1:03}] {row}\n")
                    elif idx == max_log_rows:
                        logger.debug(f"[{idx+1:03}] ...(이하 생략)\n")
                        break
                
                logger.info(f"쿼리 실행 성공: {len(rows)}개 행 반환")
                return rows
                
        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            raise Exception(f"쿼리 실행 중 오류가 발생했습니다: {e}")
    
    def _clean_value(self, value):
        """데이터베이스 값에서 UTF-8 인코딩 문제와 Decimal 타입을 해결합니다."""
        if value is None:
            return None
        
        try:
            # Decimal 타입을 float로 변환
            from decimal import Decimal
            if isinstance(value, Decimal):
                return float(value)
            elif isinstance(value, bytes):
                # 바이너리 데이터를 16진수 문자열로 변환
                return value.hex()
            elif isinstance(value, str):
                # 문자열에서 문제 있는 문자 제거
                cleaned = value.encode('utf-8', errors='ignore').decode('utf-8')
                # 제어 문자 제거
                import re
                cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
                return cleaned
            else:
                # 다른 타입은 그대로 반환 (숫자, 날짜 등)
                return value
        except Exception as e:
            logger.warning(f"값 정리 중 오류: {e}, 원본 값: {value}")
            # 오류 발생 시 안전한 문자열로 변환
            try:
                return str(value).encode('ascii', errors='ignore').decode('ascii')
            except:
                return "[인코딩 오류]"
    
    def execute_non_query(self, query: str) -> int:
        """INSERT, UPDATE, DELETE 등의 쿼리를 실행합니다."""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                conn.commit()
                
                affected_rows = result.rowcount
                logger.info(f"쿼리 실행 성공: {affected_rows}개 행 영향")
                return affected_rows
                
        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            raise Exception(f"쿼리 실행 중 오류가 발생했습니다: {e}")
    
    def validate_query(self, query: str) -> bool:
        """SQL 쿼리의 유효성을 검사합니다."""
        if not self.is_connected():
            return False
        
        try:
            # 쿼리 구문 검사 (실제 실행하지 않음)
            with self.engine.connect() as conn:
                if query.strip().upper().startswith('SELECT'):
                    self._explain_query(conn, query)
                else:
                    conn.execute(text(query))
            
            return True
            
        except Exception as e:
            # 더 자세한 오류 정보 로깅
            error_msg = str(e)
            logger.warning(f"쿼리 유효성 검사 실패: {error_msg}")
            
            # 테이블명 관련 오류인지 확인
            if "syntax" in error_msg.lower() and "'" in query:
                # 테이블명에 작은따옴표가 잘못 사용된 경우
                logger.warning(f"테이블명에 작은따옴표가 잘못 사용됨: {query}")
            
            return False
    
    @abstractmethod
    def _explain_query(self, conn, query: str):
        """데이터베이스별 EXPLAIN 쿼리를 실행합니다."""
        pass
    
    def close_connection(self):
        """데이터베이스 연결을 안전하게 종료합니다."""
        try:
            if self.engine:
                # 모든 연결 풀의 연결을 정리
                self.engine.dispose()
                logger.info("데이터베이스 엔진이 정리되었습니다.")
            
            if self.session_factory:
                self.session_factory.close_all()
                logger.info("세션 팩토리가 정리되었습니다.")
            
            self.engine = None
            self.session_factory = None
            logger.info("데이터베이스 연결이 완전히 종료되었습니다.")
            
        except Exception as e:
            logger.error(f"데이터베이스 연결 종료 중 오류 발생: {e}")

class MySQLProvider(DatabaseProvider):
    """MySQL 데이터베이스 Provider"""
    
    def __init__(self):
        super().__init__()
        self.db_type = "mysql"
    
    def _initialize_connection(self):
        """MySQL 데이터베이스 연결을 초기화합니다."""
        try:
            # SQLAlchemy 엔진 생성
            self.engine = create_engine(
                config.get_mysql_url(),
                echo=False,  # SQL 로그 비활성화
                pool_pre_ping=True,  # 연결 상태 확인
                pool_recycle=3600  # 1시간마다 연결 재생성
            )
            
            # 세션 팩토리 생성
            self.session_factory = sessionmaker(bind=self.engine)
            
            # 연결 테스트 및 문자 인코딩 설정
            with self.engine.connect() as conn:
                self._setup_connection(conn)
                # 연결 테스트
                conn.execute(text("SELECT 1"))
            
            logger.info(f"\n🚨===== 데이터베이스[{self.db_type.upper()}] 연결이 성공적으로 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"{self.db_type.upper()} 데이터베이스 연결 초기화 실패: {e}")
            self.engine = None
            self.session_factory = None
    
    def _setup_connection(self, conn):
        """MySQL 연결 설정"""
        conn.execute(text("SET NAMES utf8mb4"))
        conn.execute(text("SET CHARACTER SET utf8mb4"))
        conn.execute(text("SET character_set_connection=utf8mb4"))
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """MySQL 테이블 스키마 조회"""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            # 테이블의 COMMENT(설명) 정보를 조회
            table_comment_query = f"""
            SELECT TABLE_COMMENT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{config.MYSQL_DATABASE}'
            AND TABLE_NAME = '{table_name}'
            """
            table_comment_result = self.execute_query(table_comment_query)
            if table_comment_result and isinstance(table_comment_result, list):
                table_comment = table_comment_result[0].get("TABLE_COMMENT", "")
            else:
                table_comment = ""

            # 컬럼 정보 조회
            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY,
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{config.MYSQL_DATABASE}' 
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            columns = self.execute_query(query)
            
            return {
                "TABLE_NAME": table_name,
                "TABLE_COMMENT": table_comment,
                "COLUMNS": columns
            }
        except Exception as e:
            logger.error(f"MySQL 테이블 스키마 조회 실패: {e}")
            raise Exception(f"테이블 스키마 조회 중 오류가 발생했습니다: {e}")
    
    def get_table_list(self, database_name: str = None) -> List[Dict[str, str]]:
        """MySQL 테이블 목록 조회"""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            if database_name is None:
                database_name = config.MYSQL_DATABASE
            
            logger.debug(f"데이터베이스 이름: {database_name}")
            
            query = f"""
            SELECT 
                TABLE_NAME, 
                TABLE_COMMENT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{database_name}'
            """
            result = self.execute_query(query)
            table_list = []
            for row in result:
                table_list.append({
                    "TABLE_NAME": row.get("TABLE_NAME", ""),
                    "TABLE_COMMENT": row.get("TABLE_COMMENT", "")
                })
            logger.info(f"MySQL 테이블 목록 조회 성공: {len(table_list)}개 테이블")
            return table_list
        except Exception as e:
            logger.error(f"MySQL 테이블 목록 조회 실패: {e}")
            raise Exception(f"테이블 목록 조회 중 오류가 발생했습니다: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """MySQL 데이터베이스 정보를 반환합니다."""
        if not self.is_connected():
            return {"error": "데이터베이스에 연결되지 않았습니다."}
        
        try:
            info = {
                "database_type": "MySQL",
                "database_name": config.MYSQL_DATABASE,
                "host": config.MYSQL_HOST,
                "port": config.MYSQL_PORT,
                "user": config.MYSQL_USER,
                "tables": self.get_table_list(config.MYSQL_DATABASE),
                "connection_status": "connected"
            }
            return info
        except Exception as e:
            logger.error(f"MySQL 데이터베이스 정보 조회 실패: {e}")
            return {"error": f"데이터베이스 정보 조회 중 오류가 발생했습니다: {e}"}
    
    def _explain_query(self, conn, query: str):
        """MySQL EXPLAIN 쿼리 실행"""
        conn.execute(text(f"EXPLAIN {query}"))

class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL 데이터베이스 Provider"""
    
    def __init__(self):
        super().__init__()
        self.db_type = "postgresql"
    
    def _initialize_connection(self):
        """PostgreSQL 데이터베이스 연결을 초기화합니다."""
        try:
            # SQLAlchemy 엔진 생성
            self.engine = create_engine(
                config.get_postgresql_url(),
                echo=False,  # SQL 로그 비활성화
                pool_pre_ping=True,  # 연결 상태 확인
                pool_recycle=3600  # 1시간마다 연결 재생성
            )
            
            # 세션 팩토리 생성
            self.session_factory = sessionmaker(bind=self.engine)
            
            # 연결 테스트
            with self.engine.connect() as conn:
                self._setup_connection(conn)
                # 연결 테스트
                conn.execute(text("SELECT 1"))
            
            logger.info(f"\n🚨===== 데이터베이스[{self.db_type.upper()}] 연결이 성공적으로 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"{self.db_type.upper()} 데이터베이스 연결 초기화 실패: {e}")
            self.engine = None
            self.session_factory = None
    
    def _setup_connection(self, conn):
        """PostgreSQL 연결 설정"""
        # PostgreSQL은 기본적으로 UTF-8을 지원하므로 추가 설정 불필요
        pass
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """PostgreSQL 테이블 스키마 조회"""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            # 테이블 설명 정보 조회
            table_comment_query = f"""
            SELECT obj_description(c.oid) as table_comment
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = '{table_name}' AND n.nspname = 'public'
            """
            table_comment_result = self.execute_query(table_comment_query)
            if table_comment_result and isinstance(table_comment_result, list):
                table_comment = table_comment_result[0].get("table_comment", "")
            else:
                table_comment = ""

            # 컬럼 정보 조회
            query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                CASE 
                    WHEN pk.column_name IS NOT NULL THEN 'PRI'
                    ELSE ''
                END as column_key,
                col_description(c.oid, cols.ordinal_position) as column_comment
            FROM information_schema.columns cols
            JOIN pg_class c ON c.relname = cols.table_name
            LEFT JOIN (
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = '{table_name}'
            ) pk ON cols.column_name = pk.column_name
            WHERE cols.table_name = '{table_name}'
            ORDER BY cols.ordinal_position
            """
            columns = self.execute_query(query)
            
            return {
                "TABLE_NAME": table_name,
                "TABLE_COMMENT": table_comment,
                "COLUMNS": columns
            }
        except Exception as e:
            logger.error(f"PostgreSQL 테이블 스키마 조회 실패: {e}")
            raise Exception(f"테이블 스키마 조회 중 오류가 발생했습니다: {e}")
    
    def get_table_list(self, database_name: str = None) -> List[Dict[str, str]]:
        """PostgreSQL 테이블 목록 조회"""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            logger.debug(f"PostgreSQL 테이블 목록 조회")
            
            query = """
            SELECT 
                tablename as table_name,
                obj_description(c.oid) as table_comment
            FROM pg_tables t
            JOIN pg_class c ON c.relname = t.tablename
            WHERE schemaname = 'public'
            """
            result = self.execute_query(query)
            table_list = []
            for row in result:
                table_list.append({
                    "TABLE_NAME": row.get("table_name", ""),
                    "TABLE_COMMENT": row.get("table_comment", "")
                })
            logger.info(f"PostgreSQL 테이블 목록 조회 성공: {len(table_list)}개 테이블")
            return table_list
        except Exception as e:
            logger.error(f"PostgreSQL 테이블 목록 조회 실패: {e}")
            raise Exception(f"테이블 목록 조회 중 오류가 발생했습니다: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """PostgreSQL 데이터베이스 정보를 반환합니다."""
        if not self.is_connected():
            return {"error": "데이터베이스에 연결되지 않았습니다."}
        
        try:
            info = {
                "database_type": "PostgreSQL",
                "database_name": config.POSTGRESQL_DATABASE,
                "host": config.POSTGRESQL_HOST,
                "port": config.POSTGRESQL_PORT,
                "user": config.POSTGRESQL_USER,
                "tables": self.get_table_list(),
                "connection_status": "connected"
            }
            return info
        except Exception as e:
            logger.error(f"PostgreSQL 데이터베이스 정보 조회 실패: {e}")
            return {"error": f"데이터베이스 정보 조회 중 오류가 발생했습니다: {e}"}
    
    def _explain_query(self, conn, query: str):
        """PostgreSQL EXPLAIN 쿼리 실행"""
        conn.execute(text(f"EXPLAIN {query}"))

class OracleProvider(DatabaseProvider):
    """Oracle 데이터베이스 Provider"""
    
    def __init__(self):
        super().__init__()
        self.db_type = "oracle"
    
    def _initialize_connection(self):
        """Oracle 데이터베이스 연결을 초기화합니다."""
        try:
            # SQLAlchemy 엔진 생성
            self.engine = create_engine(
                config.get_oracle_url(),
                echo=False,  # SQL 로그 비활성화
                pool_pre_ping=True,  # 연결 상태 확인
                pool_recycle=3600  # 1시간마다 연결 재생성
            )
            
            # 세션 팩토리 생성
            self.session_factory = sessionmaker(bind=self.engine)
            
            # 연결 테스트
            with self.engine.connect() as conn:
                self._setup_connection(conn)
                # 연결 테스트
                conn.execute(text("SELECT 1 FROM DUAL"))
            
            logger.info(f"\n🚨===== 데이터베이스[{self.db_type.upper()}] 연결이 성공적으로 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"{self.db_type.upper()} 데이터베이스 연결 초기화 실패: {e}")
            self.engine = None
            self.session_factory = None
    
    def _setup_connection(self, conn):
        """Oracle 연결 설정"""
        # Oracle은 기본적으로 UTF-8을 지원하므로 추가 설정 불필요
        pass
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Oracle 테이블 스키마 조회"""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            # 테이블 설명 정보 조회
            table_comment_query = f"""
            SELECT comments as table_comment
            FROM user_tab_comments
            WHERE table_name = '{table_name.upper()}'
            """
            table_comment_result = self.execute_query(table_comment_query)
            if table_comment_result and isinstance(table_comment_result, list):
                table_comment = table_comment_result[0].get("table_comment", "")
            else:
                table_comment = ""

            # 컬럼 정보 조회
            query = f"""
            SELECT 
                column_name,
                data_type,
                nullable as is_nullable,
                data_default as column_default,
                CASE 
                    WHEN pk.column_name IS NOT NULL THEN 'PRI'
                    ELSE ''
                END as column_key,
                comments as column_comment
            FROM user_tab_columns cols
            LEFT JOIN user_col_comments col_comments ON cols.table_name = col_comments.table_name AND cols.column_name = col_comments.column_name
            LEFT JOIN (
                SELECT cols.column_name
                FROM user_constraints cons
                JOIN user_cons_columns cols ON cons.constraint_name = cols.constraint_name
                WHERE cons.constraint_type = 'P' AND cons.table_name = '{table_name.upper()}'
            ) pk ON cols.column_name = pk.column_name
            WHERE cols.table_name = '{table_name.upper()}'
            ORDER BY cols.column_id
            """
            columns = self.execute_query(query)
            
            return {
                "TABLE_NAME": table_name,
                "TABLE_COMMENT": table_comment,
                "COLUMNS": columns
            }
        except Exception as e:
            logger.error(f"Oracle 테이블 스키마 조회 실패: {e}")
            raise Exception(f"테이블 스키마 조회 중 오류가 발생했습니다: {e}")
    
    def get_table_list(self, database_name: str = None) -> List[Dict[str, str]]:
        """Oracle 테이블 목록 조회"""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        
        try:
            logger.debug(f"Oracle 테이블 목록 조회")
            
            query = """
            SELECT 
                table_name,
                comments as table_comment
            FROM user_tab_comments
            WHERE table_type = 'TABLE'
            """
            result = self.execute_query(query)
            table_list = []
            for row in result:
                table_list.append({
                    "TABLE_NAME": row.get("table_name", ""),
                    "TABLE_COMMENT": row.get("table_comment", "")
                })
            logger.info(f"Oracle 테이블 목록 조회 성공: {len(table_list)}개 테이블")
            return table_list
        except Exception as e:
            logger.error(f"Oracle 테이블 목록 조회 실패: {e}")
            raise Exception(f"테이블 목록 조회 중 오류가 발생했습니다: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Oracle 데이터베이스 정보를 반환합니다."""
        if not self.is_connected():
            return {"error": "데이터베이스에 연결되지 않았습니다."}
        
        try:
            info = {
                "database_type": "Oracle",
                "database_name": config.ORACLE_SERVICE_NAME or config.ORACLE_SID,
                "host": config.ORACLE_HOST,
                "port": config.ORACLE_PORT,
                "user": config.ORACLE_USER,
                "tables": self.get_table_list(),
                "connection_status": "connected"
            }
            return info
        except Exception as e:
            logger.error(f"Oracle 데이터베이스 정보 조회 실패: {e}")
            return {"error": f"데이터베이스 정보 조회 중 오류가 발생했습니다: {e}"}
    
    def _explain_query(self, conn, query: str):
        """Oracle EXPLAIN PLAN 쿼리 실행"""
        conn.execute(text(f"EXPLAIN PLAN FOR {query}"))

class DatabaseManager:
    """다중 데이터베이스 관리자"""
    
    def __init__(self):
        self.provider = None
        # 생성자에서 자동 초기화하지 않음
    
    def constructor(self):
        """데이터베이스 연결을 초기화합니다. (기존 호환성을 위해 유지)"""
        self._initialize_provider()
    
    def _initialize_provider(self):
        """환경변수에 따라 적절한 데이터베이스 Provider를 초기화합니다."""
        try:
            db_type = config.DATABASE_TYPE.lower()
            
            if db_type == "mysql":
                self.provider = MySQLProvider()
            elif db_type == "postgresql":
                self.provider = PostgreSQLProvider()
            elif db_type == "oracle":
                self.provider = OracleProvider()
            else:
                raise ValueError(f"지원하지 않는 데이터베이스 타입: {db_type}")
            
            # Provider 초기화
            self.provider.constructor()
            logger.info(f"데이터베이스 Provider [{db_type.upper()}]가 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"데이터베이스 Provider 초기화 실패: {e}")
            self.provider = None
    
    def is_connected(self) -> bool:
        """데이터베이스 연결 상태를 확인합니다."""
        return self.provider is not None and self.provider.is_connected()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """SQL 쿼리를 실행하고 결과를 반환합니다."""
        if not self.provider:
            raise Exception("데이터베이스 Provider가 초기화되지 않았습니다.")
        return self.provider.execute_query(query)
    
    def execute_non_query(self, query: str) -> int:
        """INSERT, UPDATE, DELETE 등의 쿼리를 실행합니다."""
        if not self.provider:
            raise Exception("데이터베이스 Provider가 초기화되지 않았습니다.")
        return self.provider.execute_non_query(query)
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """테이블 스키마 정보를 반환합니다."""
        if not self.provider:
            raise Exception("데이터베이스 Provider가 초기화되지 않았습니다.")
        return self.provider.get_table_schema(table_name)
    
    def get_table_list(self, database_name: str = None) -> List[Dict[str, str]]:
        """데이터베이스의 모든 테이블 목록을 반환합니다."""
        if not self.provider:
            raise Exception("데이터베이스 Provider가 초기화되지 않았습니다.")
        return self.provider.get_table_list(database_name)
    
    def validate_query(self, query: str) -> bool:
        """SQL 쿼리의 유효성을 검사합니다."""
        if not self.provider:
            return False
        return self.provider.validate_query(query)
    
    def get_database_info(self) -> Dict[str, Any]:
        """데이터베이스 정보를 반환합니다."""
        if not self.provider:
            return {"error": "데이터베이스 Provider가 초기화되지 않았습니다."}
        return self.provider.get_database_info()
    
    def close_connection(self):
        """데이터베이스 연결을 안전하게 종료합니다."""
        if self.provider:
            self.provider.close_connection()

# 전역 데이터베이스 관리자 인스턴스
db_manager = DatabaseManager() 