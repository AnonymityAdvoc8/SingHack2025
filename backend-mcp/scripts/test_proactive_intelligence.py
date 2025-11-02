"""
Test Proactive Intelligence Service
Tests anticipatory insights generation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.proactive_intelligence_service import ProactiveIntelligenceService

def test_activity_insights():
    """Test activity-based proactive insights"""
    service = ProactiveIntelligenceService()
    
    print("🧪 Testing Activity-Based Insights\n")
    print("=" * 80)
    
    # Test different activities
    test_cases = [
        {
            "trip_data": {
                "destination_country": "Japan",
                "activities": ["skiing"],
                "trip_duration_days": 7
            },
            "expected_emoji": "⛷️",
            "should_contain": "equipment damage"
        },
        {
            "trip_data": {
                "destination_country": "Thailand",
                "activities": ["diving"],
                "trip_duration_days": 5
            },
            "expected_emoji": "🤿",
            "should_contain": "certification"
        },
        {
            "trip_data": {
                "destination_country": "Nepal",
                "activities": ["hiking"],
                "trip_duration_days": 14
            },
            "expected_emoji": "🥾",
            "should_contain": "evacuation"
        }
    ]
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        insights = service.generate_insights(
            trip_data=test["trip_data"],
            claims_data=None,
            tavily_data=None
        )
        
        # Check if we got activity insights
        activity_insights = [i for i in insights if i.emoji == test["expected_emoji"]]
        
        if activity_insights:
            insight = activity_insights[0]
            contains_text = test["should_contain"].lower() in insight.message.lower()
            
            if contains_text:
                print(f"\n✅ TEST {i}: PASS")
                passed += 1
            else:
                print(f"\n❌ TEST {i}: FAIL (missing expected text)")
            
            print(f"Activity: {test['trip_data']['activities'][0]}")
            print(f"Insight: {insight.emoji} {insight.message}")
        else:
            print(f"\n❌ TEST {i}: FAIL (no insight generated)")
        
    print(f"\n📊 Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_claims_insights():
    """Test claims-data based insights"""
    service = ProactiveIntelligenceService()
    
    print("\n\n🧪 Testing Claims-Based Insights\n")
    print("=" * 80)
    
    # Mock claims data
    trip_data = {
        "destination_country": "Japan",
        "activities": ["general"],
        "trip_duration_days": 9
    }
    
    claims_data = {
        "total_claims": 6078,
        "average_claim_amount": 1042,
        "top_claim_types": [
            {"type": "Medical", "percentage": 73.5, "count": 4467}
        ]
    }
    
    insights = service.generate_insights(
        trip_data=trip_data,
        claims_data=claims_data,
        tavily_data=None
    )
    
    # Check for claims insights
    claims_insights = [i for i in insights if i.type in ["insight", "recommendation"]]
    
    print(f"\nGenerated {len(claims_insights)} claims-based insights:")
    for insight in claims_insights:
        print(f"\n{insight.emoji} [{insight.priority.upper()}] {insight.message}")
    
    # Verify we got insights about the claims data
    has_claims_mention = any("claims" in i.message.lower() for i in claims_insights)
    has_amount_mention = any("1,042" in i.message or "1042" in i.message for i in claims_insights)
    
    passed = has_claims_mention or has_amount_mention
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Claims data integrated into insights")
    
    return passed


def test_priority_sorting():
    """Test that insights are sorted by priority"""
    service = ProactiveIntelligenceService()
    
    print("\n\n🧪 Testing Priority Sorting\n")
    print("=" * 80)
    
    # Create trip with multiple risk factors
    trip_data = {
        "destination_country": "Thailand",
        "activities": ["diving", "skiing"],  # Multiple activities
        "trip_duration_days": 14
    }
    
    claims_data = {
        "total_claims": 3500,
        "average_claim_amount": 2500,
        "top_claim_types": [
            {"type": "Medical", "percentage": 68.0}
        ]
    }
    
    tavily_data = {
        "health_alerts": [
            {"summary": "Dengue outbreak warning", "source": "WHO"}
        ],
        "travel_restrictions": None,
        "weather_alerts": "Monsoon season approaching"
    }
    
    insights = service.generate_insights(
        trip_data=trip_data,
        claims_data=claims_data,
        tavily_data=tavily_data
    )
    
    print(f"\nGenerated {len(insights)} total insights\n")
    
    # Check priority order
    priority_order = ["high", "medium", "low"]
    last_priority_index = -1
    correctly_sorted = True
    
    for insight in insights:
        current_priority_index = priority_order.index(insight.priority)
        
        if current_priority_index < last_priority_index:
            correctly_sorted = False
        
        last_priority_index = current_priority_index
        
        print(f"[{insight.priority.upper():6}] {insight.emoji} {insight.message[:80]}...")
    
    print(f"\n{'✅ PASS' if correctly_sorted else '❌ FAIL'}: Insights correctly sorted by priority")
    
    return correctly_sorted


def test_formatting():
    """Test formatting insights for display"""
    service = ProactiveIntelligenceService()
    
    print("\n\n🧪 Testing Insight Formatting\n")
    print("=" * 80)
    
    trip_data = {
        "destination_country": "Japan",
        "activities": ["skiing"],
        "trip_duration_days": 9
    }
    
    claims_data = {
        "total_claims": 6078,
        "average_claim_amount": 1042
    }
    
    tavily_data = {
        "health_alerts": [
            {"summary": "Flu season advisory", "source": "gov.sg"}
        ]
    }
    
    insights = service.generate_insights(
        trip_data=trip_data,
        claims_data=claims_data,
        tavily_data=tavily_data,
        policy_recommendations=[
            {
                "policy_name": "Scootsurance",
                "is_recommended": True,
                "benefits": [
                    {"name": "Medical Coverage", "limit": 100000}
                ],
                "covers_pre_existing": False
            }
        ]
    )
    
    # Format for display
    formatted = service.format_insights_for_display(insights)
    
    print("\nFORMATTED INSIGHTS:")
    print("-" * 80)
    print(formatted)
    print("-" * 80)
    
    # Check formatting has sections
    has_sections = "###" in formatted
    has_emojis = any(emoji in formatted for emoji in ["⚠️", "💡", "📊"])
    
    passed = has_sections and has_emojis
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Formatting includes sections and emojis")
    
    return passed


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" PROACTIVE INTELLIGENCE SERVICE - TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        test1 = test_activity_insights()
        test2 = test_claims_insights()
        test3 = test_priority_sorting()
        test4 = test_formatting()
        
        # Summary
        print("\n\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Activity Insights: {'PASSED' if test1 else 'FAILED'}")
        print(f"✅ Claims Insights: {'PASSED' if test2 else 'FAILED'}")
        print(f"✅ Priority Sorting: {'PASSED' if test3 else 'FAILED'}")
        print(f"✅ Formatting: {'PASSED' if test4 else 'FAILED'}")
        
        if test1 and test2 and test3 and test4:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

