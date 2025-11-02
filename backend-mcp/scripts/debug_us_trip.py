"""
Debug test for the US trip extraction issue
"""

import requests
import json

BASE_URL = "http://localhost:8080"
SESSION_ID = "debug-us-trip-001"

print("="*80)
print("DEBUG: US Trip Extraction Issue")
print("="*80)

# Simulate the exact query
response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "Hey, my wife and I are going on vacation to the US in January for a month. Which insurance should we get?"}
        ],
        "session_id": SESSION_ID
    },
    timeout=120  # Longer timeout for Tavily calls
).json()

print("\n📤 Question: Hey, my wife and I are going on vacation to the US in January for a month...")
print("\n💬 Response:")
print("="*80)

if "choices" in response and len(response["choices"]) > 0:
    answer = response['choices'][0]['message']['content']
    print(answer)
    print("\n" + "="*80)
    print(f"Length: {len(answer)} characters")
else:
    print("ERROR Response:")
    print(json.dumps(response, indent=2))

print("\n" + "="*80)
print("ANALYSIS:")
print("="*80)

if "choices" in response:
    answer = response['choices'][0]['message']['content']
    
    # Check if response is incomplete
    is_incomplete = "let me generate" in answer.lower() and len(answer) < 200
    has_recommendations = "scootsurance" in answer.lower() or "traveleasy" in answer.lower()
    has_pricing = "sgd $" in answer.lower() or "price:" in answer.lower()
    
    print(f"Response seems incomplete: {is_incomplete}")
    print(f"Has policy recommendations: {has_recommendations}")
    print(f"Has pricing: {has_pricing}")
    
    if is_incomplete:
        print("\n❌ BUG CONFIRMED: Response stopped after 'let me generate your quote'")
    elif not has_recommendations:
        print("\n⚠️  No recommendations provided")
    else:
        print("\n✅ Response looks complete")

