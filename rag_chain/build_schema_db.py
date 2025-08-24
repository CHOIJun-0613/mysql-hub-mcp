import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import traceback
import requests
import json
from typing import List, Dict, Any

# --- 1. 스키마 파일 목록 정의 ---
# 처리할 스키마 파일들의 리스트
SCHEMA_FILES = [
    'docs/sql/table_schemas/devdb.STND_TERM.sql',
    'docs/sql/table_schemas/devdb.STND_WORD.sql',
    'docs/sql/table_schemas/devdb.ORDERS.sql',
    'docs/sql/table_schemas/devdb.USERS.sql'
]

# --- 2. 파일 목록에서 스키마를 읽어오는 함수 ---
def load_schemas_from_files(file_list):
    """지정된 파일 목록을 읽어 각 파일의 내용을 리스트로 반환합니다."""
    schemas = []
    for filename in file_list:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                schemas.append(f.read())
            print(f"✅ Successfully loaded: {filename}")
        except FileNotFoundError:
            print(f"❌ ERROR: File not found - {filename}")
        except Exception as e:
            print(f"❌ ERROR: Failed to read {filename} - {e}")
    return schemas

# --- 3. 스키마를 의미 단위(Document)로 파싱하는 클래스 ---
class SchemaParser:
    """SQL 스키마를 파싱하여 Document로 변환하는 클래스"""
    
    def parse_schema_to_documents(self, sql_schemas):
        documents = []
        for schema in sql_schemas:
            try:
                # 간단한 파싱을 위해 줄 단위로 분리
                lines = [line.strip() for line in schema.strip().split('\n') if line.strip()]
                
                table_name = ""
                table_comment = ""

                for line in lines:
                    if line.upper().startswith("CREATE TABLE"):
                        table_name = line.split()[2].split('(')[0] # 테이블 이름 파싱 개선
                        break
                
                if not table_name: continue

                # 테이블 설명 찾기
                for line in lines:
                    if line.upper().startswith(f"COMMENT ON TABLE {table_name}"):
                        table_comment = line.split("IS")[1].strip().replace("'", "").replace(";", "")
                        break
                    # 따옴표가 있는 경우도 처리
                    elif line.upper().startswith(f'COMMENT ON TABLE "{table_name}"'):
                        table_comment = line.split("IS")[1].strip().replace("'", "").replace(";", "")
                        break
                
                # 테이블 설명이 없으면 기본 설명 생성
                if not table_comment:
                    # 테이블명을 기반으로 기본 설명 생성
                    clean_table_name = table_name.replace('"', '').replace("'", "")
                    if clean_table_name.upper() == "ORDERS":
                        table_comment = "주문 정보를 저장하는 테이블"
                    elif clean_table_name.upper() == "USERS":
                        table_comment = "사용자 정보를 저장하는 테이블"
                    elif clean_table_name.upper() == "STND_TERM":
                        table_comment = "표준 용어 정보를 저장하는 테이블"
                    elif clean_table_name.upper() == "STND_WORD":
                        table_comment = "표준 단어 정보를 저장하는 테이블"
                    else:
                        table_comment = f"{clean_table_name} 테이블"
                
                # 테이블 정보 Document 생성
                table_doc = Document(
                    page_content=f"테이블명: {table_name}. 설명: {table_comment}",
                    metadata={"source_type": "table", "table_name": table_name}
                )
                documents.append(table_doc)

                # 컬럼 정보 Document 생성
                in_columns_section = False
                for line in lines:
                    if line.upper().startswith("CREATE TABLE"):
                        in_columns_section = True
                        continue
                    if line.startswith(");"):
                        in_columns_section = False
                        break

                    if in_columns_section and not line.upper().startswith(("PRIMARY KEY", "CONSTRAINT", "ALTER TABLE", "CREATE INDEX")):
                        # 컬럼 정의 라인 파싱
                        column_info = self._parse_column_definition(line, table_name)
                        if column_info:
                            col_name = column_info["column_name"]
                            col_type = column_info["data_type"]
                            col_nullable = column_info["is_nullable"]
                            col_key = column_info["column_key"]
                            col_extra = column_info["extra"]
                            
                            # 컬럼 코멘트 찾기
                            col_comment = self._find_column_comment(lines, table_name, col_name)
                            
                            # 컬럼 Document 생성
                            col_doc = Document(
                                page_content=f"테이블 '{table_name}'의 컬럼 '{col_name}' ({col_type})는 '{col_comment}'를 의미합니다.",
                                metadata={
                                    "source_type": "column",
                                    "table_name": table_name,
                                    "column_name": col_name,
                                    "data_type": col_type,
                                    "is_nullable": col_nullable,
                                    "column_key": col_key,
                                    "extra": col_extra
                                }
                            )
                            documents.append(col_doc)
            except Exception:
                print(f"--- ⚠️ Error parsing schema ---\n{schema[:200]}...\n---")
                traceback.print_exc()

        return documents

    def _parse_column_definition(self, line: str, table_name: str) -> Dict[str, str]:
        """컬럼 정의 라인을 파싱하여 컬럼 정보를 반환합니다."""
        try:
            # 줄 끝의 쉼표와 세미콜론 제거
            clean_line = line.strip().rstrip(',;')
            if not clean_line:
                return None
            
            # 따옴표가 있는 컬럼명 처리
            if clean_line.startswith('"') or clean_line.startswith("'"):
                # 따옴표로 둘러싸인 컬럼명 찾기
                quote_char = clean_line[0]
                end_quote = clean_line.find(quote_char, 1)
                if end_quote == -1:
                    return None
                col_name = clean_line[1:end_quote]
                remaining = clean_line[end_quote + 1:].strip()
            else:
                # 공백으로 분리하여 첫 번째 부분을 컬럼명으로
                parts = clean_line.split(None, 1)
                if len(parts) < 2:
                    return None
                col_name = parts[0]
                remaining = parts[1]
            
            # 데이터 타입과 제약조건 파싱
            data_type = ""
            is_nullable = "YES"
            column_key = ""
            extra = ""
            
            # 데이터 타입 추출 (괄호 포함)
            if '(' in remaining:
                # VARCHAR(100), INT(11) 같은 경우
                type_start = 0
                type_end = remaining.find('(')
                paren_end = remaining.find(')', type_end)
                if paren_end != -1:
                    data_type = remaining[type_start:paren_end + 1]
                    remaining = remaining[paren_end + 1:].strip()
                else:
                    data_type = remaining[type_start:type_end]
                    remaining = remaining[type_end:].strip()
            else:
                # INT, VARCHAR 같은 경우
                parts = remaining.split(None, 1)
                data_type = parts[0]
                remaining = parts[1] if len(parts) > 1 else ""
            
            # 제약조건 파싱
            remaining_upper = remaining.upper()
            if "NOT NULL" in remaining_upper:
                is_nullable = "NO"
                remaining = remaining.replace("NOT NULL", "").replace("not null", "").strip()
            
            if "PRIMARY KEY" in remaining_upper:
                column_key = "PRI"
                remaining = remaining.replace("PRIMARY KEY", "").replace("primary key", "").strip()
            elif "UNIQUE" in remaining_upper:
                column_key = "UNI"
                remaining = remaining.replace("UNIQUE", "").replace("unique", "").strip()
            
            if "AUTO_INCREMENT" in remaining_upper:
                extra = "auto_increment"
                remaining = remaining.replace("AUTO_INCREMENT", "").replace("auto_increment", "").strip()
            
            # 남은 부분을 extra에 추가
            if remaining:
                if extra:
                    extra += f" {remaining}"
                else:
                    extra = remaining
            
            return {
                "column_name": col_name,
                "data_type": data_type,
                "is_nullable": is_nullable,
                "column_key": column_key,
                "extra": extra
            }
            
        except Exception as e:
            print(f"⚠️ 컬럼 파싱 오류: {line} - {e}")
            return None

    def _find_column_comment(self, lines: List[str], table_name: str, column_name: str) -> str:
        """컬럼 코멘트를 찾아서 반환합니다."""
        try:
            for line in lines:
                # COMMENT ON COLUMN 구문 찾기
                if line.upper().startswith(f"COMMENT ON COLUMN {table_name}.{column_name}"):
                    if "IS" in line:
                        comment = line.split("IS", 1)[1].strip().rstrip(';')
                        return comment.strip("'\"")
                
                # 따옴표가 있는 경우도 처리
                elif line.upper().startswith(f'COMMENT ON COLUMN "{table_name}"."{column_name}"'):
                    if "IS" in line:
                        comment = line.split("IS", 1)[1].strip().rstrip(';')
                        return comment.strip("'\"")
            
            # 코멘트가 없으면 기본 설명 생성
            return f"{column_name} 컬럼"
            
        except Exception as e:
            print(f"⚠️ 컬럼 코멘트 찾기 오류: {column_name} - {e}")
            return f"{column_name} 컬럼"

# --- 4. LMStudio 임베딩 모델을 위한 커스텀 임베딩 클래스 ---
class LMStudioEmbeddings:
    """LMStudio의 로컬 임베딩 모델을 사용하는 커스텀 임베딩 클래스"""
    
    def __init__(self, base_url="http://localhost:1234", model_name="text-embedding-kure-v1"):
        self.base_url = base_url
        self.model_name = model_name
        self.embedding_endpoint = f"{base_url}/v1/embeddings"
    
    def embed_documents(self, texts):
        """여러 텍스트를 임베딩합니다."""
        embeddings = []
        for text in texts:
            embedding = self.embed_query(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text):
        """단일 텍스트를 임베딩합니다."""
        try:
            payload = {
                "input": text,
                "model": self.model_name
            }
            
            response = requests.post(
                self.embedding_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                print(f"❌ LMStudio API 오류: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ LMStudio 연결 오류: {e}")
            return None
    
    def is_available(self):
        """LMStudio 서비스가 사용 가능한지 확인합니다."""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False

# --- 5. 메인 실행 로직 ---
if __name__ == "__main__":
    # 1단계: 파일에서 스키마 문자열 로드
    schema_definitions = load_schemas_from_files(SCHEMA_FILES)

    # 2단계: 스키마 파싱
    schema_parser = SchemaParser()
    documents = schema_parser.parse_schema_to_documents(schema_definitions)
    print(f"\n총 {len(documents)}개의 Document(테이블+컬럼)를 생성했습니다.")

    # 3단계: 임베딩 및 Vector DB 저장
    if documents:
        # LMStudio 로컬 모델 우선 시도
        print("\n🔍 LMStudio 로컬 임베딩 모델 확인 중...")
        lmstudio_embeddings = LMStudioEmbeddings()
        
        if lmstudio_embeddings.is_available():
            print("✅ LMStudio 로컬 모델 사용: text-embedding-kure-v1")
            embedding_model = lmstudio_embeddings
            current_model_name = "text-embedding-kure-v1"
        else:
            print("⚠️ LMStudio 연결 실패, HuggingFace 모델 사용")
            # 공개적으로 접근 가능한 한국어 임베딩 모델 사용 (fallback)
            embedding_model = HuggingFaceEmbeddings(
                model_name="jhgan/ko-sroberta-multitask",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            current_model_name = "jhgan/ko-sroberta-multitask"
        
        # Vector DB 저장
        db_directory = "vector_db/chroma_db_schema"
        
        # 기존 DB가 있으면 삭제
        if os.path.exists(db_directory):
            import shutil
            shutil.rmtree(db_directory)
            print(f"🗑️ 기존 Vector DB 삭제: {db_directory}")
        
        # 새 Vector DB 생성
        print(f"\n🔨 Vector DB 생성 중: {db_directory}")
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            persist_directory=db_directory
        )
        
        # 모델 정보 저장
        model_info = {
            "model_name": current_model_name,
            "document_count": len(documents),
            "created_at": "2025-08-24"
        }
        
        model_info_path = os.path.join(db_directory, "model_info.json")
        with open(model_info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Vector DB 생성 완료!")
        print(f"📊 저장된 Document 수: {len(documents)}")
        print(f"🤖 사용된 모델: {current_model_name}")
        print(f"💾 저장 위치: {db_directory}")
        
        # 테스트 검색
        print(f"\n🧪 테스트 검색 실행...")
        test_query = "사용자"
        results = vector_db.similarity_search(test_query, k=3)
        print(f"🔍 쿼리: '{test_query}'")
        print(f"📋 결과 수: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.page_content[:100]}...")
        
    else:
        print("❌ 파싱할 Document가 없습니다.")