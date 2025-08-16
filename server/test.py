import re
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config
from database import DatabaseManager

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

result3 = {'role': 'assistant', 'content': '```json\n{\n  "name": "get_table_list",\n  "arguments": {}\n}\n```'}
result4 = {'role': 'assistant', 'content': '{"name": "get_table_schema", "arguments": {"table_name": "users"}}'}

# 'table_name' 값 추출 및 출력
tool_call = result['tool_calls'][0]
tool_call_id = tool_call['id']
print(tool_call_id)
arguments = tool_call['function']['arguments']
# arguments가 JSON 문자열이므로 파싱 필요
args_dict = json.loads(arguments)
print(args_dict['table_name'])


parsed_tool_calls = []



result = result

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
  if 'tool_calls' not in result and 'content' in result:
      content = result['content']
      
      if content.strip().startswith("```json\n{\n"):
          # '```json'과 '```' 사이의 JSON 부분 추출
          import re
          
          match = re.search(r'```json\s*([\s\S]+?)\s*```', content)
          if match:
              json_str = match.group(1)
              try:
                  function_info = json.loads(json_str)
                  name = function_info.get('name')
                  arguments = function_info.get('arguments')
                  tool_call_id = None
                  index = 1
                  parsed_tool_calls.append({
                      'name': name,
                      'tool_call_id': tool_call_id,
                      'index': index,
                      'arguments': arguments
                  })
              except Exception as e:
                  print(f"content에서 JSON 파싱 실패: {e}")
      elif content.strip().startswith('{"name"'):
          function_info = json.loads(content)
          name = function_info.get('name')
          arguments = function_info.get('arguments')
          tool_call_id = None
          index = 1
          parsed_tool_calls.append({
              'name': name,
              'tool_call_id': tool_call_id,
              'index': index,
              'arguments': arguments
          })
  else:
      print("'tool_calls'가 result에 포함되어 있지 않고 'content'도 없습니다.") 

print(parsed_tool_calls)

for tc in parsed_tool_calls:
    func_name = tc['name']
    func_args = tc['arguments']
    index = tc['index']
    print(f"(Tool 호출 감지 ): {tc['tool_call_id']}, {func_name}, {index}, {func_args}")

    print(f"🧠 LLM 요청: 로컬 함수 {tc['tool_call_id']}, {func_name}, {index}, ({json.dumps(func_args, ensure_ascii=False)}) 실행")

db_manager = DatabaseManager()
table_list =   db_manager.get_table_list()
print(table_list)





