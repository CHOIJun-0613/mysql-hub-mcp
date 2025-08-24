import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import traceback
import requests
import json

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

# --- 3. 스키마를 의미 단위(Document)로 파싱하는 함수 (이전과 동일) ---
def parse_schema_to_documents(sql_schemas):
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

                if in_columns_section and not line.upper().startswith(("PRIMARY KEY", "CONSTRAINT")):
                    parts = line.split()
                    col_name = parts[0]
                    col_type = parts[1].replace(',', '')
                    col_comment = ""
                    
                    for c_line in lines:
                        if c_line.upper().startswith(f"COMMENT ON COLUMN {table_name}.{col_name}"):
                            col_comment = c_line.split("IS")[1].strip().replace("'", "").replace(";", "")
                            break
                        # 따옴표가 있는 경우도 처리
                        elif c_line.upper().startswith(f'COMMENT ON COLUMN "{table_name}"."{col_name}"'):
                            col_comment = c_line.split("IS")[1].strip().replace("'", "").replace(";", "")
                            break
                    
                    col_doc = Document(
                        page_content=f"테이블 '{table_name}'의 컬럼 '{col_name}' ({col_type})는 '{col_comment}'를 의미합니다.",
                        metadata={
                            "source_type": "column",
                            "table_name": table_name,
                            "column_name": col_name,
                            "data_type": col_type
                        }
                    )
                    documents.append(col_doc)
        except Exception:
            print(f"--- ⚠️ Error parsing schema ---\n{schema[:200]}...\n---")
            traceback.print_exc()

    return documents

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
    documents = parse_schema_to_documents(schema_definitions)
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
        
        db_directory = "vector_db/chroma_db_schema"
        model_info_file = os.path.join(db_directory, "model_info.json")
        
        # 기존 Vector DB 확인 및 모델 정보 체크
        if os.path.exists(db_directory):
            print(f"\n📁 기존 Vector DB 발견: {db_directory}")
            
            # 모델 정보 파일 확인
            if os.path.exists(model_info_file):
                try:
                    with open(model_info_file, 'r', encoding='utf-8') as f:
                        saved_model_info = json.load(f)
                    saved_model_name = saved_model_info.get("model_name", "unknown")
                    
                    print(f"📋 저장된 모델: {saved_model_name}")
                    print(f"📋 현재 모델: {current_model_name}")
                    
                    if saved_model_name != current_model_name:
                        print("⚠️ 임베딩 모델이 변경되었습니다!")
                        print("🔄 Vector DB를 새로 생성합니다...")
                        
                        # 기존 디렉토리 삭제
                        import shutil
                        shutil.rmtree(db_directory)
                        print("🗑️ 기존 Vector DB 삭제 완료")
                        
                        # 새로 생성
                        vector_db = Chroma.from_documents(
                            documents=documents, 
                            embedding=embedding_model, 
                            persist_directory=db_directory
                        )
                        
                        # 모델 정보 저장
                        os.makedirs(db_directory, exist_ok=True)
                        with open(model_info_file, 'w', encoding='utf-8') as f:
                            json.dump({"model_name": current_model_name}, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ 새로운 모델로 Vector DB 생성 완료: {current_model_name}")
                        
                    else:
                        print("✅ 동일한 모델 사용 중, 기존 데이터 업데이트")
                        # 기존 컬렉션에 새 문서 추가
                        vector_db = Chroma(
                            persist_directory=db_directory,
                            embedding_function=embedding_model
                        )
                        
                        # 기존 문서 수 확인
                        existing_count = vector_db._collection.count()
                        print(f"📊 기존 문서 수: {existing_count}")
                        
                        # 새 문서 추가
                        vector_db.add_documents(documents)
                        
                        # 업데이트된 문서 수 확인
                        updated_count = vector_db._collection.count()
                        print(f"📊 업데이트된 문서 수: {updated_count}")
                        print(f"📈 새로 추가된 문서 수: {updated_count - existing_count}")
                        
                except Exception as e:
                    print(f"⚠️ 모델 정보 확인 실패: {e}")
                    print("🔄 안전을 위해 Vector DB를 새로 생성합니다...")
                    
                    # 기존 디렉토리 삭제 후 새로 생성
                    import shutil
                    shutil.rmtree(db_directory)
                    
                    vector_db = Chroma.from_documents(
                        documents=documents, 
                        embedding=embedding_model, 
                        persist_directory=db_directory
                    )
                    
                    # 모델 정보 저장
                    os.makedirs(db_directory, exist_ok=True)
                    with open(model_info_file, 'w', encoding='utf-8') as f:
                        json.dump({"model_name": current_model_name}, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ Vector DB 새로 생성 완료: {current_model_name}")
            else:
                print("⚠️ 모델 정보 파일이 없습니다.")
                print("🔄 Vector DB를 새로 생성합니다...")
                
                # 기존 디렉토리 삭제 후 새로 생성
                import shutil
                shutil.rmtree(db_directory)
                
                vector_db = Chroma.from_documents(
                    documents=documents, 
                    embedding=embedding_model, 
                    persist_directory=db_directory
                )
                
                # 모델 정보 저장
                os.makedirs(db_directory, exist_ok=True)
                with open(model_info_file, 'w', encoding='utf-8') as f:
                    json.dump({"model_name": current_model_name}, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Vector DB 새로 생성 완료: {current_model_name}")
                
        else:
            print(f"\n🆕 새로운 Vector DB 생성: {db_directory}")
            # 새 컬렉션 생성
            vector_db = Chroma.from_documents(
                documents=documents, 
                embedding=embedding_model, 
                persist_directory=db_directory
            )
            
            # 모델 정보 저장
            os.makedirs(db_directory, exist_ok=True)
            with open(model_info_file, 'w', encoding='utf-8') as f:
                json.dump({"model_name": current_model_name}, f, ensure_ascii=False, indent=2)
            
            print(f"📊 새로 생성된 문서 수: {vector_db._collection.count()}")
        
        print(f"\nChromaDB에 총 {vector_db._collection.count()}개의 Document가 저장/업데이트 되었습니다.")

        # --- 6. 저장된 스키마 정보 검색(Querying) ---
        print("\n--- 스키마 정보 검색 예시 ---")

        query1 = "'사용자'는 어떤 테이블에 저장되어 있나요?"
        retrieved_docs1 = vector_db.similarity_search(query1, k=2)
        print(f"\n[질문 1] {query1}")
        for doc in retrieved_docs1:
            print(f"  - (유사도 높은 정보): {doc.page_content}")
            print(f"  - (메타데이터): {doc.metadata}")

        query2 = "표준 용어는 어떤 테이블이야?"
        retrieved_docs2 = vector_db.similarity_search(query2, k=1)
        print(f"\n[질문 2] {query2}")
        for doc in retrieved_docs2:
            print(f"  - (유사도 높은 정보): {doc.page_content}")
            print(f"  - (메타데이터): {doc.metadata}")