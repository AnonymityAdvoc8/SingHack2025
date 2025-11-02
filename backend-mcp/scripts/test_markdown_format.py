"""
Simple test to check markdown output format
"""

import requests

BASE_URL = "http://localhost:8080"

response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "I need insurance for Japan, December for 9 days, I'm 31"}
        ],
        "session_id": "format-test-001"
    },
    timeout=60
).json()

answer = response['choices'][0]['message']['content']

# Save raw output
with open("markdown_output.txt", "w") as f:
    f.write(answer)

print("="*80)
print("MARKDOWN OUTPUT ANALYSIS")
print("="*80)
print(f"Total length: {len(answer)} chars")
print(f"Line breaks: {answer.count(chr(10))}")
print(f"Double breaks: {answer.count(chr(10) + chr(10))}")
print(f"\nFirst 300 characters:")
print("-"*80)
print(repr(answer[:300]))
print("-"*80)

# Check for proper markdown
has_headers = "##" in answer
has_bold = "**" in answer
has_bullets = "\n-" in answer or "\n •" in answer
has_tables = "|" in answer

print(f"\nMarkdown elements:")
print(f"  Headers (##): {has_headers}")
print(f"  Bold (**): {has_bold}")
print(f"  Bullets (-): {has_bullets}")
print(f"  Tables (|): {has_tables}")

print(f"\n✅ Saved to markdown_output.txt")

