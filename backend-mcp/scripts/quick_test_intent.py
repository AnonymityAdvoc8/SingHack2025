"""
Quick test of the updated intent detection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.orchestration_service import ConversationOrchestrator

db = next(get_db())
orch = ConversationOrchestrator(db)

# Test the exact user query
message = "I am 31 years old male travelling to Japan from March 1-10 for hiking, which policy would you recommend?"

print(f"Testing: {message}\n")

result = orch.handle_message(message)

print(f"🎯 Intent Detected: {result['intent']}")
print(f"📍 Destination: {result.get('trip_details', {}).get('destination_country', 'N/A')}")
print(f"🎒 Activities: {result.get('trip_details', {}).get('planned_activities', [])}")
print(f"📅 Duration: {result.get('trip_details', {}).get('trip_duration_days', 'N/A')} days")
print(f"✅ Complete: {result.get('is_complete', False)}")

# Check if Tavily was triggered
intel = result.get('real_time_intelligence', {})
if intel:
    print(f"\n🔥 Tavily Intelligence:")
    if intel.get('destination'):
        print(f"   ✅ Destination Intel: Retrieved")
    if intel.get('risks'):
        print(f"   ✅ Risk Analysis: {intel['risks'].get('overall_risk_level', 'N/A')}")
    if intel.get('medical_costs'):
        print(f"   ✅ Medical Costs: Retrieved")
else:
    print(f"\n⚠️ No Tavily intelligence (check if extraction is complete)")

# Check policy recommendations
policies = result.get('policy_recommendations', [])
print(f"\n💼 Policy Recommendations: {len(policies)} found")
for i, policy in enumerate(policies, 1):
    print(f"   {i}. {policy.get('policy_name', 'Unknown')}")

# Show answer
print(f"\n💬 Answer Preview:")
print(result.get('answer', 'No answer')[:300])

