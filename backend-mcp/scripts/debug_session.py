"""
Debug session loading to see what's being saved/loaded
"""

import requests
import json

BASE_URL = "http://localhost:8080"
SESSION_ID = "debug-session-456"

def debug_session():
    """Debug what's happening with session storage"""
    print("="*80)
    print("DEBUG: Session Storage")
    print("="*80)
    
    # Turn 1
    print("\n📤 Turn 1: I need insurance for Japan")
    r1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": [
                {"role": "user", "content": "I need insurance for Japan"}
            ],
            "stream": False,
            "session_id": SESSION_ID
        },
        timeout=60
    ).json()
    
    print(f"💬 Response: {r1['choices'][0]['message']['content'][:150]}...")
    
    # Turn 2
    print("\n📤 Turn 2: What's the difference between Scootsurance and TravelEasy?")
    r2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": [
                {"role": "user", "content": "What's the difference between Scootsurance and TravelEasy?"}
            ],
            "stream": False,
            "session_id": SESSION_ID
        },
        timeout=60
    ).json()
    
    print(f"💬 Response: {r2['choices'][0]['message']['content'][:150]}...")
    
    # Check if it compared (not asking about trip)
    is_comparison = "comparison" in r2['choices'][0]['message']['content'].lower()
    print(f"\n✅ Turn 2 is comparison: {is_comparison}")
    
    # Turn 3
    print("\n📤 Turn 3: Which one is better for pre-existing conditions?")
    r3 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": [
                {"role": "user", "content": "Which one is better for pre-existing conditions?"}
            ],
            "stream": False,
            "session_id": SESSION_ID
        },
        timeout=60
    ).json()
    
    print(f"💬 Response: {r3['choices'][0]['message']['content'][:300]}...")
    
    # Check if it answered (not asking where you're going)
    not_asking = "where" not in r3['choices'][0]['message']['content'].lower()
    mentions_policy = any(keyword in r3['choices'][0]['message']['content'].lower() 
                         for keyword in ["traveleasy pre-existing", "pre-existing", "condition"])
    
    print(f"\n✅ Turn 3 didn't forget context: {not_asking}")
    print(f"✅ Turn 3 referenced policies: {mentions_policy}")
    
    if is_comparison and not_asking and mentions_policy:
        print("\n🎉 Session persistence working correctly!")
    else:
        print("\n❌ Session persistence has issues")
        print(f"   - Turn 2 comparison: {is_comparison}")
        print(f"   - Turn 3 context preserved: {not_asking}")
        print(f"   - Turn 3 policy reference: {mentions_policy}")

if __name__ == "__main__":
    debug_session()

