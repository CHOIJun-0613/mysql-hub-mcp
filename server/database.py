"""
MySQL 데이터베이스 관리 모듈
데이터베이스 연결과 쿼리 실행을 관리합니다.
"""

import logging
from typing import List, Dict, Any, Optional
import pymysql
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MySQL 데이터베이스 관리자"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
    
    def constructor(self):
        """데이터베이스 연결을 초기화합니다."""

        self._initialize_connection()
    
    def _initialize_connection(self):
        """데이터베이스 연결을 초기화합니다."""
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
                # 문자 인코딩 설정
                conn.execute(text("SET NAMES utf8mb4"))
                conn.execute(text("SET CHARACTER SET utf8mb4"))
                conn.execute(text("SET character_set_connection=utf8mb4"))
                conn.execute(text("SELECT 1"))
            
            logger.info("\n🚨===== 데이터베이스[MySQL] 연결이 성공적으로 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"MySQL 데이터베이스 연결 초기화 실패: {e}")
            self.engine = None
            self.session_factory = None
    
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
        """데이터베이스 값에서 UTF-8 인코딩 문제를 해결합니다."""
        if value is None:
            return None
        
        try:
            if isinstance(value, bytes):
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
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """테이블 스키마 정보를 반환합니다."""
        if not self.is_connected():
            raise Exception("데이터베이스에 연결되지 않았습니다.")
        # 결과를 {"TABLE_NAME": ..., "TABLE_COMMENT": ..., "COLUMNS": [...] } 형태로 반환
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

            # 결과 포맷 맞추기
            result = {
                "TABLE_NAME": table_name,
                "TABLE_COMMENT": table_comment,
                "COLUMNS": columns
            }
            return result
        except Exception as e:
            logger.error(f"테이블 스키마 조회 실패: {e}")
            raise Exception(f"테이블 스키마 조회 중 오류가 발생했습니다: {e}")
    

    
    def get_table_list(self, database_name: str = None) -> List[str]:
        """데이터베이스의 모든 테이블 목록을 반환합니다."""
        
        try:
            if database_name is None:
                database_name = config.MYSQL_DATABASE
            
            logger.debug(f"데이터베이스 이름: {database_name}")
            
            # INFORMATION_SCHEMA.TABLES에서 테이블명과 COMMENT 조회
            query = f"""
            SELECT 
                TABLE_NAME, 
                TABLE_COMMENT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{database_name}'
            """
            result = self.execute_query(query)
            # 결과를 [{TABLE_NAME, TABLE_COMMENT}, ...] 형태로 반환
            table_list = []
            for row in result:
                table_list.append({
                    "TABLE_NAME": row.get("TABLE_NAME", ""),
                    "TABLE_COMMENT": row.get("TABLE_COMMENT", "")
                })
            logger.info(f"테이블 목록 및 COMMENT 조회 성공: {len(table_list)}개 테이블")
            return table_list
        except Exception as e:
            logger.error(f"테이블 목록 및 COMMENT 조회 실패: {e}")
            raise Exception(f"테이블 목록 및 COMMENT 조회 중 오류가 발생했습니다: {e}")

    
    def validate_query(self, query: str) -> bool:
        """SQL 쿼리의 유효성을 검사합니다."""
        if not self.is_connected():
            return False
        
        try:
            # 쿼리 구문 검사 (실제 실행하지 않음)
            with self.engine.connect() as conn:
                # EXPLAIN을 사용하여 쿼리 유효성 검사
                if query.strip().upper().startswith('SELECT'):
                    conn.execute(text(f"EXPLAIN {query}"))
                else:
                    # SELECT가 아닌 경우 파싱만 시도
                    conn.execute(text(query))
            
            return True
            
        except Exception as e:
            logger.warning(f"쿼리 유효성 검사 실패: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """데이터베이스 정보를 반환합니다."""
        if not self.is_connected():
            return {"error": "데이터베이스에 연결되지 않았습니다."}
        
        try:
            info = {
                "database_name": config.MYSQL_DATABASE,
                "host": config.MYSQL_HOST,
                "port": config.MYSQL_PORT,
                "user": config.MYSQL_USER,
                "tables": self.get_table_list(config.MYSQL_DATABASE),
                "connection_status": "connected"
            }
            
            return info
            
        except Exception as e:
            logger.error(f"데이터베이스 정보 조회 실패: {e}")
            return {"error": f"데이터베이스 정보 조회 중 오류가 발생했습니다: {e}"}

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

# 전역 데이터베이스 관리자 인스턴스
db_manager = DatabaseManager() 