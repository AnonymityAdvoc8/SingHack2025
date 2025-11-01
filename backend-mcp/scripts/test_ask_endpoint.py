"""
Test Script: Improved Extraction + /ask Endpoint Integration
Tests that extraction properly captures destination and activities
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_ask_endpoint_with_recommendation():
    """Test the /ask endpoint with recommendation request"""
    print_section("TEST: /ask Endpoint - Recommendation with Tavily")
    
    payload = {
        "question": "I'm 31 years old male travelling to Japan in march for a hiking adventure and I love to eat. Which insurance policy would you recommend?",
        "session_id": "test_session_123"
    }
    
    print(f"\n📤 Request:")
    print(f"   POST {BASE_URL}/ask")
    print(f"   Question: {payload['question'][:80]}...")
    
    try:
        response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Response (Status {response.status_code}):")
            print(f"\n🎯 Intent: {data.get('intent')}")
            print(f"📊 API Version: {data.get('api_version')}")
            print(f"🔥 Features Used: {', '.join(data.get('features_used', []))}")
            
            # Trip details
            trip = data.get('trip_details', {})
            print(f"\n📍 Extracted Trip Details:")
            print(f"   - Destination: {trip.get('destination_country', 'NOT EXTRACTED')}")
            print(f"   - Activities: {trip.get('planned_activities', [])}")
            print(f"   - Travelers: {trip.get('travelers', [])}")
            print(f"   - Departure: {trip.get('departure_date', 'N/A')}")
            print(f"   - Duration: {trip.get('trip_duration_days', 'N/A')} days")
            
            # Tavily intelligence
            intel = data.get('real_time_intelligence', {})
            if intel:
                print(f"\n🔥 Tavily Intelligence:")
                if intel.get('destination'):
                    dest = intel['destination']
                    print(f"   ✅ Destination Intel: {len(dest.get('key_findings', []))} findings")
                if intel.get('risks'):
                    risks = intel['risks']
                    print(f"   ✅ Risk Analysis: {risks.get('overall_risk_level', 'N/A')}")
                if intel.get('medical_costs'):
                    print(f"   ✅ Medical Costs: Retrieved")
            
            # Policy recommendations
            policies = data.get('policy_recommendations', [])
            print(f"\n💼 Policy Recommendations: {len(policies)} policies")
            for i, policy in enumerate(policies[:2], 1):
                print(f"   {i}. {policy.get('policy_name', 'Unknown')}")
            
            # Answer
            answer = data.get('answer', '')
            print(f"\n💬 Generated Answer:")
            print(f"   {answer[:200]}...")
            
            # CHECK: Did we extract destination properly?
            if trip.get('destination_country'):
                print(f"\n✅ EXTRACTION SUCCESS: Destination captured!")
            else:
                print(f"\n❌ EXTRACTION FAILED: Destination not captured")
            
            # CHECK: Did we extract activities properly?
            if trip.get('planned_activities') and len(trip.get('planned_activities', [])) > 0:
                print(f"✅ EXTRACTION SUCCESS: Activities captured!")
            else:
                print(f"❌ EXTRACTION FAILED: Activities not captured")
            
            return True
            
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
        print(f"   Make sure the server is running: cd backend-mcp && uvicorn app.main:app")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_ask_endpoint_simple_question():
    """Test the /ask endpoint with simple policy question"""
    print_section("TEST: /ask Endpoint - Simple Question (No Tavily)")
    
    payload = {
        "question": "What does medical evacuation cover?"
    }
    
    print(f"\n📤 Request:")
    print(f"   POST {BASE_URL}/ask")
    print(f"   Question: {payload['question']}")
    
    try:
        response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Response (Status {response.status_code}):")
            print(f"🎯 Intent: {data.get('intent')}")
            print(f"🔥 Features Used: {', '.join(data.get('features_used', []))}")
            print(f"💬 Answer: {data.get('answer', '')[:150]}...")
            
            return True
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_health_check():
    """Test if server is running"""
    print_section("TEST: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Server not running at {BASE_URL}")
        print(f"\n💡 To start the server:")
        print(f"   cd backend-mcp")
        print(f"   source venv/bin/activate")
        print(f"   uvicorn app.main:app --reload")
        return False


def main():
    print("\n" + "="*80)
    print("🧪 /ASK ENDPOINT + EXTRACTION TESTS")
    print("="*80)
    
    # Check server first
    if not test_health_check():
        print("\n⚠️  Server is not running. Please start it first.")
        return
    
    tests = [
        ("Simple Question", test_ask_endpoint_simple_question),
        ("Recommendation with Tavily", test_ask_endpoint_with_recommendation)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n🎯 Results: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()

