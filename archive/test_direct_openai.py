#!/usr/bin/env python3
"""
Test direct OpenAI connection with existing API key
"""

from langchain_openai import ChatOpenAI


def get_api_key_from_env_file(env_file_path="/home/envs/openai.env"):
    """Get API key from .env file"""
    try:
        with open(env_file_path, "r") as file:
            for line in file:
                if line.startswith("OPENAI_API_KEY="):
                    return line.strip().split("=", 1)[1]
        raise ValueError(f"OPENAI_API_KEY not found in {env_file_path}")
    except FileNotFoundError:
        raise ValueError(f".env file not found: {env_file_path}")


def test_direct_openai():
    """Test direct OpenAI connection"""
    print("🧪 Testing direct OpenAI connection...")

    try:
        api_key = get_api_key_from_env_file()
        print(f"API key starts with: {api_key[:10]}...")

        # Direct OpenAI configuration (no custom base URL)
        llm = ChatOpenAI(model="gpt-4", temperature=0.3, openai_api_key=api_key)

        print("✅ Direct OpenAI LLM created successfully")

        # Test invocation
        response = llm.invoke("Say hello in one word")
        print(f"✅ Response: {response.content}")
        return True

    except Exception as e:
        print(f"❌ Direct OpenAI Error: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Direct OpenAI Test")
    print("=" * 30)

    works = test_direct_openai()

    if works:
        print("\n✅ Your OpenAI API key works with direct OpenAI!")
        print("The issue is specifically with OpenRouter configuration.")
    else:
        print("\n❌ API key issue - may be invalid or expired.")
