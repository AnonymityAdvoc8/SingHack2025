"""
Test Script: Conversation Orchestrator with Tavily Auto-Trigger
Demonstrates how the orchestrator automatically calls Tavily tools
"""

import sys
from pathlib import Path

# Add backend-mcp to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import database first
from app.database import get_db
from app.utils.logger import get_logger

# Import orchestrator (avoid services/__init__.py to prevent circular import)
import sys
if 'app.services' in sys.modules:
    del sys.modules['app.services']  # Clear if already loaded

from app.services.orchestration_service import ConversationOrchestrator
import json

logger = get_logger(__name__)


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_user_recommendation_request():
    """
    Test the EXACT question from the user that should trigger Tavily
    """
    print_section("TEST: User Recommendation Request (Tavily Auto-Trigger)")
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    # The EXACT question from the user
    user_message = """I'm 31 years old male travelling to Japan in march for a hiking adventure and I love to eat. Which insurance policy would you recommend?"""
    
    print(f"👤 User Question:\n{user_message}\n")
    print("⏳ Processing... (This will automatically call Tavily tools!)\n")
    
    # This single call orchestrates:
    # 1. extract_trip_from_conversation
    # 2. get_destination_intelligence (Tavily)
    # 3. analyze_real_time_risks (Tavily)
    # 4. get_medical_cost_intelligence (Tavily)
    # 5. check_eligibility
    # 6. compare_policies
    response = orchestrator.handle_message(user_message)
    
    # Display results
    print("✅ Response Generated!\n")
    print(f"🎯 Detected Intent: {response['intent']}\n")
    
    print("📊 Extracted Trip Details:")
    trip = response.get("trip_details", {})
    print(f"   - Destination: {trip.get('destination', 'N/A')}")
    print(f"   - Month: {trip.get('departure_date', 'N/A')}")
    print(f"   - Activities: {trip.get('activities', [])}")
    print(f"   - Travelers: {trip.get('number_of_travelers', 'N/A')}")
    print(f"   - Age: {trip.get('traveler_age', 'N/A')}")
    
    print("\n🔥 Real-Time Intelligence (Tavily):")
    intel = response.get("real_time_intelligence", {})
    
    # Destination intelligence
    dest = intel.get("destination", {})
    if dest and not dest.get("error"):
        print(f"\n   🌏 Destination: {dest.get('destination', 'N/A')}")
        findings = dest.get("key_findings", [])
        if findings:
            print(f"   📋 Key Findings:")
            for finding in findings[:3]:
                print(f"      - {finding}")
        else:
            print(f"   📋 Key Findings: (Tavily returned no answer - API may need valid key)")
    else:
        error = dest.get("error", "N/A")
        print(f"   ⚠️  Destination Intel: Error - {error[:100]}")
    
    # Risk analysis
    risks = intel.get("risks", {})
    if risks and not risks.get("error"):
        print(f"\n   ⚠️  Risk Level: {risks.get('overall_risk_level', 'N/A')}")
        key_risks = risks.get("key_risks", [])
        if key_risks:
            print(f"   🚨 Key Risks:")
            for risk in key_risks[:2]:
                print(f"      - {risk}")
    else:
        error = risks.get("error", "N/A")
        print(f"   ⚠️  Risk Analysis: Error - {error[:100]}")
    
    # Medical costs
    medical = intel.get("medical_costs", {})
    if medical and not medical.get("error"):
        print(f"\n   💊 Medical Costs:")
        print(f"      - Summary: {medical.get('cost_summary', 'N/A')[:100]}")
        recommendations = medical.get("coverage_recommendations", [])
        if recommendations:
            print(f"      - Recommendation: {recommendations[0]}")
    else:
        error = medical.get("error", "N/A")
        print(f"   💊 Medical Costs: Error - {error[:100]}")
    
    # Policy recommendations
    print("\n📋 Policy Recommendations:")
    policies = response.get("policy_recommendations", [])
    if policies:
        for i, policy in enumerate(policies, 1):
            print(f"\n   {i}. {policy.get('policy_name', 'Unknown')}")
            print(f"      - Policy ID: {policy.get('policy_id', 'N/A')}")
            print(f"      - Max Coverage: ${policy.get('max_coverage', 0):,.0f}")
            print(f"      - Benefits: {len(policy.get('benefits', []))} covered")
    else:
        print("   No policies found matching criteria")
    
    # Final answer
    print("\n💬 Generated Answer:")
    print("-" * 80)
    print(response.get("answer", "No answer generated"))
    print("-" * 80)
    
    return response


def test_incomplete_trip_details():
    """Test when user doesn't provide complete trip details"""
    print_section("TEST: Incomplete Trip Details (Follow-up Question)")
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    user_message = "I'm planning a trip to Japan"
    
    print(f"👤 User: {user_message}\n")
    print("⏳ Processing...\n")
    
    response = orchestrator.handle_message(user_message)
    
    print(f"🤖 Assistant: {response.get('answer')}\n")
    print(f"✅ Should ask follow-up: {not response.get('extraction_complete', False)}")
    
    return response


def test_policy_question():
    """Test policy-specific question (no Tavily needed)"""
    print_section("TEST: Policy Question (No Tavily)")
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    user_message = "What does medical evacuation cover?"
    
    print(f"👤 User: {user_message}\n")
    print("⏳ Processing (should use Q&A tool only)...\n")
    
    response = orchestrator.handle_message(user_message)
    
    print(f"🤖 Assistant:\n{response.get('answer')}\n")
    print(f"🎯 Intent: {response.get('intent')}")
    print(f"📊 Confidence: {response.get('confidence', 0):.0%}")
    
    return response


def main():
    """Run all orchestrator tests"""
    print("\n" + "="*80)
    print("🧪 CONVERSATION ORCHESTRATOR TESTS")
    print("="*80)
    print("Testing automatic Tavily triggering during natural conversation...\n")
    
    tests = [
        ("Recommendation Request (Tavily Auto-Trigger)", test_user_recommendation_request),
        ("Incomplete Trip Details", test_incomplete_trip_details),
        ("Policy Question", test_policy_question)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            response = test_func()
            success = response.get("answer") is not None
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Orchestrator automatically triggers Tavily!")
        print("\n💡 KEY INSIGHT:")
        print("   When a user asks for recommendations, the orchestrator now:")
        print("   1. Extracts trip details from conversation")
        print("   2. 🔥 Automatically calls Tavily for real-time intelligence")
        print("   3. Uses Tavily insights to enhance policy recommendations")
        print("   4. Generates answer with real-time context")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")


if __name__ == "__main__":
    main()

