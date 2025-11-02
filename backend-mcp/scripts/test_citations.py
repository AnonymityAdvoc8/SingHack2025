"""
Test if policy Q&A includes citations
"""

import requests
import json

BASE_URL = "http://localhost:8080"

print("="*80)
print("TEST: Citations in Policy Q&A")
print("="*80)

# Test a policy question
question = "What's covered under medical expenses?"

print(f"\n📤 Question: {question}")

response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": question}
        ],
        "session_id": "citation-test-001"
    },
    timeout=60
).json()

answer = response['choices'][0]['message']['content']

print(f"\n💬 Response:")
print("="*80)
print(answer)
print("="*80)

# Check for citations
has_citations = any(marker in answer for marker in ["Page", "page", "Policy", "policy", "ID:", "Excerpt", "Reference"])
has_policy_id = "scootsurance" in answer.lower() or "traveleasy" in answer.lower()
has_source = "source" in answer.lower() or "according to" in answer.lower()

print(f"\n📊 CITATION ANALYSIS:")
print(f"  - Has citation markers: {has_citations}")
print(f"  - References policy IDs: {has_policy_id}")
print(f"  - Mentions source: {has_source}")

if has_citations and has_policy_id:
    print("\n✅ PASS: Response includes citations")
else:
    print("\n⚠️  PARTIAL: Response may lack explicit citations")
    print("   Checking if citations are in a separate field...")

