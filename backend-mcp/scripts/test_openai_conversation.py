"""
Test conversation memory in OpenAI-compatible API
Shows FULL responses to verify Japan is mentioned
"""

import requests
import json

BASE_URL = "http://localhost:8080"

messages = []

# Turn 1
messages.append({"role": "user", "content": "I need travel insurance"})
response1 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"model": "travelmate-ai", "messages": messages, "stream": False},
    timeout=30
).json()
messages.append({"role": "assistant", "content": response1['choices'][0]['message']['content']})

print("="*80)
print("TURN 1:")
print(f"User: {messages[-2]['content']}")
print(f"Assistant: {messages[-1]['content']}")

# Turn 2
messages.append({"role": "user", "content": "I'm going to Japan"})
response2 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"model": "travelmate-ai", "messages": messages, "stream": False},
    timeout=30
).json()
messages.append({"role": "assistant", "content": response2['choices'][0]['message']['content']})

print("\n" + "="*80)
print("TURN 2:")
print(f"User: {messages[-2]['content']}")
print(f"Assistant: {messages[-1]['content']}")

# Turn 3
messages.append({"role": "user", "content": "December for 9 days, I'm 31"})
print("\n" + "="*80)
print("TURN 3:")
print(f"User: {messages[-1]['content']}")
print(f"(Sending {len(messages)} messages in history)")

response3 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"model": "travelmate-ai", "messages": messages, "stream": False},
    timeout=60
).json()
assistant_reply_3 = response3['choices'][0]['message']['content']

print("\n" + "="*80)
print("FULL ASSISTANT RESPONSE:")
print("="*80)
print(assistant_reply_3)

print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)

if "japan" in assistant_reply_3.lower():
    print("✅ Context preserved: 'Japan' mentioned in final response")
else:
    print("❌ Context lost: 'Japan' NOT mentioned in final response")

if "december" in assistant_reply_3.lower() or "9" in assistant_reply_3 or "9-day" in assistant_reply_3.lower():
    print("✅ Context preserved: Travel dates/duration mentioned")
else:
    print("❌ Context lost: Travel dates NOT mentioned")

if "policy" in assistant_reply_3.lower() or "scootsurance" in assistant_reply_3.lower() or "traveleasy" in assistant_reply_3.lower():
    print("✅ Policy recommendations included")
else:
    print("⚠️  No policy recommendations found")

print("\n" + "="*80)
print("✅ TEST COMPLETE - Conversation memory working!" if "japan" in assistant_reply_3.lower() else "❌ TEST FAILED")
print("="*80)

