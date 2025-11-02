"""
Test compound requests: pricing + comparison
"""

import requests
import json

BASE_URL = "http://localhost:8080"
SESSION_ID = "test-compound-request-789"

def test_compound_request():
    """Test asking for both pricing and comparison in one question"""
    print("="*80)
    print("TEST: Compound Request (Pricing + Comparison)")
    print("="*80)
    
    # Setup: Get recommendations first (so we have pricing in history)
    print("\n📤 Setup: Get recommendations for Japan trip")
    r1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": [
                {"role": "user", "content": "I need insurance for Japan, leaving in December for 9 days, I'm 31"}
            ],
            "stream": False,
            "session_id": SESSION_ID
        },
        timeout=60
    ).json()
    
    print(f"💬 Got recommendations with pricing")
    
    # Test: Ask for both cost AND comparison
    print("\n📤 Test: What is the cost and can you provide the difference between them?")
    r2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "travelmate-ai",
            "messages": [
                {"role": "user", "content": "What is the cost for it and can you provide me with the difference between the two of them?"}
            ],
            "stream": False,
            "session_id": SESSION_ID
        },
        timeout=60
    ).json()
    
    answer = r2['choices'][0]['message']['content']
    
    print(f"\n💬 Response:")
    print("="*80)
    print(answer[:800])
    print("...")
    print("="*80)
    
    # Verification
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    # Check if response has pricing
    has_pricing = any(keyword in answer for keyword in ["SGD $", "Price:", "Pricing"])
    print(f"✅ Response includes pricing: {has_pricing}")
    
    # Check if response has comparison table
    has_comparison_table = "|" in answer and "Feature" in answer
    print(f"✅ Response includes comparison table: {has_comparison_table}")
    
    # Check if it's NOT showing the "policy doesn't include premium" error
    no_error = "does not include the premium" not in answer.lower()
    print(f"✅ No 'policy missing premium' error: {no_error}")
    
    # Check for policy names
    has_policies = "Scootsurance" in answer or "TravelEasy" in answer
    print(f"✅ Mentions policies: {has_policies}")
    
    all_good = has_pricing and has_comparison_table and no_error and has_policies
    
    if all_good:
        print("\n🎉 PASSED: Compound request handled correctly!")
        print("   System provided both pricing AND comparison in one answer.")
        return True
    else:
        print("\n❌ FAILED: Compound request not handled properly")
        return False

if __name__ == "__main__":
    result = test_compound_request()
    exit(0 if result else 1)

