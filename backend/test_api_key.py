"""Quick test to verify OpenAI API key is working."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.config import settings

print("=" * 60)
print("OpenAI API Key Configuration Test")
print("=" * 60)

# Check if key is loaded
if not settings.openai_api_key:
    print("❌ ERROR: OPENAI_API_KEY is not set")
    print("   Please add OPENAI_API_KEY to your .env file")
    sys.exit(1)

# Mask the key for display
api_key = settings.openai_api_key
masked = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
print(f"✓ API Key loaded: {masked}")
print(f"  Length: {len(api_key)} characters")

# Test with OpenAI directly
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    print("\nTesting API call to OpenAI...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' in exactly 3 words"}
        ],
        max_tokens=20
    )
    
    print("=" * 60)
    print("✅ SUCCESS! Your OpenAI API key is working!")
    print("=" * 60)
    print(f"Response: {response.choices[0].message.content}")
    print("=" * 60)
    print("\n✓ Your Copilot feature should work now!")
    print("  Try asking a question in the UI at http://localhost:3000/copilot")
    
except Exception as e:
    print("=" * 60)
    print("❌ ERROR: API test failed")
    print("=" * 60)
    print(f"Error: {e}")
    
    error_msg = str(e).lower()
    if "api_key" in error_msg or "authentication" in error_msg:
        print("\n⚠️  This looks like an authentication issue.")
        print("   Please verify:")
        print("   1. Your API key is correct")
        print("   2. The key starts with 'sk-'")
        print("   3. It hasn't been revoked")
    elif "quota" in error_msg or "billing" in error_msg:
        print("\n⚠️  This looks like a billing/quota issue.")
        print("   Check your OpenAI account billing status.")
    
    sys.exit(1)
