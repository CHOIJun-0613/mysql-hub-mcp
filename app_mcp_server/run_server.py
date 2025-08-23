#!/usr/bin/env python3
"""
서버 실행 스크립트
서버를 쉽게 실행할 수 있도록 하는 스크립트입니다.
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from server_app import main

if __name__ == "__main__":
    main() 