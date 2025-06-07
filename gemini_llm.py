from langchain_openai import ChatOpenAI
import os

def get_gemini_llm():
    """
    Returns a ChatOpenAI instance configured for Gemini 2.5 Pro via OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Try loading from .env if not already loaded
        from dotenv import load_dotenv
        load_dotenv("/home/envs/openrouter.env")
        api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found in environment or /home/envs/openrouter.env")
    return ChatOpenAI(
        model="google/gemini-2.5-pro-preview",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.2,
        max_tokens=2048,
        extra_headers={
            "HTTP-Referer": "https://github.com/fhalamzie/langchain_project",
            "X-Title": "WINCASA DB Query System"
        }
    )
