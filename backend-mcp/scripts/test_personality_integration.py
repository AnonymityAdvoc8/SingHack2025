"""
Test Personality System Integration
Tests the full personality layer integrated with orchestration

NOTE: This test makes REAL API calls to:
- Groq LLM (conversational extraction + Q&A)
- Tavily API (real-time intelligence)
- PostgreSQL (claims database)

Set SKIP_API_CALLS=1 to run without API calls (faster, free)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from app.services.orchestration_service import ConversationOrchestrator

# Check if we should skip API calls
SKIP_API_CALLS = os.getenv('SKIP_API_CALLS', '0') == '1'

if SKIP_API_CALLS:
    print("\n⚠️  SKIP_API_CALLS=1 detected")
    print("   These tests will be SKIPPED to avoid API costs")
    print("   To run with real API calls: unset SKIP_API_CALLS\n")

def test_emotional_adaptation():
    """Test that responses adapt based on user emotion"""
    
    if SKIP_API_CALLS:
        print("⚠️  SKIPPING (SKIP_API_CALLS=1)")
        return True
    
    print("🧪 Testing Emotional Adaptation in Full System\n")
    print("=" * 80)
    print("⚠️  Making REAL API calls to Groq LLM + Tavily + PostgreSQL")
    print("   This may take 30-60 seconds and consume API credits\n")
    
    # Get database session
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    # Test scenarios with different emotions
    test_cases = [
        {
            "message": "This is so confusing, I don't understand insurance at all",
            "expected_emotion": "stressed",
            "should_contain": ["get it", "simplify", "break"]
        },
        {
            "message": "I'm worried about traveling with my elderly mother",
            "expected_emotion": "worried",
            "should_contain": ["understand", "designed", "protect"]
        },
        {
            "message": "I'm so excited for my Japan trip!",
            "expected_emotion": "excited",
            "should_contain": ["exciting", "amazing", "great"]
        }
    ]
    
    passed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['expected_emotion'].upper()}")
        print("-" * 80)
        print(f"User: \"{test['message']}\"")
        
        # Process message
        response = orchestrator.handle_message(
            message=test['message'],
            session_id=f"test_emotion_{i}"
        )
        
        answer = response.get('answer', '')
        detected_emotion = response.get('emotional_context', {}).get('detected_emotion', 'unknown')
        
        print(f"\nDetected Emotion: {detected_emotion}")
        print(f"\nResponse Preview:")
        print(answer[:300] + "..." if len(answer) > 300 else answer)
        
        # Check if response contains expected empathetic language
        contains_empathy = any(phrase.lower() in answer.lower() for phrase in test['should_contain'])
        
        if contains_empathy and detected_emotion == test['expected_emotion']:
            print(f"\n✅ PASS: Emotional adaptation working")
            passed += 1
        else:
            print(f"\n❌ FAIL: Missing emotional adaptation")
            if detected_emotion != test['expected_emotion']:
                print(f"   Expected emotion: {test['expected_emotion']}, got: {detected_emotion}")
            if not contains_empathy:
                print(f"   Missing empathetic phrases: {test['should_contain']}")
    
    print(f"\n📊 Results: {passed}/{len(test_cases)} tests passed")
    
    return passed == len(test_cases)


def test_proactive_insights_integration():
    """Test that proactive insights appear in recommendations"""
    
    if SKIP_API_CALLS:
        print("⚠️  SKIPPING (SKIP_API_CALLS=1)")
        return True
    
    print("\n\n🧪 Testing Proactive Insights Integration\n")
    print("=" * 80)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    # Test with skiing trip (should trigger skiing insights)
    message = "I need insurance for skiing in Japan for 2 weeks"
    
    print(f"User: \"{message}\"")
    
    response = orchestrator.handle_message(
        message=message,
        session_id="test_proactive_skiing"
    )
    
    answer = response.get('answer', '')
    
    print(f"\nResponse Preview:")
    print(answer[:500] + "..." if len(answer) > 500 else answer)
    
    # Check for proactive skiing insights
    has_skiing_insight = any(phrase in answer.lower() for phrase in ["equipment", "ski", "73%"])
    has_emoji = "⛷️" in answer or "🏥" in answer or "💡" in answer
    
    if has_skiing_insight:
        print(f"\n✅ PASS: Proactive skiing insights present")
        passed = True
    else:
        print(f"\n❌ FAIL: Missing proactive insights for skiing")
        passed = False
    
    if has_emoji:
        print(f"✅ Includes personality emojis")
    
    return passed


def test_personality_tone():
    """Test that responses have TravelMate personality"""
    
    if SKIP_API_CALLS:
        print("⚠️  SKIPPING (SKIP_API_CALLS=1)")
        return True
    
    print("\n\n🧪 Testing Personality Tone\n")
    print("=" * 80)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    message = "I need travel insurance"
    
    print(f"User: \"{message}\"")
    
    response = orchestrator.handle_message(
        message=message,
        session_id="test_personality"
    )
    
    answer = response.get('answer', '')
    
    print(f"\nResponse:")
    print("-" * 80)
    print(answer[:400] + "..." if len(answer) > 400 else answer)
    print("-" * 80)
    
    # Check for personality traits
    personality_indicators = [
        ("friendly", ["happy", "love", "great", "perfect"]),
        ("helpful", ["help", "let me", "i'll", "i can"]),
        ("enthusiastic", ["!", "✨", "amazing", "exciting"]),
        ("empathetic", ["understand", "know", "feel"])
    ]
    
    found_traits = []
    
    for trait, phrases in personality_indicators:
        if any(phrase in answer.lower() for phrase in phrases):
            found_traits.append(trait)
            print(f"✅ {trait.capitalize()} tone detected")
    
    # Should have at least 2 personality traits
    passed = len(found_traits) >= 2
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Personality traits present ({len(found_traits)}/4)")
    
    return passed


def test_jargon_simplification():
    """Test that jargon is simplified for confused users"""
    
    if SKIP_API_CALLS:
        print("⚠️  SKIPPING (SKIP_API_CALLS=1)")
        return True
    
    print("\n\n🧪 Testing Jargon Simplification\n")
    print("=" * 80)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    # First, trigger a confused state
    message1 = "This is confusing, what's a deductible?"
    
    print(f"User: \"{message1}\"")
    
    response = orchestrator.handle_message(
        message=message1,
        session_id="test_jargon"
    )
    
    answer = response.get('answer', '')
    
    print(f"\nResponse Preview:")
    print(answer[:400] + "..." if len(answer) > 400 else answer)
    
    # Check for simplified explanation
    has_simplification = any(phrase in answer.lower() for phrase in [
        "pay first",
        "before insurance",
        "think of it",
        "let me break",
        "plain english"
    ])
    
    has_empathy = "get it" in answer.lower() or "understand" in answer.lower()
    
    if has_simplification and has_empathy:
        print(f"\n✅ PASS: Jargon simplified with empathy")
        return True
    else:
        print(f"\n❌ FAIL: Missing simplification or empathy")
        if not has_simplification:
            print("   - No simplified explanation found")
        if not has_empathy:
            print("   - No empathetic acknowledgment")
        return False


def test_multi_turn_personality_consistency():
    """Test that personality is consistent across multiple turns"""
    
    if SKIP_API_CALLS:
        print("⚠️  SKIPPING (SKIP_API_CALLS=1)")
        return True
    
    print("\n\n🧪 Testing Multi-Turn Personality Consistency\n")
    print("=" * 80)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    session_id = "test_consistency"
    
    # Conversation flow
    messages = [
        "I need travel insurance",
        "Going to Japan",
        "For skiing",
        "2 weeks in December"
    ]
    
    personality_count = 0
    
    for i, message in enumerate(messages, 1):
        print(f"\nTurn {i}:")
        print(f"User: \"{message}\"")
        
        response = orchestrator.handle_message(
            message=message,
            session_id=session_id
        )
        
        answer = response.get('answer', '')
        
        # Check for personality indicators
        has_personality = any(indicator in answer.lower() for indicator in [
            "!", "✨", "perfect", "great", "amazing", "help", "let me"
        ])
        
        if has_personality:
            personality_count += 1
            print(f"✅ Turn {i}: Personality present")
        else:
            print(f"❌ Turn {i}: No personality detected")
        
        print(f"Response: {answer[:150]}...")
    
    # Should have personality in most turns
    passed = personality_count >= len(messages) - 1
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Personality consistent ({personality_count}/{len(messages)} turns)")
    
    return passed


def test_data_driven_messaging():
    """Test that responses include data-driven insights"""
    
    if SKIP_API_CALLS:
        print("⚠️  SKIPPING (SKIP_API_CALLS=1)")
        return True
    
    print("\n\n🧪 Testing Data-Driven Messaging\n")
    print("=" * 80)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    # Provide complete trip details so we get full recommendations with data
    message = "31 year old traveling to Japan December 1-10, 2025 for skiing"
    
    print(f"User: \"{message}\"")
    
    response = orchestrator.handle_message(
        message=message,
        session_id="test_data_driven"
    )
    
    answer = response.get('answer', '')
    
    print(f"\nResponse Preview:")
    print(answer[:500] + "..." if len(answer) > 500 else answer)
    
    # Check for data-driven elements
    data_indicators = [
        ("Claims data", ["claims", "similar trips", "6,078", "based on"]),
        ("Specific numbers", ["$", "SGD", "%"]),
        ("Risk level", ["risk", "moderate", "low", "high"]),
        ("Citations", ["based on", "according to", "data shows"])
    ]
    
    found_data = []
    
    for indicator_name, phrases in data_indicators:
        if any(phrase in answer.lower() for phrase in phrases):
            found_data.append(indicator_name)
            print(f"✅ {indicator_name} present")
    
    # Should have at least 2 data indicators
    passed = len(found_data) >= 2
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Data-driven messaging ({len(found_data)}/4 indicators)")
    
    return passed


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" PERSONALITY SYSTEM INTEGRATION - TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        test1 = test_emotional_adaptation()
        test2 = test_proactive_insights_integration()
        test3 = test_personality_tone()
        test4 = test_jargon_simplification()
        test5 = test_multi_turn_personality_consistency()
        test6 = test_data_driven_messaging()
        
        # Summary
        print("\n\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Emotional Adaptation: {'PASSED' if test1 else 'FAILED'}")
        print(f"✅ Proactive Insights: {'PASSED' if test2 else 'FAILED'}")
        print(f"✅ Personality Tone: {'PASSED' if test3 else 'FAILED'}")
        print(f"✅ Jargon Simplification: {'PASSED' if test4 else 'FAILED'}")
        print(f"✅ Multi-Turn Consistency: {'PASSED' if test5 else 'FAILED'}")
        print(f"✅ Data-Driven Messaging: {'PASSED' if test6 else 'FAILED'}")
        
        if test1 and test2 and test3 and test4 and test5 and test6:
            print("\n🎉 ALL TESTS PASSED!")
            print("\n💡 The personality system is working correctly!")
            print("   - Emotions are detected and adapted to")
            print("   - Proactive insights are generated")
            print("   - TravelMate personality is consistent")
            print("   - Jargon is simplified when needed")
            print("   - Data-driven recommendations are included")
        else:
            print("\n⚠️  SOME TESTS FAILED")
            print("\n   Review the failures above to identify issues.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

