"""Test OpenAI via backend Copilot"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.copilot.agent import copilot_agent

print("Testing Copilot Agent Integration")
print("=" * 40)

if not copilot_agent:
    print("ERROR: Copilot agent not initialized")
    sys.exit(1)

print("Sending test query...")
response = copilot_agent.query("Say hello in 3 words")

print("=" * 40)
if "API key" in response or "not configured" in response or "authentication" in response:
    print("FAILED - API Key Issue")
    print(response)
    sys.exit(1)
else:
    print("SUCCESS!")
    print(f"Response: {response}")
    print("=" * 40)
    print("Your Copilot is working!")
