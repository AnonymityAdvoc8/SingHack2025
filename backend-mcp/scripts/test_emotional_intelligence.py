"""
Test Emotional Intelligence Service
Tests emotion detection and response adaptation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.emotional_intelligence_service import EmotionalIntelligenceService

def test_emotion_detection():
    """Test emotion detection from user messages"""
    service = EmotionalIntelligenceService()
    
    print("🧪 Testing Emotional Intelligence Detection\n")
    print("=" * 80)
    
    # Test cases
    test_messages = [
        {
            "message": "This is so confusing, I don't understand any of this",
            "expected_emotion": "stressed"
        },
        {
            "message": "I'm worried about traveling with my elderly mother who has diabetes",
            "expected_emotion": "worried"
        },
        {
            "message": "I'm so excited! Can't wait for this trip to Japan!",
            "expected_emotion": "excited"
        },
        {
            "message": "This is ridiculous, insurance is too complicated",
            "expected_emotion": "frustrated"
        },
        {
            "message": "Is this legit? Can I trust these recommendations?",
            "expected_emotion": "skeptical"
        },
        {
            "message": "I need travel insurance for my trip",
            "expected_emotion": "neutral"
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_messages:
        message = test["message"]
        expected = test["expected_emotion"]
        
        # Detect emotion
        context = service.detect_emotion(message)
        
        # Check result
        success = context.state == expected
        status = "✅ PASS" if success else "❌ FAIL"
        
        if success:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}")
        print(f"Message: \"{message}\"")
        print(f"Expected: {expected}")
        print(f"Detected: {context.state} (confidence: {context.confidence:.1%})")
        if context.indicators:
            print(f"Indicators: {', '.join(context.indicators)}")
        print(f"Response Prefix: \"{context.response_prefix[:80]}...\"")
        print(f"Adjustment: {context.adjustment}")
    
    print("\n" + "=" * 80)
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(test_messages)} tests")
    
    return passed == len(test_messages)


def test_response_adaptation():
    """Test how responses are adapted based on emotion"""
    service = EmotionalIntelligenceService()
    
    print("\n\n🧪 Testing Response Adaptation\n")
    print("=" * 80)
    
    # Original response (typical insurance response)
    original_response = """
Based on your trip parameters, I recommend TravelEasy Pre-Ex Policy.

Coverage includes:
- Medical expenses up to $150,000
- Trip cancellation coverage
- Pre-existing condition coverage with deductible of $500

Premium: SGD $1,450.00
"""
    
    print("\nORIGINAL RESPONSE:")
    print("-" * 80)
    print(original_response)
    
    # Test with different emotions
    emotions_to_test = [
        ("stressed", "This is so confusing"),
        ("worried", "I'm worried about my mother's health"),
        ("excited", "I'm so excited for this trip!"),
        ("frustrated", "This is too complicated"),
        ("skeptical", "Is this really the best option?")
    ]
    
    for emotion_name, trigger_message in emotions_to_test:
        # Detect emotion
        context = service.detect_emotion(trigger_message)
        
        # Adapt response
        adapted = service.adapt_response(original_response, context)
        
        print(f"\n\n{'=' * 80}")
        print(f"EMOTION: {emotion_name.upper()} (from: \"{trigger_message}\")")
        print(f"{'=' * 80}")
        print("\nADAPTED RESPONSE:")
        print("-" * 80)
        print(adapted)
    
    return True


def test_confusion_detection():
    """Test detection of specific confusion areas"""
    service = EmotionalIntelligenceService()
    
    print("\n\n🧪 Testing Confusion Area Detection\n")
    print("=" * 80)
    
    test_cases = [
        ("What's a deductible?", ["deductible"]),
        ("I don't understand pre-existing conditions", ["pre_existing"]),
        ("How do I make a claim?", ["claims"]),
        ("What's not covered?", ["exclusions"]),
        ("Explain medical coverage", ["medical_coverage"])
    ]
    
    for message, expected_areas in test_cases:
        confusion_areas = service.detect_confusion_areas(message)
        
        print(f"\nMessage: \"{message}\"")
        print(f"Detected Areas: {confusion_areas}")
        print(f"Expected: {expected_areas}")
        
        # Check if at least one expected area was detected
        found = any(area in confusion_areas for area in expected_areas)
        status = "✅ PASS" if found else "⚠️  PARTIAL"
        print(f"Status: {status}")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" EMOTIONAL INTELLIGENCE SERVICE - TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        test1 = test_emotion_detection()
        test2 = test_response_adaptation()
        test3 = test_confusion_detection()
        
        # Summary
        print("\n\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Emotion Detection: {'PASSED' if test1 else 'FAILED'}")
        print(f"✅ Response Adaptation: {'PASSED' if test2 else 'FAILED'}")
        print(f"✅ Confusion Detection: {'PASSED' if test3 else 'FAILED'}")
        
        if test1 and test2 and test3:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

