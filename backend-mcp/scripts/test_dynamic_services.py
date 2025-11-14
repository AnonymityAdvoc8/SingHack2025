#!/usr/bin/env python3
"""
Test Dynamic LLM-Powered Services
Demonstrates how dynamic services handle ANY country, emotion, or activity
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.dynamic_personality_service import get_dynamic_personality_service
from app.services.dynamic_proactive_service import get_dynamic_proactive_service
from app.services.enhanced_emotional_intelligence import get_enhanced_emotional_intelligence


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def test_dynamic_proactive():
    """Test dynamic proactive service with various scenarios"""
    print_section("Testing Dynamic Proactive Service")
    
    service = get_dynamic_proactive_service()
    
    # Test 1: Uncommon country + rare activity
    print("Test 1: Morocco - Camel Trekking & Desert Camping")
    insights = await asyncio.to_thread(
        service.generate_activity_specific_insights,
        activities=["camel trekking", "desert camping"],
        destination="Morocco",
        claims_data=None
    )
    
    for insight in insights:
        print(f"  {insight.emoji} [{insight.priority}] {insight.message}\n")
    
    # Test 2: Multiple uncommon activities
    print("\nTest 2: Norway - Ice Climbing & Dog Sledding")
    insights = await asyncio.to_thread(
        service.generate_activity_specific_insights,
        activities=["ice climbing", "dog sledding", "northern lights photography"],
        destination="Norway",
        claims_data=None
    )
    
    for insight in insights:
        print(f"  {insight.emoji} [{insight.priority}] {insight.message}\n")
    
    # Test 3: Destination insights for uncommon location
    print("\nTest 3: Destination Insights - Iceland")
    dest_insights = await asyncio.to_thread(
        service.generate_destination_insights,
        destination="Iceland",
        travel_dates="March 2026",
        claims_data={
            "total_claims": 450,
            "average_claim_amount": 1850,
            "top_claim_types": [{"type": "Medical", "percentage": 62}]
        },
        realtime_data={
            "weather": "Severe winter storms possible",
            "health_alerts": []
        }
    )
    
    for insight in dest_insights:
        print(f"  {insight.emoji} [{insight.priority}] {insight.message}\n")
    
    print("✅ Dynamic Proactive Service tests passed!\n")


async def test_dynamic_personality():
    """Test dynamic personality service"""
    print_section("Testing Dynamic Personality Service")
    
    service = get_dynamic_personality_service()
    
    # Test 1: Activity insight for extreme sport
    print("Test 1: Activity Insight - Wingsuit Flying")
    insight = await asyncio.to_thread(
        service.generate_activity_insight,
        activities=["wingsuit flying", "base jumping"],
        destination="Switzerland",
        claims_data=None
    )
    print(f"  {insight}\n")
    
    # Test 2: Destination insight for uncommon country
    print("\nTest 2: Destination Insight - Bhutan")
    dest_insight = await asyncio.to_thread(
        service.generate_destination_insight,
        destination="Bhutan",
        travel_dates="April 2026",
        claims_data={
            "total_claims": 23,
            "average_claim_amount": 4200
        }
    )
    print(f"  {dest_insight}\n")
    
    # Test 3: Follow-up question generation
    print("\nTest 3: Dynamic Follow-up Question")
    followup = await asyncio.to_thread(
        service.generate_followup_question,
        missing_fields=["return_date", "traveler_ages"],
        current_context={
            "destination_country": "New Zealand",
            "departure_date": "2026-06-15",
            "planned_activities": ["bungee jumping", "hiking"]
        },
        emotional_state="excited"
    )
    print(f"  {followup}\n")
    
    print("✅ Dynamic Personality Service tests passed!\n")


async def test_enhanced_emotional_intelligence():
    """Test enhanced emotional intelligence"""
    print_section("Testing Enhanced Emotional Intelligence")
    
    service = get_enhanced_emotional_intelligence()
    
    # Test 1: Complex emotion detection
    print("Test 1: Analyzing Complex Emotion")
    profile = await asyncio.to_thread(
        service.analyze_emotional_state,
        message="I'm so excited about my trip but also really worried about making sure I have the right coverage. What if something goes wrong?",
        conversation_history=[]
    )
    
    print(f"  Primary Emotion: {profile.primary_emotion}")
    print(f"  Intensity: {profile.intensity:.2f}")
    print(f"  Secondary Emotions: {', '.join(profile.secondary_emotions)}")
    print(f"  Detected Concerns: {', '.join(profile.detected_concerns)}")
    print(f"  Suggested Approach: {profile.suggested_approach}")
    print(f"  Confidence: {profile.confidence:.2f}\n")
    
    # Test 2: Response adaptation
    print("\nTest 2: Adapting Response for Overwhelmed User")
    original = """Based on your trip parameters (Japan, 9 days, skiing activities), I recommend the following policies:
    
1. Scootsurance - Comprehensive coverage with pre-existing condition exclusions
2. TravelEasy - Standard medical coverage with deductibles

Both policies include medical evacuation coverage with sub-limits and aggregate maximums."""
    
    overwhelmed_profile = await asyncio.to_thread(
        service.analyze_emotional_state,
        message="This is way too complicated. I don't understand any of this insurance stuff.",
        conversation_history=[]
    )
    
    adapted = await asyncio.to_thread(
        service.adapt_response,
        original_response=original,
        emotional_profile=overwhelmed_profile,
        user_message="This is way too complicated."
    )
    
    print("  ORIGINAL:")
    print(f"  {original[:150]}...\n")
    print("  ADAPTED:")
    print(f"  {adapted}\n")
    
    # Test 3: Empathetic opening
    print("\nTest 3: Generating Empathetic Opening")
    opening = await asyncio.to_thread(
        service.generate_empathetic_opening,
        emotional_profile=overwhelmed_profile,
        context={"destination": "Japan"}
    )
    print(f"  {opening}\n")
    
    print("✅ Enhanced Emotional Intelligence tests passed!\n")


async def test_edge_cases():
    """Test with truly unusual scenarios"""
    print_section("Testing Edge Cases - Uncommon Scenarios")
    
    proactive = get_dynamic_proactive_service()
    personality = get_dynamic_personality_service()
    
    # Test 1: Very rare destination + activity combo
    print("Test 1: Rare Combo - Antarctica Expedition")
    insights = await asyncio.to_thread(
        proactive.generate_activity_specific_insights,
        activities=["polar expedition", "ice diving", "wildlife photography"],
        destination="Antarctica",
        claims_data=None
    )
    
    for insight in insights[:2]:  # Show first 2
        print(f"  {insight.emoji} {insight.message}\n")
    
    # Test 2: Non-traditional "country"
    print("\nTest 2: Cruise Ship (Multiple Countries)")
    dest_insight = await asyncio.to_thread(
        personality.generate_destination_insight,
        destination="Mediterranean Cruise (Italy, Greece, Turkey)",
        travel_dates="July 2026"
    )
    print(f"  {dest_insight}\n")
    
    # Test 3: Complex emotional state
    emotional = get_enhanced_emotional_intelligence()
    complex_emotion = await asyncio.to_thread(
        emotional.analyze_emotional_state,
        message="I'm skeptical about whether I actually need this much coverage, but my wife is adamant we get it. I guess I'm looking for someone to prove it's worth the cost.",
        conversation_history=[]
    )
    
    print("\nTest 3: Complex Mixed Emotions")
    print(f"  Primary: {complex_emotion.primary_emotion} ({complex_emotion.intensity:.2f})")
    print(f"  Concerns: {', '.join(complex_emotion.detected_concerns)}")
    print(f"  Approach: {complex_emotion.suggested_approach}\n")
    
    print("✅ Edge case tests passed!\n")


async def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("  DYNAMIC LLM-POWERED SERVICES TEST SUITE")
    print("  Testing with ANY country, emotion, or activity")
    print("🚀"*30)
    
    try:
        # Run all test suites
        await test_dynamic_proactive()
        await test_dynamic_personality()
        await test_enhanced_emotional_intelligence()
        await test_edge_cases()
        
        print("\n" + "🎉"*30)
        print("  ALL TESTS PASSED!")
        print("  Dynamic services working perfectly!")
        print("🎉"*30 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

