"""
Test Script: MCP Server + Tavily Integration
Tests that Phase 3 tools are properly exposed and working through MCP protocol
"""

import sys
from pathlib import Path

# Add backend-mcp to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.mcp.server import MCPServer
from app.utils.logger import get_logger

logger = get_logger(__name__)


def test_list_tools():
    """Test 1: Verify Phase 3 tools are listed"""
    print("\n" + "="*80)
    print("TEST 1: List MCP Tools (Should Include Phase 3 Tavily Tools)")
    print("="*80)
    
    db = next(get_db())
    server = MCPServer(db)
    
    request = {
        "type": "list_tools"
    }
    
    response = server.handle_request(request)
    
    if response["success"]:
        print("✅ MCP Server responding")
        print(f"\n📋 Total Tools Available: {len(response['tools'])}\n")
        
        phase3_tools = [
            "extract_trip_from_conversation",
            "get_destination_intelligence",
            "analyze_real_time_risks",
            "get_medical_cost_intelligence"
        ]
        
        for tool in response["tools"]:
            is_phase3 = tool["id"] in phase3_tools
            marker = "🔥 [PHASE 3]" if is_phase3 else "   "
            print(f"{marker} {tool['id']:<40} | {tool['description']}")
        
        # Verify all Phase 3 tools are present
        tool_ids = [t["id"] for t in response["tools"]]
        missing = [t for t in phase3_tools if t not in tool_ids]
        
        if missing:
            print(f"\n❌ Missing Phase 3 Tools: {missing}")
            return False
        else:
            print(f"\n✅ All Phase 3 Tools Registered!")
            return True
    else:
        print(f"❌ Error: {response.get('error')}")
        return False


def test_conversational_extraction():
    """Test 2: Call extract_trip_from_conversation through MCP"""
    print("\n" + "="*80)
    print("TEST 2: Conversational Extraction via MCP Protocol")
    print("="*80)
    
    db = next(get_db())
    server = MCPServer(db)
    
    request = {
        "type": "call_tool",
        "parameters": {
            "tool_id": "extract_trip_from_conversation",
            "params": {
                "message": "I'm planning to go to Japan next month for skiing with my wife",
                "context": None
            }
        }
    }
    
    print(f"\n📝 User Message: {request['parameters']['params']['message']}")
    
    response = server.handle_request(request)
    
    if response["success"]:
        result = response["result"]
        print(f"\n✅ Extraction Successful!")
        print(f"\n📊 Extracted Details:")
        print(f"   - Destination: {result.get('extracted', {}).get('destination')}")
        print(f"   - Activities: {result.get('extracted', {}).get('activities')}")
        print(f"   - Travelers: {result.get('extracted', {}).get('number_of_travelers')}")
        print(f"   - Complete: {result.get('is_complete')}")
        print(f"\n💬 Follow-up: {result.get('follow_up_question')}")
        return True
    else:
        print(f"❌ Error: {response.get('error')}")
        return False


def test_destination_intelligence():
    """Test 3: Call get_destination_intelligence through MCP"""
    print("\n" + "="*80)
    print("TEST 3: Tavily Destination Intelligence via MCP Protocol")
    print("="*80)
    
    db = next(get_db())
    server = MCPServer(db)
    
    request = {
        "type": "call_tool",
        "parameters": {
            "tool_id": "get_destination_intelligence",
            "params": {
                "destination": "Japan",
                "travel_date": "December 2025"
            }
        }
    }
    
    print(f"\n🌏 Destination: {request['parameters']['params']['destination']}")
    print(f"📅 Travel Date: {request['parameters']['params']['travel_date']}")
    print(f"\n⏳ Querying Tavily API...")
    
    response = server.handle_request(request)
    
    if response["success"]:
        result = response["result"]
        print(f"\n✅ Intelligence Retrieved!")
        print(f"\n📊 Summary:")
        print(f"   {result.get('summary', 'N/A')[:200]}...")
        
        if result.get("travel_advisories"):
            print(f"\n⚠️  Travel Advisories:")
            for adv in result["travel_advisories"][:2]:
                print(f"   - {adv}")
        
        if result.get("sources"):
            print(f"\n📚 Sources ({len(result['sources'])} citations):")
            for src in result["sources"][:2]:
                print(f"   - {src.get('title', 'N/A')}")
                print(f"     {src.get('url', 'N/A')}")
        
        return True
    else:
        print(f"❌ Error: {response.get('error')}")
        return False


def test_risk_analysis():
    """Test 4: Call analyze_real_time_risks through MCP"""
    print("\n" + "="*80)
    print("TEST 4: Tavily Risk Analysis via MCP Protocol")
    print("="*80)
    
    db = next(get_db())
    server = MCPServer(db)
    
    request = {
        "type": "call_tool",
        "parameters": {
            "tool_id": "analyze_real_time_risks",
            "params": {
                "destination": "Thailand",
                "activities": ["scuba diving", "motorcycle rental"],
                "travel_date": "November 2025"
            }
        }
    }
    
    print(f"\n🌏 Destination: {request['parameters']['params']['destination']}")
    print(f"🎯 Activities: {', '.join(request['parameters']['params']['activities'])}")
    print(f"\n⏳ Analyzing risks via Tavily...")
    
    response = server.handle_request(request)
    
    if response["success"]:
        result = response["result"]
        print(f"\n✅ Risk Analysis Complete!")
        print(f"\n📊 Overall Risk: {result.get('overall_risk_level', 'N/A')}")
        
        if result.get("key_risks"):
            print(f"\n⚠️  Key Risks Identified:")
            for risk in result["key_risks"][:3]:
                print(f"   - {risk}")
        
        if result.get("recommendations"):
            print(f"\n💡 Recommendations:")
            for rec in result["recommendations"][:3]:
                print(f"   - {rec}")
        
        return True
    else:
        print(f"❌ Error: {response.get('error')}")
        return False


def test_medical_costs():
    """Test 5: Call get_medical_cost_intelligence through MCP"""
    print("\n" + "="*80)
    print("TEST 5: Tavily Medical Cost Intelligence via MCP Protocol")
    print("="*80)
    
    db = next(get_db())
    server = MCPServer(db)
    
    request = {
        "type": "call_tool",
        "parameters": {
            "tool_id": "get_medical_cost_intelligence",
            "params": {
                "destination": "United States"
            }
        }
    }
    
    print(f"\n🌏 Destination: {request['parameters']['params']['destination']}")
    print(f"\n⏳ Querying medical costs via Tavily...")
    
    response = server.handle_request(request)
    
    if response["success"]:
        result = response["result"]
        print(f"\n✅ Medical Intelligence Retrieved!")
        print(f"\n📊 Cost Level: {result.get('cost_level', 'N/A')}")
        
        coverage = result.get('recommended_coverage_usd', 'N/A')
        if isinstance(coverage, (int, float)):
            print(f"💰 Recommended Coverage: ${coverage:,.0f}")
        else:
            print(f"💰 Recommended Coverage: {coverage}")
        
        if result.get("key_findings"):
            print(f"\n📝 Key Findings:")
            for finding in result["key_findings"][:3]:
                print(f"   - {finding}")
        
        return True
    else:
        print(f"❌ Error: {response.get('error')}")
        return False


def main():
    """Run all MCP + Tavily integration tests"""
    print("\n" + "="*80)
    print("🧪 MCP SERVER + TAVILY INTEGRATION TESTS")
    print("="*80)
    print("Testing that Phase 3 Tavily tools work through MCP protocol...")
    
    tests = [
        ("List Tools", test_list_tools),
        ("Conversational Extraction", test_conversational_extraction),
        ("Destination Intelligence", test_destination_intelligence),
        ("Risk Analysis", test_risk_analysis),
        ("Medical Costs", test_medical_costs)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 3 Tavily integration working through MCP!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")


if __name__ == "__main__":
    main()

