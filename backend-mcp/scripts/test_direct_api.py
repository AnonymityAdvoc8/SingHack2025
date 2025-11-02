"""
Test directly against the backend to see the FULL response
Bypasses JAN.ai to see what the server actually returns
"""

import requests
import json

BASE_URL = "http://localhost:8080"

print("="*80)
print("DIRECT API TEST (Bypassing JAN.ai)")
print("="*80)

# Test with the exact same question
payload = {
    "model": "travelmate-ai",
    "messages": [
        {"role": "user", "content": "Hey, my wife and I are going on vacation to the US in January for a month. Which insurance should we get?"}
    ],
    "session_id": "direct-test-999",
    "stream": False  # Explicitly disable streaming
}

print(f"\n📤 Sending request to: {BASE_URL}/v1/chat/completions")
print(f"📤 Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        timeout=120
    )
    
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"]
            
            print(f"\n💬 FULL RESPONSE ({len(answer)} chars):")
            print("="*80)
            print(answer)
            print("="*80)
            
            # Analysis
            print(f"\n📊 ANALYSIS:")
            print(f"  - Has headers (##): {'##' in answer}")
            print(f"  - Has policy names: {'Scootsurance' in answer or 'TravelEasy' in answer}")
            print(f"  - Has pricing: {'SGD $' in answer or 'Price:' in answer}")
            print(f"  - Stops at 'generate quote': {answer.strip().endswith('generate your quote.')}")
            
            if answer.strip().endswith("generate your quote."):
                print("\n❌ BUG: Response ends prematurely!")
            elif len(answer) > 500:
                print("\n✅ Response looks complete")
            else:
                print("\n⚠️  Response seems short")
        else:
            print("\n❌ No choices in response")
            print(json.dumps(result, indent=2))
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("\n❌ Request timed out after 120 seconds")
except Exception as e:
    print(f"\n❌ Error: {e}")

