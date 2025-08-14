# Google Gemini 모델 사용 가이드

## 개요
MySQL Hub MCP 서버에 Google Gemini 모델을 추가하여 자연어를 SQL로 변환하는 기능을 제공합니다. **Gemini 1.5 Flash는 Tool 사용을 완벽하게 지원**하여 더욱 정확한 SQL 생성이 가능합니다.

## 설정 방법

### 1. 환경 변수 설정
`.env` 파일에 다음 설정을 추가하세요:

```bash
# AI Provider 설정
AI_PROVIDER=google

# Google Gemini 설정
GOOGLE_API_KEY='your_google_api_key'
GOOGLE_MODEL=gemini-1.5-flash
```

### 2. API 키 발급
1. [Google AI Studio](https://makersuite.google.com/app/apikey)에 접속
2. Google 계정으로 로그인
3. "Create API Key" 버튼 클릭
4. 생성된 API 키를 복사하여 `.env` 파일에 설정

### 3. 의존성 설치
```bash
pip install google-generativeai>=0.8.0
```

## 사용법

### Provider 전환
HTTP API를 통해 Google Provider로 전환할 수 있습니다:

```bash
curl -X POST "http://localhost:9000/ai/switch-provider" \
  -H "Content-Type: application/json" \
  -d '{"provider": "google"}'
```

### 현재 Provider 확인
```bash
curl "http://localhost:9000/ai/provider"
```

## 모델 특징

### 장점
- **완벽한 Tool 지원**: Gemini 1.5 Flash는 Function Calling을 완벽하게 지원
- **고품질 응답**: Google의 최신 AI 모델로 정확한 SQL 생성
- **빠른 응답**: 최적화된 모델로 빠른 처리 속도
- **안정성**: Google의 안정적인 인프라
- **Tool 체인 지원**: 복잡한 데이터베이스 쿼리도 단계별로 처리 가능

### Tool 사용 기능
Gemini 1.5 Flash는 다음과 같은 Tool을 완벽하게 지원합니다:

1. **get_table_list()**: 데이터베이스의 모든 테이블 목록 조회
2. **get_table_schema("테이블명")**: 특정 테이블의 스키마 정보 조회
3. **자동 Tool 체인**: 필요한 정보를 순차적으로 수집하여 최적의 SQL 생성

## 프롬프트 최적화

Gemini 1.5 Flash 모델을 위해 최적화된 프롬프트가 자동으로 적용됩니다:

1. **사고 단계**: 질문 분석 및 계획 수립
2. **Tool 사용 단계**: 필요한 도구를 순차적으로 호출하여 정보 수집
3. **SQL 생성 단계**: 수집된 정보를 바탕으로 정확한 SQL 쿼리 생성

## 테스트

테스트 스크립트를 실행하여 Google Provider가 정상 작동하는지 확인할 수 있습니다:

```bash
python test_google_provider.py
```

## 문제 해결

### 일반적인 오류

1. **API 키 오류**
   - API 키가 올바르게 설정되었는지 확인
   - API 키에 적절한 권한이 있는지 확인

2. **모델 오류**
   - `gemini-1.5-flash` 모델이 사용 가능한지 확인
   - 다른 Gemini 모델로 변경 시도

3. **연결 오류**
   - 인터넷 연결 상태 확인
   - 방화벽 설정 확인

4. **Tool 사용 오류**
   - `google-generativeai>=0.8.0` 버전이 설치되었는지 확인
   - Tool 정의가 올바른지 확인

### 로그 확인
서버 로그에서 자세한 오류 정보를 확인할 수 있습니다:

```bash
tail -f logs/server-YYYYMMDD.log
```

## 성능 최적화

1. **Tool 체인 최적화**: 필요한 정보만 순차적으로 수집
2. **프롬프트 최적화**: 명확하고 구체적인 질문 작성
3. **모델 선택**: `gemini-1.5-flash`는 Tool 사용에 최적화됨

## 라이선스 및 비용

- Google AI API 사용량에 따른 비용 발생
- [Google AI Studio 가격 정책](https://ai.google.dev/pricing) 참조
- 무료 할당량 및 유료 요금제 확인 필요
- Gemini 1.5 Flash는 비용 효율적인 모델

## Tool 사용 예시

### 1. 테이블 목록 조회
```python
# 자동으로 get_table_list() 호출
response = await ai_manager.generate_response("사용 가능한 테이블을 보여줘", tools)
```

### 2. 스키마 기반 SQL 생성
```python
# 자동으로 get_table_schema() 호출 후 SQL 생성
response = await ai_manager.generate_response("사용자 테이블에서 모든 데이터를 가져와줘", tools)
```

### 3. 복잡한 쿼리 생성
```python
# 여러 테이블의 스키마를 수집하여 JOIN 쿼리 생성
response = await ai_manager.generate_response("사용자와 주문 정보를 함께 조회해줘", tools)
```
