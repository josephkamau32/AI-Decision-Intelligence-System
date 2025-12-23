"""Quick OpenAI API Key Test"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.config import settings

print("Testing OpenAI API Key...")
print("-" * 50)

if not settings.openai_api_key:
    print("ERROR: No API key found")
    sys.exit(1)

key = settings.openai_api_key
print(f"Key loaded: {key[:10]}...{key[-4:]} ({len(key)} chars)")

try:
    from openai import OpenAI
    client = OpenAI(api_key=key)
    
    print("Calling OpenAI API...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say: API works"}],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    print("-" * 50)
    print("SUCCESS!")
    print(f"Response: {result}")
    print("-" * 50)
    print("Your API key is working correctly!")
    
except Exception as e:
    print("-" * 50)
    print(f"FAILED: {str(e)[:200]}")
    print("-" * 50)
    sys.exit(1)
