#!/usr/bin/env python3
"""
Test OpenRouter authentication without custom headers
"""

import sys
from langchain_openai import ChatOpenAI

def get_api_key_from_env_file(env_file_path="/home/envs/openai.env"):
    """Get API key from .env file"""
    try:
        with open(env_file_path, 'r') as file:
            for line in file:
                if line.startswith('OPENAI_API_KEY='):
                    return line.strip().split('=', 1)[1]
        raise ValueError(f"OPENAI_API_KEY not found in {env_file_path}")
    except FileNotFoundError:
        raise ValueError(f".env file not found: {env_file_path}")

def test_basic_openrouter():
    """Test basic OpenRouter connection without custom headers"""
    print("🧪 Testing basic OpenRouter connection...")
    
    try:
        api_key = get_api_key_from_env_file()
        
        # Basic configuration without custom headers
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        print("✅ LLM created successfully")
        
        # Test invocation
        response = llm.invoke("Say hello in one word")
        print(f"✅ Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_headers():
    """Test with custom headers"""
    print("\n🧪 Testing with custom headers...")
    
    try:
        api_key = get_api_key_from_env_file()
        
        headers = {
            "HTTP-Referer": "https://github.com/fhalamzie/langchain_project",
            "X-Title": "WINCASA DB Query System"
        }
        
        # Configuration with custom headers
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers=headers
        )
        
        print("✅ LLM with headers created successfully")
        
        # Test invocation
        response = llm.invoke("Say hello in one word")
        print(f"✅ Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error with headers: {e}")
        return False

if __name__ == "__main__":
    print("🔍 OpenRouter Authentication Test")
    print("=" * 50)
    
    # Test 1: Basic connection
    basic_works = test_basic_openrouter()
    
    # Test 2: With headers
    headers_work = test_with_headers()
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"Basic OpenRouter: {'✅ WORKS' if basic_works else '❌ FAILS'}")
    print(f"With Headers: {'✅ WORKS' if headers_work else '❌ FAILS'}")
    
    if basic_works and not headers_work:
        print("\n🎯 Headers are causing the authentication issue!")
    elif not basic_works:
        print("\n⚠️ OpenRouter authentication failing even without headers")
    else:
        print("\n✅ Both configurations work!")