import requests
import json

def test_natural_language_query():
    url = "http://localhost:8000/database/natural-query"
    headers = {"Content-Type": "application/json"}
    data = {"question": "사용자 목록을 검색해줘"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            if result.get('success'):
                print(f"SQL Query: {result.get('data', {}).get('sql_query')}")
                print(f"Result: {result.get('data', {}).get('result')}")
            else:
                print(f"Error: {result.get('error')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_natural_language_query()
