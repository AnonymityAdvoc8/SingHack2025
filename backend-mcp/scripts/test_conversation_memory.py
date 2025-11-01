"""
Test conversation memory in OpenAI-compatible API
Verifies that conversation history is properly maintained across multiple turns
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_conversation_memory():
    """Test multi-turn conversation with memory"""
    
    print("="*80)
    print("TESTING CONVERSATION MEMORY")
    print("="*80)
    
    # Turn 1: User mentions they need insurance
    print("\n📤 TURN 1: Initial request")
    messages = [
        {"role": "user", "content": "I need travel insurance"}
    ]
    
    print(f"Request: {messages[-1]['content']}")
    
    response1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=30
    )
    
    if response1.status_code != 200:
        print(f"❌ Error: {response1.status_code} - {response1.text}")
        return False
    
    data1 = response1.json()
    assistant_reply_1 = data1['choices'][0]['message']['content']
    messages.append({"role": "assistant", "content": assistant_reply_1})
    
    print(f"\n💬 Assistant: {assistant_reply_1[:200]}...")
    
    # Turn 2: User provides destination (references previous context)
    print("\n📤 TURN 2: Provide destination")
    messages.append({"role": "user", "content": "I'm going to Japan"})
    
    print(f"Request: {messages[-1]['content']}")
    print(f"(Conversation history: {len(messages)-1} messages)")
    
    response2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=30
    )
    
    if response2.status_code != 200:
        print(f"❌ Error: {response2.status_code} - {response2.text}")
        return False
    
    data2 = response2.json()
    assistant_reply_2 = data2['choices'][0]['message']['content']
    messages.append({"role": "assistant", "content": assistant_reply_2})
    
    print(f"\n💬 Assistant: {assistant_reply_2[:200]}...")
    
    # Turn 3: User provides more details (references previous context)
    print("\n📤 TURN 3: Provide travel dates and age")
    messages.append({"role": "user", "content": "December for 9 days, I'm 31 years old"})
    
    print(f"Request: {messages[-1]['content']}")
    print(f"(Conversation history: {len(messages)-1} messages)")
    
    response3 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    )
    
    if response3.status_code != 200:
        print(f"❌ Error: {response3.status_code} - {response3.text}")
        return False
    
    data3 = response3.json()
    assistant_reply_3 = data3['choices'][0]['message']['content']
    
    print(f"\n💬 Assistant: {assistant_reply_3[:500]}...")
    
    # Verify that the assistant understood the full context
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Check if final response mentions Japan (from Turn 2)
    if "japan" in assistant_reply_3.lower():
        print("✅ Context preserved: Japan mentioned in final response")
    else:
        print("❌ Context lost: Japan NOT mentioned in final response")
        return False
    
    # Check if final response mentions dates (from Turn 3)
    if "december" in assistant_reply_3.lower() or "9" in assistant_reply_3:
        print("✅ Context preserved: Travel dates mentioned in final response")
    else:
        print("❌ Context lost: Travel dates NOT mentioned in final response")
        return False
    
    # Check if final response has policy recommendations
    if "policy" in assistant_reply_3.lower() or "recommend" in assistant_reply_3.lower():
        print("✅ Response includes policy recommendations")
    else:
        print("⚠️ Response may not include policy recommendations")
    
    print("\n" + "="*80)
    print("✅ CONVERSATION MEMORY TEST PASSED!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_conversation_memory()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

