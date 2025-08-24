"""
RAG 통합 모듈
벡터 DB에서 테이블 리스트와 스키마 정보를 검색합니다.
"""

import logging
import sys
import os
from typing import List, Dict, Any, Optional

# RAG 체인 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag_chain'))

try:
    from retrieve_test import setup_vector_db, search_table_schema
except ImportError as e:
    logging.error(f"RAG 모듈 임포트 실패: {e}")
    setup_vector_db = None
    search_table_schema = None

logger = logging.getLogger(__name__)

def get_tables_from_rag() -> List[Dict[str, str]]:
    """RAG를 통해 테이블 목록을 검색합니다."""
    try:
        if not setup_vector_db:
            raise Exception("RAG 모듈을 사용할 수 없습니다")
        
        vector_db, embedding_model = setup_vector_db()
        if not vector_db:
            raise Exception("벡터 DB를 초기화할 수 없습니다")
        
        # "테이블"로 검색하여 테이블 목록 생성
        query = "테이블"
        results = vector_db.similarity_search(query, k=20)
        
        tables = []
        seen_tables = set()
        
        for result in results:
            if result.metadata.get("source_type") == "table":
                table_name = result.metadata.get("table_name", "")
                if table_name and table_name not in seen_tables:
                    # 테이블 코멘트 추출
                    table_comment = result.page_content
                    if "설명:" in table_comment:
                        table_comment = table_comment.split("설명:")[1].strip()
                    
                    tables.append({
                        "table_name": table_name,
                        "table_comment": table_comment
                    })
                    seen_tables.add(table_name)
        
        logger.info(f"RAG에서 {len(tables)}개 테이블을 찾았습니다")
        return tables
        
    except Exception as e:
        logger.error(f"RAG 테이블 목록 조회 실패: {e}")
        return []

def get_schema_from_rag(table_name: str) -> Dict[str, Any]:
    """RAG를 통해 특정 테이블의 스키마를 검색합니다."""
    try:
        if not setup_vector_db or not search_table_schema:
            raise Exception("RAG 모듈을 사용할 수 없습니다")
        
        vector_db, embedding_model = setup_vector_db()
        if not vector_db:
            raise Exception("벡터 DB를 초기화할 수 없습니다")
        
        # 테이블 스키마 검색
        schema_result = search_table_schema(vector_db, table_name, k=20)
        
        if not schema_result["table_info"] and not schema_result["columns"]:
            return {"error": f"테이블 '{table_name}'을 찾을 수 없습니다"}
        
        # 스키마 정보 구성
        schema_info = {
            "table_name": table_name,
            "table_comment": "",
            "columns": [],
            "source": "RAG"
        }
        
        # 테이블 정보
        if schema_result["table_info"]:
            table_content = schema_result["table_info"].page_content
            if "설명:" in table_content:
                schema_info["table_comment"] = table_content.split("설명:")[1].strip()
        
        # 컬럼 정보
        if schema_result["columns"]:
            for col_doc in schema_result["columns"]:
                metadata = col_doc.metadata
                column_info = {
                    "column_name": metadata.get("column_name", ""),
                    "data_type": metadata.get("data_type", ""),
                    "is_nullable": metadata.get("is_nullable", "YES"),
                    "column_comment": col_doc.page_content,
                    "column_key": metadata.get("column_key", ""),
                    "extra": metadata.get("extra", "")
                }
                schema_info["columns"].append(column_info)
        
        logger.info(f"RAG에서 테이블 '{table_name}' 스키마를 찾았습니다")
        return schema_info
        
    except Exception as e:
        logger.error(f"RAG 스키마 조회 실패: {e}")
        return {"error": str(e), "source": "RAG"}
