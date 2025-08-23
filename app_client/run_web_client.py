#!/usr/bin/env python3
"""
MySQL Hub MCP Web Client Runner
Streamlit 웹 클라이언트를 실행하는 스크립트
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Streamlit 웹 클라이언트 실행"""
    
    # 현재 디렉토리 확인
    current_dir = Path(__file__).parent
    client_web_path = current_dir / "client_web.py"
    
    if not client_web_path.exists():
        print(f"❌ 오류: {client_web_path} 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    print("🚀 MySQL Hub MCP Web Client를 시작합니다...")
    print(f"📁 작업 디렉토리: {current_dir}")
    print(f"🌐 웹 인터페이스: http://localhost:8501")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    print("-" * 50)
    
    try:
        # Streamlit 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(client_web_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], cwd=current_dir)
        
    except KeyboardInterrupt:
        print("\n👋 웹 클라이언트를 종료합니다.")
    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 