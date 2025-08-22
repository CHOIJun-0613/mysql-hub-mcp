def main():
    print("Hello from adk-agents!")
    
    # AI Provider 정보 표시
    try:
        from mysql_hub_agent.ai_config import ai_config
        provider_info = ai_config.get_provider_info()
        print(f"🤖 AI Provider: {provider_info['provider']}")
        print(f"📱 모델: {provider_info['model']}")
        print(f"✅ 상태: {'사용 가능' if provider_info['available'] else '사용 불가능'}")
    except ImportError:
        print("⚠️ AI Provider 정보를 불러올 수 없습니다.")


if __name__ == "__main__":
    main()
