"""
Test detailed quote follow-up flow
"""

import requests

BASE_URL = "http://localhost:8080"
SESSION_ID = "test-detailed-quote-123"

print("="*80)
print("TEST: Detailed Quote Follow-up")
print("="*80)

# Turn 1: Get recommendations
print("\n📤 Turn 1: Which insurance should we get?")
r1 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "My wife and I are going to the US in January for a month. Which insurance should we get?"}
        ],
        "session_id": SESSION_ID
    },
    timeout=120
).json()

print(f"💬 Response: {r1['choices'][0]['message']['content'][:150]}...")

# Turn 2: Ask for detailed quote
print("\n📤 Turn 2: Can you provide me with a detailed quote?")
r2 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "Can you provide me with a detailed quote?"}
        ],
        "session_id": SESSION_ID
    },
    timeout=120
).json()

answer2 = r2['choices'][0]['message']['content']

print(f"\n💬 Response:")
print("="*80)
print(answer2[:1000])
print("...")
print("="*80)

# Check if it's a comparison (not repeated recommendation)
is_comparison = "Policy Comparison" in answer2
has_table = "|" in answer2 and "Feature" in answer2
is_duplicate = answer2 == r1['choices'][0]['message']['content']

print(f"\n📊 ANALYSIS:")
print(f"  - Is comparison format: {is_comparison}")
print(f"  - Has comparison table: {has_table}")
print(f"  - Is duplicate of Turn 1: {is_duplicate}")

if is_comparison and has_table and not is_duplicate:
    print("\n✅ PASS: Detailed quote shows comparison!")
elif is_duplicate:
    print("\n❌ FAIL: Still repeating same recommendations")
else:
    print("\n⚠️  Response format different")

