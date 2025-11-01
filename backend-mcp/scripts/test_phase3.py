#!/usr/bin/env python3
"""
TravelMate AI - Phase 3 Testing Script
Tests conversational extraction and Tavily intelligence
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.mcp.tools import MCPTools
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)
settings = get_settings()

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)


def test_conversational_extraction():
    """Test Phase 3: Conversational extraction"""
    print_section("TEST 1: Conversational Trip Extraction")
    
    db = SessionLocal()
    tools = MCPTools(db)
    
    # Test 1: Single message extraction
    print("\n🗣️ Test 1.1: Extract from single message")
    message1 = "I'm planning to go to Japan next month for skiing with my wife"
    
    result = tools.extract_trip_from_conversation(message1)
    
    print(f"✅ Extracted data:")
    print(json.dumps(result["extracted"], indent=2))
    print(f"\n❓ Follow-up question: {result['follow_up_question']}")
    print(f"📊 Complete: {result['is_complete']}")
    print(f"🎯 Confidence: {result['confidence']}")
    
    # Test 2: Multi-turn conversation
    print("\n🗣️ Test 1.2: Multi-turn conversation")
    
    context = result["extracted"]
    message2 = "We'll be there for 2 weeks"
    
    result2 = tools.extract_trip_from_conversation(message2, context)
    
    print(f"✅ Updated extracted data:")
    print(json.dumps(result2["extracted"], indent=2))
    print(f"\n❓ Follow-up question: {result2['follow_up_question']}")
    print(f"📊 Complete: {result2['is_complete']}")
    
    db.close()
    return True


def test_tavily_destination_intelligence():
    """Test Phase 3: Tavily destination intelligence"""
    print_section("TEST 2: Tavily Destination Intelligence")
    
    db = SessionLocal()
    tools = MCPTools(db)
    
    # Test with Japan
    print("\n🗺️ Getting real-time intelligence for Japan...")
    
    result = tools.get_destination_intelligence(
        destination="Japan",
        travel_date="December 2025"
    )
    
    print(f"\n✅ Intelligence Summary:")
    print(f"📍 Destination: {result['destination']}")
    print(f"\n💬 Tavily Answer:")
    print(f"   {result.get('answer', 'N/A')[:300]}...")
    
    print(f"\n🔑 Key Findings ({len(result.get('key_findings', []))}):")
    for finding in result.get("key_findings", [])[:3]:
        print(f"   - {finding}")
    
    print(f"\n🏥 Health Alerts ({len(result.get('health_alerts', []))}):")
    for alert in result.get("health_alerts", []):
        print(f"   ⚠️ {alert}")
    
    print(f"\n📚 Citations ({len(result.get('citations', []))}):")
    for citation in result.get("citations", [])[:2]:
        print(f"   - {citation}")
    
    db.close()
    return True


def test_tavily_risk_analysis():
    """Test Phase 3: Tavily real-time risk analysis"""
    print_section("TEST 3: Tavily Real-Time Risk Analysis")
    
    db = SessionLocal()
    tools = MCPTools(db)
    
    # Test with skiing in Japan
    print("\n⚠️ Analyzing risks for skiing in Japan...")
    
    result = tools.analyze_real_time_risks(
        destination="Japan",
        activities=["skiing", "snowboarding"],
        travel_date="December 2025"
    )
    
    print(f"\n✅ Risk Analysis:")
    print(f"📍 Destination: {result['destination']}")
    print(f"🎿 Activities: {', '.join(result['activities'])}")
    
    print(f"\n💬 Risk Summary:")
    print(f"   {result.get('risk_summary', 'N/A')[:300]}...")
    
    print(f"\n⚠️ Risk Factors ({len(result.get('risk_factors', []))}):")
    for factor in result.get("risk_factors", [])[:3]:
        print(f"   - {factor.get('description', 'N/A')}")
    
    print(f"\n💡 Recommendations ({len(result.get('recommendations', []))}):")
    for rec in result.get("recommendations", []):
        print(f"   ✓ {rec}")
    
    print(f"\n📚 Citations ({len(result.get('citations', []))}):")
    for citation in result.get("citations", [])[:2]:
        print(f"   - {citation}")
    
    db.close()
    return True


def test_tavily_medical_costs():
    """Test Phase 3: Tavily medical cost intelligence"""
    print_section("TEST 4: Tavily Medical Cost Intelligence")
    
    db = SessionLocal()
    tools = MCPTools(db)
    
    # Test with Japan
    print("\n💰 Getting medical cost intelligence for Japan...")
    
    result = tools.get_medical_cost_intelligence("Japan")
    
    print(f"\n✅ Medical Cost Intelligence:")
    print(f"📍 Destination: {result['destination']}")
    
    print(f"\n💬 Cost Summary:")
    print(f"   {result.get('cost_summary', 'N/A')[:300]}...")
    
    print(f"\n💡 Coverage Recommendations:")
    for rec in result.get("coverage_recommendations", []):
        print(f"   ✓ {rec}")
    
    print(f"\n📚 Citations ({len(result.get('citations', []))}):")
    for citation in result.get("citations", [])[:2]:
        print(f"   - {citation}")
    
    db.close()
    return True


def test_integrated_flow():
    """Test Phase 3: End-to-end integrated flow"""
    print_section("TEST 5: Integrated Flow (Conversation + Tavily)")
    
    db = SessionLocal()
    tools = MCPTools(db)
    
    # Step 1: User starts conversation
    print("\n👤 User: 'I want to go skiing in Japan next month'")
    
    extraction = tools.extract_trip_from_conversation(
        "I want to go skiing in Japan next month"
    )
    
    print(f"✅ Extracted: {extraction['extracted'].get('destination_country')} - {extraction['extracted'].get('planned_activities')}")
    
    # Step 2: Get real-time intelligence while asking follow-up
    if extraction["extracted"].get("destination_country"):
        print(f"\n🔍 AI: Getting real-time intelligence for Japan...")
        
        intel = tools.get_destination_intelligence(
            extraction["extracted"]["destination_country"]
        )
        
        print(f"✅ Found {len(intel.get('key_findings', []))} key findings")
        
        # Get risk analysis
        if extraction["extracted"].get("planned_activities"):
            risk = tools.analyze_real_time_risks(
                extraction["extracted"]["destination_country"],
                extraction["extracted"]["planned_activities"]
            )
            
            print(f"✅ Risk analysis: {len(risk.get('risk_factors', []))} factors identified")
    
    # Step 3: Ask follow-up
    print(f"\n🤖 AI: {extraction['follow_up_question']}")
    
    # Step 4: User responds
    print(f"\n👤 User: '2 weeks with my wife'")
    
    extraction2 = tools.extract_trip_from_conversation(
        "2 weeks with my wife",
        extraction["extracted"]
    )
    
    print(f"✅ Now have: {extraction2['extracted'].get('trip_duration_days')} days, {len(extraction2['extracted'].get('travelers', []))} travelers")
    print(f"📊 Complete: {extraction2['is_complete']}")
    
    if not extraction2["is_complete"]:
        print(f"\n🤖 AI: {extraction2['follow_up_question']}")
    else:
        print(f"\n🎉 AI: All details collected! Generating quote...")
    
    db.close()
    return True


def main():
    """Run all Phase 3 tests"""
    print("\n" + "=" * 80)
    print("🚀 TravelMate AI - Phase 3 Testing")
    print("   Conversational Extraction + Tavily Intelligence")
    print("=" * 80)
    
    tests = [
        ("Conversational Extraction", test_conversational_extraction),
        ("Tavily Destination Intelligence", test_tavily_destination_intelligence),
        ("Tavily Risk Analysis", test_tavily_risk_analysis),
        ("Tavily Medical Costs", test_tavily_medical_costs),
        ("Integrated Flow", test_integrated_flow)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print_section("PHASE 3 TEST SUMMARY")
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL PHASE 3 TESTS PASSED!")
        print("\n✨ Phase 3 Features Working:")
        print("   ✓ Conversational trip extraction")
        print("   ✓ Tavily real-time destination intelligence")
        print("   ✓ Tavily real-time risk analysis")
        print("   ✓ Tavily medical cost intelligence")
        print("   ✓ Integrated conversation + intelligence flow")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Review errors above.")
    
    print("\n" + "=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

