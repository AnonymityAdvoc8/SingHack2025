"""
Test improved orchestration: Better intent detection and concise responses
Verifies fixes for:
1. "Why are pre-existing conditions not covered?" → Should go to policy Q&A
2. "Going with my family" → Should be recognized as trip detail
3. Follow-up questions after recommendations → Should not re-run full recommendation
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_pre_existing_question_intent():
    """Test that pre-existing condition questions route to Q&A, not trip extraction"""
    print("="*80)
    print("TEST 1: Pre-existing Condition Question Routing")
    print("="*80)
    
    messages = [
        {"role": "user", "content": "I need travel insurance for Malaysia"},
        {"role": "assistant", "content": "Great! I can help you with that. When are you planning to travel to Malaysia?"},
        {"role": "user", "content": "December 15 to December 25, I'm 45 years old"},
        {"role": "assistant", "content": "**Your Trip to Malaysia**...(policy recommendations shown)"},
    ]
    
    # Now ask about pre-existing conditions
    messages.append({"role": "user", "content": "Why are pre-existing conditions not covered?"})
    
    print(f"\n📤 User asks: {messages[-1]['content']}")
    print(f"(After receiving policy recommendations)")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer = response['choices'][0]['message']['content']
    
    print(f"\n💬 Assistant response preview: {answer[:200]}...")
    
    # Verify it's a Q&A response, not asking for trip details again
    is_asking_trip_details = any(
        phrase in answer.lower()
        for phrase in ["when are you", "where are you", "how many days", "destination"]
    )
    
    is_qa_response = any(
        phrase in answer.lower()
        for phrase in ["pre-existing", "condition", "policy", "coverage", "cover"]
    )
    
    if is_asking_trip_details:
        print("\n❌ FAILED: System is asking for trip details (wrong intent)")
        return False
    elif is_qa_response:
        print("\n✅ PASSED: System provided Q&A about pre-existing conditions")
        return True
    else:
        print("\n⚠️  UNCLEAR: Response doesn't match expected patterns")
        print(f"Full response: {answer[:500]}")
        return False


def test_family_trip_recognition():
    """Test that 'going with my family' is recognized as trip detail"""
    print("\n" + "="*80)
    print("TEST 2: Family Trip Recognition")
    print("="*80)
    
    messages = [
        {"role": "user", "content": "I need insurance"},
        {"role": "assistant", "content": "Where are you planning to travel?"},
        {"role": "user", "content": "Japan, going with my family"}
    ]
    
    print(f"\n📤 User says: {messages[-1]['content']}")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer = response['choices'][0]['message']['content']
    
    print(f"\n💬 Assistant response: {answer[:200]}...")
    
    # Should ask for dates/duration, not where again
    is_asking_about_trip = any(
        phrase in answer.lower()
        for phrase in ["when", "dates", "how long", "duration", "how many days"]
    )
    
    is_asking_where_again = "where" in answer.lower()
    
    if is_asking_where_again:
        print("\n❌ FAILED: System asking 'where' again (didn't recognize Japan)")
        return False
    elif is_asking_about_trip:
        print("\n✅ PASSED: System recognized Japan and family, asking for more details")
        return True
    else:
        print(f"\n⚠️  Response: {answer[:300]}")
        return False


def test_concise_followup_response():
    """Test that follow-up requests don't repeat all intelligence data"""
    print("\n" + "="*80)
    print("TEST 3: Concise Follow-up Responses")
    print("="*80)
    
    # First, get full recommendations
    messages = [
        {"role": "user", "content": "I'm 31 traveling to Japan from December 1-10 for hiking. Which policy?"}
    ]
    
    print(f"\n📤 Initial request: {messages[0]['content']}")
    
    response1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer1 = response1['choices'][0]['message']['content']
    messages.append({"role": "assistant", "content": answer1})
    
    print(f"\n✅ Got initial recommendation ({len(answer1)} chars)")
    
    # Now ask for more details (should be concise, not repeat all Tavily data)
    messages.append({"role": "user", "content": "Tell me more about the medical coverage"})
    
    print(f"\n📤 Follow-up: {messages[-1]['content']}")
    
    response2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer2 = response2['choices'][0]['message']['content']
    
    print(f"\n💬 Follow-up response ({len(answer2)} chars)")
    
    # Check if second response is significantly shorter (no full intelligence dump)
    has_full_intelligence_dump = all([
        "historical claims data" in answer2.lower(),
        "tavily" in answer2.lower() or "real-time" in answer2.lower(),
        len(answer2) > 1000
    ])
    
    has_medical_info = "medical" in answer2.lower()
    
    if has_full_intelligence_dump:
        print("\n⚠️  WARNING: Follow-up response includes full intelligence dump (too verbose)")
        print(f"  Length: {len(answer2)} chars (should be more concise)")
        return False
    elif has_medical_info:
        print("\n✅ PASSED: Concise follow-up response about medical coverage")
        print(f"  Length: {len(answer2)} chars (appropriate)")
        return True
    else:
        print(f"\n⚠️  Response preview: {answer2[:300]}...")
        return False


if __name__ == "__main__":
    print("\n🧪 TESTING IMPROVED ORCHESTRATION\n")
    
    results = {
        "pre_existing_intent": test_pre_existing_question_intent(),
        "family_recognition": test_family_trip_recognition(),
        "concise_followup": test_concise_followup_response()
    }
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Review fixes needed")
    print("="*80)
    
    exit(0 if all_passed else 1)

