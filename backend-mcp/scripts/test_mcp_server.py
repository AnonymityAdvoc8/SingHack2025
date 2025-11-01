#!/usr/bin/env python3
"""
TravelMate AI - Phase 2 Comprehensive Testing Script
Tests all MCP Server components with REAL data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.mcp.server import MCPServer
from app.schemas.trip import TripDetailsSchema, TravelerSchema
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


def test_resources(mcp_server):
    """Test MCP Resources Layer"""
    print_section("TEST 1: MCP Resources Layer")
    
    # Test normalized policies
    print("\n📋 Getting normalized policies...")
    policies = mcp_server.resources.get_normalized_policies()
    print(f"✅ Retrieved {len(policies)} policies")
    for policy in policies:
        print(f"   - {policy.policy_name}: {len(policy.benefits)} benefits")
    
    # Test original text
    print("\n📝 Getting original policy text...")
    if policies:
        text_data = mcp_server.resources.get_original_policy_text(policies[0].policy_id)
        text_length = len(text_data.get("text", ""))
        print(f"✅ Retrieved {text_length:,} chars of original text")
        print(f"   First 200 chars: {text_data.get('text', '')[:200]}...")
    
    # Test taxonomy schema
    print("\n🏗️  Getting taxonomy schema...")
    schema = mcp_server.resources.get_taxonomy_schema()
    print(f"✅ Taxonomy has {len(schema.get('layers', {}))} layers")
    for layer_name in schema.get("layers", {}).keys():
        print(f"   - {layer_name}")
    
    return True


def test_tools_eligibility(mcp_server):
    """Test eligibility checking"""
    print_section("TEST 2: Eligibility Checking")
    
    # Create sample trip
    trip_details = {
        "destination_country": "USA",
        "destination_region": "North America",
        "departure_date": "2025-12-01",
        "return_date": "2025-12-15",
        "trip_duration_days": 14,
        "trip_purpose": "leisure",
        "travelers": [
            {
                "age": 35,
                "has_pre_existing_conditions": False
            },
            {
                "age": 8,
                "has_pre_existing_conditions": False
            }
        ],
        "has_high_risk_activities": False,
        "planned_activities": []
    }
    
    print("\n👤 Checking eligibility for sample trip...")
    print(f"   Destination: {trip_details['destination_country']}")
    print(f"   Duration: {trip_details['trip_duration_days']} days")
    print(f"   Travelers: {len(trip_details['travelers'])}")
    
    result = mcp_server.tools.check_eligibility(trip_details)
    
    print(f"\n✅ Checked {len(result)} policies")
    for eligibility in result:
        status = "✅ ELIGIBLE" if eligibility["is_eligible"] else "❌ NOT ELIGIBLE"
        print(f"\n   {eligibility['policy_name']}: {status}")
        if eligibility["is_eligible"]:
            print(f"      Eligible travelers: {len(eligibility['eligible_travelers'])}")
            if eligibility.get("warnings"):
                for warning in eligibility["warnings"]:
                    print(f"      ⚠️  {warning}")
        else:
            for reason in eligibility.get("reasons", []):
                print(f"      ❌ {reason}")
    
    return True


def test_tools_question_answering(mcp_server):
    """Test question answering with LLM"""
    print_section("TEST 3: Question Answering with LLM")
    
    questions = [
        "What is the maximum coverage for emergency medical expenses?",
        "Are pre-existing conditions covered under these policies?",
        "What activities are excluded from coverage?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n❓ Question {i}: {question}")
        
        result = mcp_server.tools.answer_policy_question(
            question=question,
            include_citations=True
        )
        
        print(f"\n💬 Answer (confidence: {result['confidence']:.0%}):")
        print(f"   {result['answer'][:300]}...")
        
        if result.get("citations"):
            print(f"\n📚 Citations:")
            for citation in result["citations"][:2]:
                print(f"   - {citation}")
    
    return True


def test_tools_comparison(mcp_server):
    """Test policy comparison"""
    print_section("TEST 4: Policy Comparison")
    
    # Get all policy IDs
    policies = mcp_server.resources.get_normalized_policies()
    policy_ids = [p.policy_id for p in policies]
    
    if len(policy_ids) >= 2:
        print(f"\n🔍 Comparing {len(policy_ids)} policies...")
        
        result = mcp_server.tools.compare_policies(
            policy_ids=policy_ids,
            comparison_criteria=["coverage_limits", "pre_existing", "age_eligibility"]
        )
        
        print(f"\n✅ Comparison completed")
        print(f"\n🏆 Recommendation:")
        print(f"   {result.get('recommendation', 'N/A')[:300]}...")
        
        # Show comparison matrix summary
        matrix = result.get("comparison_matrix", {})
        if "benefits_comparison" in matrix:
            benefits = matrix["benefits_comparison"]
            print(f"\n📊 Compared {len(benefits)} benefit categories")
    
    return True


def test_tools_quote(mcp_server):
    """Test quote generation"""
    print_section("TEST 5: Quote Generation")
    
    # Create sample trip
    trip_details = {
        "destination_country": "Japan",
        "destination_region": "Asia",
        "departure_date": "2025-12-20",
        "return_date": "2026-01-05",
        "trip_duration_days": 16,
        "trip_purpose": "leisure",
        "travelers": [
            {
                "age": 45,
                "has_pre_existing_conditions": False
            },
            {
                "age": 42,
                "has_pre_existing_conditions": False
            }
        ],
        "has_high_risk_activities": True,
        "planned_activities": ["skiing"]
    }
    
    print("\n💰 Generating quotes for sample trip...")
    print(f"   Destination: {trip_details['destination_country']}")
    print(f"   Duration: {trip_details['trip_duration_days']} days")
    print(f"   Travelers: {len(trip_details['travelers'])}")
    print(f"   High-risk activities: Yes")
    
    result = mcp_server.tools.get_quote(trip_details=trip_details)
    
    print(f"\n✅ Generated {len(result.get('quotes', []))} quotes")
    print(f"   Quote ID: {result.get('quote_id')}")
    
    for quote in result.get("quotes", []):
        if quote.get("is_eligible"):
            status = "⭐ RECOMMENDED" if quote["policy_id"] == result.get("recommended_policy_id") else ""
            print(f"\n   💼 {quote['policy_name']} {status}")
            print(f"      Premium: ${quote['premium']:.2f} SGD")
            print(f"      Recommendation Score: {quote.get('recommendation_score', 0):.2f}")
    
    if result.get("recommendation_rationale"):
        print(f"\n💡 Recommendation:")
        print(f"   {result['recommendation_rationale']}")
    
    return True


def test_prompts(mcp_server):
    """Test prompt generation"""
    print_section("TEST 6: Prompt Templates")
    
    # Test greeting
    print("\n👋 Greeting Prompt:")
    greeting = mcp_server.prompts.greeting_prompt()
    print(greeting[:200] + "...")
    
    # Test comparison prompt
    print("\n🔍 Comparison Prompt:")
    comparison_text = mcp_server.prompts.comparison_prompt_template(
        policies=["Policy A", "Policy B"],
        comparison_result={
            "recommendation": "Policy A provides better coverage for your needs",
            "comparison_matrix": {
                "benefits_comparison": {
                    "Medical Coverage": {
                        "POL001": {"policy_name": "Policy A", "coverage_limit": 100000},
                        "POL002": {"policy_name": "Policy B", "coverage_limit": 50000}
                    }
                }
            }
        }
    )
    print(comparison_text[:300] + "...")
    
    return True


def test_mcp_protocol(mcp_server):
    """Test full MCP protocol"""
    print_section("TEST 7: MCP Protocol Requests")
    
    # Test list resources
    print("\n📋 Testing list_resources...")
    response = mcp_server.handle_request({"type": "list_resources"})
    print(f"✅ Found {len(response.get('resources', []))} resources")
    
    # Test list tools
    print("\n🛠️  Testing list_tools...")
    response = mcp_server.handle_request({"type": "list_tools"})
    print(f"✅ Found {len(response.get('tools', []))} tools")
    for tool in response.get("tools", [])[:3]:
        print(f"   - {tool['name']}")
    
    # Test call tool
    print("\n⚙️  Testing call_tool...")
    response = mcp_server.handle_request({
        "type": "call_tool",
        "parameters": {
            "tool_id": "answer_policy_question",
            "params": {
                "question": "What is covered under medical benefits?"
            }
        }
    })
    if response.get("success"):
        answer_length = len(response.get("result", {}).get("answer", ""))
        print(f"✅ Tool executed successfully ({answer_length} chars answer)")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🚀 TravelMate AI - Phase 2 MCP Server Testing")
    print("=" * 80)
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Initialize MCP server
        print("\n🔧 Initializing MCP Server...")
        mcp_server = MCPServer(db)
        print("✅ MCP Server initialized")
        
        # Run all tests
        tests = [
            ("Resources Layer", test_resources),
            ("Eligibility Checking", test_tools_eligibility),
            ("Question Answering", test_tools_question_answering),
            ("Policy Comparison", test_tools_comparison),
            ("Quote Generation", test_tools_quote),
            ("Prompt Templates", test_prompts),
            ("MCP Protocol", test_mcp_protocol)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func(mcp_server):
                    passed += 1
                else:
                    failed += 1
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                failed += 1
                print(f"❌ {test_name} FAILED: {e}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print_section("TEST SUMMARY")
        print(f"\n✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {passed + failed}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Phase 2 MCP Server is ready!")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
        
        print("\n" + "=" * 80)
        
        return failed == 0
        
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

