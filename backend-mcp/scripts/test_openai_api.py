"""
Test OpenAI-Compatible Chat Completions API
Tests both streaming and non-streaming modes
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_non_streaming():
    """Test non-streaming chat completions"""
    print("="*80)
    print("TEST 1: Non-Streaming Chat Completions")
    print("="*80)
    
    payload = {
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "I am 31 years old travelling to Japan in December for 9 days for hiking. Which policy would you recommend?"}
        ],
        "stream": False
    }
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    
    print(f"\n⏳ Sending request...")
    start = time.time()
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    elapsed = time.time() - start
    
    print(f"\n✅ Response (took {elapsed:.2f}s):")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response Structure:")
        print(f"  ID: {data.get('id')}")
        print(f"  Model: {data.get('model')}")
        print(f"  Choices: {len(data.get('choices', []))}")
        print(f"  Finish Reason: {data['choices'][0].get('finish_reason')}")
        print(f"\n💬 Assistant Response:")
        print("-" * 80)
        print(data['choices'][0]['message']['content'])
        print("-" * 80)
        print(f"\n📈 Usage:")
        usage = data.get('usage', {})
        print(f"  Prompt tokens: {usage.get('prompt_tokens')}")
        print(f"  Completion tokens: {usage.get('completion_tokens')}")
        print(f"  Total tokens: {usage.get('total_tokens')}")
    else:
        print(f"\n❌ Error: {response.text}")
    
    return response.status_code == 200


def test_streaming():
    """Test streaming chat completions"""
    print("\n" + "="*80)
    print("TEST 2: Streaming Chat Completions")
    print("="*80)
    
    payload = {
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "What's the difference between Scootsurance and TravelEasy policies?"}
        ],
        "stream": True
    }
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    
    print(f"\n⏳ Streaming response...")
    print("-" * 80)
    
    start = time.time()
    
    try:
        with requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        ) as response:
            
            if response.status_code != 200:
                print(f"❌ Error ({response.status_code}): {response.text}")
                return False
            
            full_content = ""
            chunk_count = 0
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            
                            if content:
                                print(content, end='', flush=True)
                                full_content += content
                                chunk_count += 1
                                
                        except json.JSONDecodeError as e:
                            print(f"\n[Warning: JSON decode error: {e}]")
                            pass
            
            elapsed = time.time() - start
            
            print()
            print("-" * 80)
            print(f"\n✅ Streaming complete (took {elapsed:.2f}s)")
            print(f"  Chunks received: {chunk_count}")
            print(f"  Total content length: {len(full_content)} characters")
            
            return True
    
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_history():
    """Test multi-turn conversation"""
    print("\n" + "="*80)
    print("TEST 3: Conversation with History")
    print("="*80)
    
    payload = {
        "model": "travelmate-ai",
        "messages": [
            {"role": "user", "content": "I need travel insurance for Japan"},
            {"role": "assistant", "content": "I'd be happy to help! Could you tell me when you're planning to travel and for how long?"},
            {"role": "user", "content": "December 1-10, 2025, I'm 31 years old"}
        ],
        "stream": False
    }
    
    print(f"\n📤 Request (with conversation history):")
    print(f"  Messages: {len(payload['messages'])}")
    for i, msg in enumerate(payload['messages'], 1):
        print(f"  {i}. {msg['role']}: {msg['content'][:50]}...")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Response:")
        print(data['choices'][0]['message']['content'][:200] + "...")
        return True
    else:
        print(f"\n❌ Error: {response.text}")
        return False


def test_models_endpoint():
    """Test models listing endpoint"""
    print("\n" + "="*80)
    print("TEST 4: List Available Models")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/v1/models")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Models available:")
        for model in data.get('data', []):
            print(f"  - {model['id']} (owned by: {model['owned_by']})")
        return True
    else:
        print(f"\n❌ Error: {response.text}")
        return False


def main():
    print("\n" + "="*80)
    print("🤖 TravelMate AI - OpenAI-Compatible API Test Suite")
    print("="*80)
    
    # Wait for server
    print("\n⏳ Checking if server is running...")
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Server is ready\n")
    except:
        print("❌ Server not running. Start it with: python scripts/start_server.py")
        return
    
    results = {}
    
    # Run tests
    results['non_streaming'] = test_non_streaming()
    results['streaming'] = test_streaming()
    results['conversation'] = test_conversation_history()
    results['models'] = test_models_endpoint()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All tests passed! OpenAI-compatible API is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    main()

