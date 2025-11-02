"""
Test to see the actual markdown output from the API
"""

import requests
import json

BASE_URL = "http://localhost:8080"
SESSION_ID = "markdown-test-999"

# Setup: Get recommendations
print("Setting up with recommendations...")
r1 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [{"role": "user", "content": "I need insurance for Japan, leaving December for 9 days, I'm 31"}],
        "session_id": SESSION_ID
    },
    timeout=60
).json()

# Ask for comparison
print("Asking for comparison...")
r2 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [{"role": "user", "content": "What's the cost and compare them"}],
        "session_id": SESSION_ID
    },
    timeout=60
).json()

answer = r2['choices'][0]['message']['content']

# Save to file to inspect
with open("/tmp/markdown_output.md", "w") as f:
    f.write(answer)

print(f"\n✅ Saved markdown output to /tmp/markdown_output.md")
print(f"Length: {len(answer)} characters")
print(f"\nFirst 500 chars:")
print("=" * 80)
print(answer[:500])
print("=" * 80)

# Check for proper line breaks
line_count = answer.count('\n')
double_line_breaks = answer.count('\n\n')
print(f"\nLine breaks: {line_count}")
print(f"Double line breaks: {double_line_breaks}")

# Check if headers have proper spacing
has_header_spacing = '\n\n##' in answer or '\n##' in answer
print(f"Headers have spacing: {has_header_spacing}")

