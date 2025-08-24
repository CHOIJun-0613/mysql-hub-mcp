from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import traceback
import requests
import json
import os

# --- 1. LMStudio 임베딩 모델을 위한 커스텀 임베딩 클래스 ---
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

# --- 2. Vector DB 연결 및 임베딩 모델 설정 ---
def setup_vector_db():
    """Vector DB를 설정하고 임베딩 모델을 반환합니다."""
    db_directory = "vector_db/chroma_db_schema"
    
    if not os.path.exists(db_directory):
        print(f"❌ Vector DB 디렉토리를 찾을 수 없습니다: {db_directory}")
        print("먼저 build_schema_db.py를 실행하여 Vector DB를 생성해주세요.")
        return None, None
    
    # 저장된 모델 정보 확인
    model_info_file = os.path.join(db_directory, "model_info.json")
    if os.path.exists(model_info_file):
        try:
            with open(model_info_file, 'r', encoding='utf-8') as f:
                saved_model_info = json.load(f)
            saved_model_name = saved_model_info.get("model_name", "unknown")
            print(f"📋 Vector DB에 저장된 모델: {saved_model_name}")
        except Exception as e:
            print(f"⚠️ 모델 정보 읽기 실패: {e}")
            saved_model_name = "unknown"
    else:
        print("⚠️ 모델 정보 파일이 없습니다.")
        saved_model_name = "unknown"
    
    # 저장된 모델과 동일한 모델 사용
    if saved_model_name == "text-embedding-kure-v1":
        print("🔍 LMStudio 로컬 임베딩 모델 확인 중...")
        lmstudio_embeddings = LMStudioEmbeddings()
        
        if lmstudio_embeddings.is_available():
            print("✅ LMStudio 로컬 모델 사용: text-embedding-kure-v1")
            embedding_model = lmstudio_embeddings
        else:
            print("❌ LMStudio 연결 실패!")
            print("⚠️ Vector DB는 'text-embedding-kure-v1' 모델로 생성되었습니다.")
            print("❌ 다른 모델로 검색하면 정확도가 떨어집니다.")
            print("💡 LMStudio를 실행하거나 Vector DB를 재생성해주세요.")
            return None, None
            
    elif saved_model_name == "jhgan/ko-sroberta-multitask":
        print("✅ HuggingFace 모델 사용: ko-sroberta-multitask")
        embedding_model = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
    else:
        print(f"⚠️ 알 수 없는 모델: {saved_model_name}")
        print("🔄 안전을 위해 HuggingFace 모델 사용")
        embedding_model = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    # Vector DB 연결
    try:
        vector_db = Chroma(
            persist_directory=db_directory,
            embedding_function=embedding_model
        )
        
        # 문서 수 확인
        doc_count = vector_db._collection.count()
        print(f"📊 Vector DB 연결 성공! 총 {doc_count}개의 문서가 있습니다.")
        
        return vector_db, embedding_model
        
    except Exception as e:
        print(f"❌ Vector DB 연결 실패: {e}")
        return None, None

# --- 3. 스키마 정보 검색 함수 ---
def search_schema_info(vector_db, query, k=3):
    """스키마 정보를 검색합니다."""
    try:
        retrieved_docs = vector_db.similarity_search(query, k=k)
        print(f"\n🔍 검색 결과: '{query}'")
        print(f"📋 찾은 문서 수: {len(retrieved_docs)}")
        
        for i, doc in enumerate(retrieved_docs, 1):
            print(f"\n📄 문서 {i}:")
            print(f"  📝 내용: {doc.page_content}")
            print(f"  🏷️  메타데이터: {doc.metadata}")
            
        return retrieved_docs
        
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")
        return []

# --- 3-3. Vector DB 디버그 함수 ---
def debug_vector_db(vector_db, max_docs=20):
    """Vector DB에 저장된 실제 데이터를 확인합니다."""
    try:
        print(f"\n🔍 Vector DB 디버그 정보")
        print("=" * 60)
        
        # 전체 문서 수 확인
        total_docs = vector_db._collection.count()
        print(f"📊 총 문서 수: {total_docs}")
        
        # 모든 문서의 메타데이터 확인
        print(f"\n📋 메타데이터 샘플 (최대 {max_docs}개):")
        
        # 간단한 쿼리로 모든 문서 가져오기
        all_docs = vector_db.similarity_search("테이블", k=total_docs)
        
        # 테이블별로 그룹화
        tables = {}
        for doc in all_docs:
            source_type = doc.metadata.get("source_type", "unknown")
            table_name = doc.metadata.get("table_name", "unknown")
            
            if source_type not in tables:
                tables[source_type] = {}
            if table_name not in tables[source_type]:
                tables[source_type][table_name] = []
            
            tables[source_type][table_name].append(doc)
        
        # 결과 출력
        for source_type, table_data in tables.items():
            print(f"\n🏷️  {source_type.upper()}:")
            for table_name, docs in table_data.items():
                print(f"  📊 {table_name}: {len(docs)}개 문서")
                # 첫 번째 문서 내용 샘플
                if docs:
                    print(f"    📝 샘플: {docs[0].page_content[:100]}...")
        
        return tables
        
    except Exception as e:
        print(f"❌ 디버그 중 오류 발생: {e}")
        return {}

# --- 3-1. 테이블별 컬럼 정보 검색 함수 (수정) ---
def search_table_columns(vector_db, table_name, k=None):
    """특정 테이블의 모든 컬럼 정보를 검색합니다."""
    try:
        print(f"\n🔍 테이블 '{table_name}' 컬럼 검색")
        
        # k 값이 지정되지 않았으면 충분히 큰 값으로 설정
        if k is None:
            k = 100  # 더 큰 값으로 설정
        
        print(f"📊 검색 범위: 상위 {k}개 문서에서 필터링")
        
        # 더 일반적인 쿼리로 검색
        query = "컬럼"
        all_docs = vector_db.similarity_search(query, k=k)
        
        # 해당 테이블의 컬럼만 필터링 (대소문자 구분 없이)
        table_columns = []
        table_name_upper = table_name.upper()
        
        for doc in all_docs:
            if doc.metadata.get("source_type") == "column":
                doc_table_name = doc.metadata.get("table_name", "")
                # 따옴표 제거 및 대소문자 비교
                doc_table_clean = doc_table_name.replace('"', '').replace("'", "").upper()
                
                if doc_table_clean == table_name_upper:
                    table_columns.append(doc)
        
        if table_columns:
            print(f"📋 '{table_name}' 테이블의 컬럼 수: {len(table_columns)}")
            
            # 컬럼 정보를 보기 좋게 정리
            for i, col_doc in enumerate(table_columns, 1):
                metadata = col_doc.metadata
                print(f"\n📊 컬럼 {i}:")
                print(f"  🏷️  컬럼명: {metadata.get('column_name', 'N/A')}")
                print(f"  📝 데이터타입: {metadata.get('data_type', 'N/A')}")
                print(f"  📄 설명: {col_doc.page_content}")
                
        else:
            print(f"❌ '{table_name}' 테이블의 컬럼을 찾을 수 없습니다.")
            print(f"💡 k 값을 늘려서 다시 시도해보세요. (현재 k={k})")
            print(f"🔍 실제 테이블명: '{table_name}'")
            
        return table_columns
        
    except Exception as e:
        print(f"❌ 컬럼 검색 중 오류 발생: {e}")
        return []

# --- 3-2. 향상된 스키마 검색 함수 ---
def search_table_schema(vector_db, table_name, k=15):
    """테이블의 전체 스키마 정보를 종합적으로 검색합니다."""
    try:
        print(f"\n🔍 테이블 '{table_name}' 전체 스키마 검색")
        print("=" * 60)
        
        # 1. 테이블 정보 검색
        table_query = f"테이블명: {table_name}"
        table_docs = vector_db.similarity_search(table_query, k=5)
        
        table_info = None
        for doc in table_docs:
            if (doc.metadata.get("source_type") == "table" and 
                table_name.upper() in doc.page_content.upper()):
                table_info = doc
                break
        
        if table_info:
            print("📋 테이블 정보:")
            print(f"  {table_info.page_content}")
        else:
            print(f"❌ '{table_name}' 테이블 정보를 찾을 수 없습니다.")
        
        # 2. 컬럼 정보 검색
        print(f"\n📊 컬럼 정보:")
        columns = search_table_columns(vector_db, table_name, k=k)
        
        # 3. 요약 정보
        if columns:
            print(f"\n📈 요약:")
            print(f"  • 총 컬럼 수: {len(columns)}")
            
            # 데이터 타입별 분류
            data_types = {}
            for col in columns:
                dtype = col.metadata.get("data_type", "unknown")
                data_types[dtype] = data_types.get(dtype, 0) + 1
            
            print(f"  • 데이터 타입 분포:")
            for dtype, count in data_types.items():
                print(f"    - {dtype}: {count}개")
        
        return {
            "table_info": table_info,
            "columns": columns
        }
        
    except Exception as e:
        print(f"❌ 스키마 검색 중 오류 발생: {e}")
        return {"table_info": None, "columns": []}

# --- 4. 메인 실행 로직 ---
if __name__ == "__main__":
    print("🚀 Vector DB 스키마 정보 검색 시작")
    print("=" * 50)
    
    # Vector DB 설정
    vector_db, embedding_model = setup_vector_db()
    
    if vector_db is None:
        print("❌ Vector DB 설정 실패. 프로그램을 종료합니다.")
        exit(1)
    
    # 먼저 디버그 정보 확인
    debug_vector_db(vector_db)
    
    # 검색 예시 실행
    print("\n" + "=" * 50)
    print("🔍 스키마 정보 검색 예시")
    print("=" * 50)
    
    # 예시 1: 특정 컬럼이 있는 테이블 찾기
    query1 = "'email'는 어떤 테이블에 저장되어 있나요?"
    search_schema_info(vector_db, query1, k=1)
    
    # 예시 2: 표준 용어 관련 테이블 찾기
    query2 = "표준 용어는 어떤 테이블이야?"
    search_schema_info(vector_db, query2, k=1)
    
    # 예시 3: 사용자 관련 정보 찾기
    query3 = "'사용자'는 어떤 테이블에 저장되어 있나요?"
    search_schema_info(vector_db, query3, k=1)
    
    # 'orders' 테이블의 모든 컬럼 정보를 정확히 받고 싶다면, 임베딩 모델에 질의할 때 아래와 같이 명확하게 요청하는 것이 좋습니다.
    # 예시:
    query_orders_all_columns = "'orders' 테이블의 모든 컬럼명과 데이터 타입, 제약조건을 상세히 알려줘"
    search_schema_info(vector_db, query_orders_all_columns, k=10)
    # 또는
    # query_orders_all_columns = "'orders' 테이블의 전체 스키마(컬럼명, 타입, 제약조건 등)를 모두 보여줘"
    # search_schema_info(vector_db, query_orders_all_columns, k=10)
    
    # 예시 4: orders 테이블의 전체 스키마 정보 (새로운 함수 사용)
    print("\n" + "=" * 60)
    print("🆕 향상된 스키마 검색 예시")
    print("=" * 60)
    
    # orders 테이블의 전체 스키마 검색
    search_table_schema(vector_db, "orders")
    
    # USERS 테이블의 전체 스키마 검색
    search_table_schema(vector_db, "USERS")
    
    print("\n" + "=" * 50)
    print("✅ 검색 완료!")
    print("=" * 50)