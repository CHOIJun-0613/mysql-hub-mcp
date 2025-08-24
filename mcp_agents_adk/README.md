# MCP AI 에이전트 (Google ADK)

이 디렉토리에는 Google의 Agent Development Kit (ADK)를 기반으로 구축된 지능형 AI 에이전트가 포함되어 있습니다.

## 주요 기능

- **Google ADK 기반**: Google의 LLM 및 에이전트 개발 도구를 사용하여, 복잡한 추론과 도구 사용(Tool Use)이 가능한 에이전트를 구현합니다.
- **다중 AI Provider 지원**: `ai_providers.py`를 통해 Google Gemini 뿐만 아니라 Groq, LM Studio 등 다양한 LLM을 에이전트의 추론 엔진으로 사용할 수 있도록 지원합니다.
- **MCP 서버 연동**: 에이전트는 `app_mcp_server`와 통신하여 데이터베이스 정보 조회, 쿼리 실행 등의 작업을 수행하도록 구성될 수 있습니다.

## 주요 파일

- `main.py`: AI 에이전트를 실행하는 메인 스크립트입니다.
- `db_hub_agent/agent.py`: ADK `Agent`를 래핑하고 MCP 서버와 통신하기 위한 도구를 설정하는 등 에이전트의 핵심 로직을 포함합니다.
- `db_hub_agent/ai_config.py`: `.env` 파일에서 에이전트가 사용할 AI Provider 및 모델 설정을 읽어옵니다.
- `db_hub_agent/ai_providers.py`: 각 AI Provider (Google, Groq, LM Studio)에 맞는 LLM 클라이언트 초기화 로직을 담고 있습니다.
- `db_hub_agent/env.example`: 에이전트 설정에 필요한 환경 변수 목록 예제입니다.

## 실행 방법

프로젝트 루트의 `run_cmd` 디렉토리에 있는 배치 파일을 사용하여 에이전트를 실행합니다.

- **MCP 에이전트 실행 (콘솔)**:
  ```batch
  \run_cmd\2-2.run_mcp_agent_cmd.bat
  ```