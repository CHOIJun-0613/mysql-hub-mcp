import re
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config

result = {
    'role': 'assistant', 
    'tool_calls': [
        {'id': '1r64jcfg2', 
         'type': 'function', 
         'function': {
             'name': 'get_table_schema', 
             'arguments': '{"table_name":"users"}'
            }}
    ]
}

result2 = { 
           'role': 'assistant', 
           'content': '', 
           'tool_calls': [
               {'function': {'name': 'get_table_list', 'arguments': {}}}, 
               {'function': {'index': 1, 'name': 'get_table_schema', 'arguments': {'table_name': '사용자'}}}, 
               {'function': {'index': 2, 'name': 'get_table_schema', 'arguments': {'table_name': '구매'}}}
               ]
           }

result3 = """
response:
GenerateContentResponse(
    done=True,
    iterator=None,
    result=protos.GenerateContentResponse({
      "candidates": [
        {
          "content": {
            "parts": [
              {
                "function_call": {
                  "name": "get_table_list",
                  "args": {}
                }
              }
            ],
            "role": "model"
          },
          "finish_reason": "STOP",
          "avg_logprobs": -1.2874037201981991e-05
        }
      ],
      "usage_metadata": {
        "prompt_token_count": 2095,
        "candidates_token_count": 5,
        "total_token_count": 2100
      },
              "model_version": "llama3:8b"
    }),
)
"""

# 'table_name' 값 추출 및 출력
tool_call = result['tool_calls'][0]
tool_call_id = tool_call['id']
print(tool_call_id)
arguments = tool_call['function']['arguments']
# arguments가 JSON 문자열이므로 파싱 필요
args_dict = json.loads(arguments)
print(args_dict['table_name'])


parsed_tool_calls = []



result = result2

if 'tool_calls' in result:
    print("'tool_calls'가 result에 포함되어 있습니다.")
    for tool_call in result['tool_calls']:
        function_info = tool_call.get('function', {})
        name = function_info.get('name')
        tool_call_id = tool_call.get('id', None)
        index = function_info.get('index', 1)
        arguments = function_info.get('arguments')
        # arguments가 문자열이면 json 파싱 시도
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                pass
        parsed_tool_calls.append({
            'name': name,
            'tool_call_id': tool_call_id,
            'index': index,
            'arguments': arguments
        })
else:
    print("'tool_calls'가 result에 포함되어 있지 않습니다.")



print(parsed_tool_calls)

for tc in parsed_tool_calls:
    func_name = tc['name']
    func_args = tc['arguments']
    index = tc['index']
    print(f"(Tool 호출 감지 ): {tc['tool_call_id']}, {func_name}, {index}, {func_args}")

    print(f"🧠 LLM 요청: 로컬 함수 {tc['tool_call_id']}, {func_name}, {index}, ({json.dumps(func_args, ensure_ascii=False)}) 실행")







