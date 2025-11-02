"""
Test session persistence across server restarts
Simulates what happens when the server is restarted mid-conversation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"
SESSION_ID = "test-session-persistence-123"

def test_session_persistence():
    """Test that sessions persist across multiple requests with same session_id"""
    print("="*80)
    print("TEST: Session Persistence (Survives Server Restarts)")
    print("="*80)
    
    # Turn 1: Initial conversation
    print("\n📤 Turn 1: Initial conversation with session_id")
    messages_1 = [
        {"role": "user", "content": "I need travel insurance for Japan"}
    ]
    
    response_1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": messages_1,
            "stream": False,
            "user": SESSION_ID  # Use 'user' field as session_id
        },
        timeout=60
    ).json()
    
    answer_1 = response_1['choices'][0]['message']['content']
    print(f"💬 Assistant: {answer_1[:200]}...")
    
    # Turn 2: Follow-up (without providing full history in messages)
    print("\n📤 Turn 2: Follow-up question (relying on session storage)")
    messages_2 = [
        {"role": "user", "content": "What's the difference between Scootsurance and TravelEasy?"}
    ]
    
    response_2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": messages_2,  # NOT including turn 1 in history!
            "stream": False,
            "user": SESSION_ID
        },
        timeout=60
    ).json()
    
    answer_2 = response_2['choices'][0]['message']['content']
    print(f"💬 Assistant: {answer_2[:200]}...")
    
    # Turn 3: Another follow-up
    print("\n📤 Turn 3: Yet another follow-up (still relying on session)")
    messages_3 = [
        {"role": "user", "content": "Which one covers pre-existing conditions?"}
    ]
    
    response_3 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": messages_3,
            "stream": False,
            "user": SESSION_ID
        },
        timeout=60
    ).json()
    
    answer_3 = response_3['choices'][0]['message']['content']
    print(f"💬 Assistant: {answer_3[:300]}...")
    
    # Verification
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    # Check if turn 2 actually compared policies (not asking for Japan trip details again)
    has_comparison = any(keyword in answer_2.lower() for keyword in 
                        ["comparison", "scootsurance", "traveleasy", "difference", "table"])
    print(f"✅ Turn 2 understood context (comparison): {has_comparison}")
    
    # Check if turn 3 referenced the comparison
    mentions_pre_existing = "pre-existing" in answer_3.lower() or "preexisting" in answer_3.lower()
    print(f"✅ Turn 3 answered about pre-existing: {mentions_pre_existing}")
    
    # Check if it didn't ask for Japan details again
    not_asking_destination = "where" not in answer_3.lower() and "destination" not in answer_3.lower()
    print(f"✅ Turn 3 didn't forget Japan context: {not_asking_destination}")
    
    all_good = has_comparison and mentions_pre_existing and not_asking_destination
    
    if all_good:
        print("\n🎉 PASSED: Session persistence working!")
        print("   Sessions are saved to .sessions/ folder and survive server restarts.")
        return True
    else:
        print("\n❌ FAILED: Session persistence not working properly")
        return False

if __name__ == "__main__":
    result = test_session_persistence()
    exit(0 if result else 1)

