"""
Test follow-up questions after policy recommendations
Verifies that asking for more details about recommended policies 
routes to Q&A instead of re-running recommendations
"""

import requests
import json

BASE_URL = "http://localhost:8080"

messages = []

# Initial conversation to get recommendations
print("="*80)
print("STEP 1: Provide all trip details at once")
print("="*80)

messages.append({"role": "user", "content": "I'm 31 years old traveling to Japan from December 1 to December 10 for hiking. Which policy would you recommend?"})
print(f"User: {messages[-1]['content']}")

response1 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"model": "travelmate-ai", "messages": messages, "stream": False},
    timeout=60
).json()
assistant_reply_1 = response1['choices'][0]['message']['content']
messages.append({"role": "assistant", "content": assistant_reply_1})

print(f"\n💬 Assistant provided recommendations:")
print(f"  - Response length: {len(assistant_reply_1)} chars")
print(f"  - Has 'Scootsurance': {'scootsurance' in assistant_reply_1.lower()}")
print(f"  - Has 'TravelEasy': {'traveleasy' in assistant_reply_1.lower()}")
print(f"  - Has pricing: {'sgd $' in assistant_reply_1.lower()}")
print(f"  - Has 'Recommended Policies': {'recommended policies' in assistant_reply_1.lower()}")

if not ('scootsurance' in assistant_reply_1.lower() or 'recommended policies' in assistant_reply_1.lower()):
    print("\n⚠️  First response didn't include recommendations. Response:")
    print(assistant_reply_1[:300])
    print("\nSkipping follow-up test...")
    exit(1)

# Follow-up question asking for more details
print("\n" + "="*80)
print("FOLLOW-UP QUESTION - Asking for More Details")
print("="*80)

messages.append({"role": "user", "content": "Can you go more into details on what the Scootsurance policy covers?"})
print(f"\n📤 User: {messages[-1]['content']}")
print(f"(Sending {len(messages)} messages in conversation history)")

response2 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"model": "travelmate-ai", "messages": messages, "stream": False},
    timeout=60
).json()
assistant_reply_2 = response2['choices'][0]['message']['content']

print("\n" + "="*80)
print("ASSISTANT RESPONSE:")
print("="*80)
print(assistant_reply_2[:800])
if len(assistant_reply_2) > 800:
    print("... [truncated]")

# Verify the response
print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)

# Check if response is DIFFERENT from the first one (not repeating recommendations)
if assistant_reply_2 == assistant_reply_1:
    print("❌ FAILED: Response is identical to first response (re-ran recommendations)")
    print("   Expected: Detailed answer about Scootsurance policy")
    print("   Got: Same policy recommendation list")
elif "Your Trip to" in assistant_reply_2 and "Recommended Policies" in assistant_reply_2:
    print("⚠️  WARNING: Response looks like a full recommendation (may have re-run)")
    print("   Expected: Detailed Q&A about specific policy benefits")
else:
    print("✅ PASSED: Response appears to be policy Q&A (not full recommendations)")

# Check if response mentions Scootsurance specifically
if "scootsurance" in assistant_reply_2.lower():
    print("✅ Response mentions Scootsurance")
else:
    print("⚠️  Response does not mention Scootsurance")

# Check if response has detailed benefit information
detail_indicators = ["benefit", "coverage", "cover", "claim", "medical", "emergency"]
has_details = any(word in assistant_reply_2.lower() for word in detail_indicators)
if has_details:
    print("✅ Response includes detailed policy information")
else:
    print("⚠️  Response may lack detailed information")

print("\n" + "="*80)
final_result = (
    assistant_reply_2 != assistant_reply_1 and 
    "scootsurance" in assistant_reply_2.lower() and 
    has_details
)
print("✅ TEST PASSED - Follow-up questions work correctly!" if final_result else "❌ TEST FAILED")
print("="*80)

