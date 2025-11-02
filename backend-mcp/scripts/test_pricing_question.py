"""
Test pricing question fix
Verifies that "What would be the price?" after recommendations 
returns the actual prices instead of "price not found in policy documents"
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_pricing_question_after_recommendations():
    """Test that pricing questions are answered from conversation context"""
    print("="*80)
    print("TEST: Pricing Question After Recommendations")
    print("="*80)
    
    messages = []
    
    # Turn 1: Ask for insurance
    messages.append({"role": "user", "content": "Hey, I'm going on a trip to the middle-east for my birthday and looking for travel insurance"})
    
    response1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    messages.append({"role": "assistant", "content": response1['choices'][0]['message']['content']})
    print(f"✅ Turn 1 complete")
    
    # Turn 2: Provide trip details
    messages.append({"role": "user", "content": "Going to Egypt for 2 weeks in December"})
    
    response2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer2 = response2['choices'][0]['message']['content']
    messages.append({"role": "assistant", "content": answer2})
    
    print(f"✅ Turn 2 complete - Got recommendations ({len(answer2)} chars)")
    
    # Check if recommendations include pricing
    has_pricing = "sgd $" in answer2.lower() or "price:" in answer2.lower()
    print(f"  Recommendations include pricing: {has_pricing}")
    
    # Turn 3: Ask about pricing
    messages.append({"role": "user", "content": "What would be the price for the insurance?"})
    
    print(f"\n📤 User asks: {messages[-1]['content']}")
    
    response3 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer3 = response3['choices'][0]['message']['content']
    
    print(f"\n💬 Assistant response:")
    print("-" * 80)
    print(answer3[:500])
    if len(answer3) > 500:
        print("... [truncated]")
    print("-" * 80)
    
    # Verify the response
    answer_lower = answer3.lower()
    
    # BAD: Policy documents don't include pricing
    has_bad_response = any([
        "does not include the premium" in answer_lower,
        "not provided in any of the policy" in answer_lower,
        "contact the insurance provider" in answer_lower,
        "visit their website" in answer_lower
    ])
    
    # GOOD: Shows actual prices
    has_good_response = any([
        "sgd $" in answer_lower,
        "price" in answer_lower and ("scootsurance" in answer_lower or "traveleasy" in answer_lower)
    ])
    
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    if has_bad_response:
        print("❌ FAILED: System searched policy PDFs (which don't have pricing)")
        print("   Got: 'policy does not include premium' or 'contact provider'")
        return False
    elif has_good_response:
        print("✅ PASSED: System returned actual pricing from conversation context")
        print("   Got: Pricing information (SGD $...)")
        return True
    else:
        print("⚠️  UNCLEAR: Response doesn't match expected patterns")
        print(f"   Full response: {answer3[:300]}...")
        return False


if __name__ == "__main__":
    print("\n🧪 TESTING PRICING QUESTION FIX\n")
    
    result = test_pricing_question_after_recommendations()
    
    print("\n" + "="*80)
    if result:
        print("🎉 TEST PASSED! Pricing questions work correctly.")
    else:
        print("❌ TEST FAILED - Pricing questions not working")
    print("="*80)
    
    exit(0 if result else 1)

