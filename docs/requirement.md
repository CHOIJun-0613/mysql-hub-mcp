# MCP(Model Context Protocol)Server 를 직접 구현하려고 함.

##1. 목적
1) Cursor AI에서 MCP를 통해 MySQL DB서버에 연결하려고 함
2) Cursor AI chat 창에서 MySQL에 자연어로 데이터를 검색색하려고 함

##2. 개발환경
1) 개발도구: Cursor IDE
2) 개발언어: Python

##3. 제반 사항
1) 대화 언어: 한국어로 표현하되, 보조적으로 영어를 사용해도됨
2) 기술용어나 약어: 기술용어나 약어는 원문을 병기할 것
3) 나의 MCP에 대한 지식: 초보자로써 알아가는 중, 따라서 쉽게 설명해주기 바람
4) 참고문서 URL: https://modelcontextprotocol.io/specification/2025-06-18/server
5) sample 프로젝트: https://modelcontextprotocol.io/quickstart/server

##4. 요청 사항
1) 내가 작성했던 프로젝트를 반드시 참조할 것: https://github.com/CHOIJun-0613/mcp-study.git
  - 이 어플리케이션 구조와 동일하게 작성할 것
  - client chat : mcp-client/client_app.py
  - server - Http 서버 및 MCP 서버버 : mcp-server/server_app.py
  - Cursor MCP tool : mcp-server/mcp-bridge.py
2) 구현해야할 대상: 상기 1.목적을 달성하기 위해 구현해야할 대상을 알려줘
3) 소스 제공: 구현해야할 대상 별로 모든 소스에 한글 코멘트 추가해서 제공해줘
4) server에서 AI Provider(Groq, Ollama)와 모델(Grog/llama3-8b-8192, Ollama/llama3:8b)을 선택적으로 사용하도록 할 것(환경설정)
5) README.md: 이 프로젝트에 대한 제반사항을 정리해서 README.md로 저장해줘
6) uv package를 사용할 것.
7) logging package를 사용하고, log level및 출력 형태는 환경설정 값을 참조하는 형태로 작성


##5. 프로젝트 구조
1) 프로젝트 폴더: D:\\workspaces\\mcp-work\\mysql-hub-mcp
2) clent: mcp server를 테스트 하기 위한 client 어플리케이션 저장 폴더
3) server: MCP server source 저장 폴더
4) bridge: Cursor MCP tool 연결 source 저장 폴더더
5) docs: requirement 문서 저장폴더
6) 'uv init mysql-hub-mcp' 해놓은 상태임
7) client 폴더와 server 폴더에 각각 가상환경 구성해줘
4) 기타: 각 폴더의 하위 폴더는 용도에 맞게 적절히 결정할 것
