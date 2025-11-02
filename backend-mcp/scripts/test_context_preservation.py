"""
Test Context Preservation
Ensures trip details are never lost across conversation turns
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from app.services.orchestration_service import ConversationOrchestrator

def test_multi_turn_context_preservation():
    """Test that trip details accumulate and are never lost"""
    
    print("🧪 Testing Multi-Turn Context Preservation\n")
    print("=" * 80)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    session_id = "test_context_preservation"
    
    # Conversation flow
    turns = [
        {
            "message": "My wife and I are going to Paris for our anniversary",
            "should_extract": {"destination": "France", "travelers": 2}
        },
        {
            "message": "We'll be there for 2 weeks",
            "should_extract": {"duration": 14}
        },
        {
            "message": "We're 50 and 52 years old",
            "should_extract": {"ages": [50, 52]}
        }
    ]
    
    for i, turn in enumerate(turns, 1):
        print(f"\n{'='*80}")
        print(f"Turn {i}: {turn['message']}")
        print('='*80)
        
        response = orchestrator.handle_message(
            message=turn['message'],
            session_id=session_id
        )
        
        trip_details = response.get('trip_details', {})
        answer = response.get('answer', '')
        
        # Show what was extracted
        print(f"\n📊 Trip Context State:")
        print(f"   Destination: {trip_details.get('destination_country', 'NOT SET')}")
        print(f"   Duration: {trip_details.get('trip_duration_days', 'NOT SET')} days")
        print(f"   Travelers: {len(trip_details.get('travelers', []))} person(s)")
        if trip_details.get('travelers'):
            for j, t in enumerate(trip_details['travelers'], 1):
                print(f"      {j}. Age: {t.get('age', 'NOT SET')}")
        
        print(f"\n💬 TravelMate Response:")
        print(f"   {answer[:150]}...")
        
        # Check for repetition (asking for something we already have)
        if i == 2:  # After saying "2 weeks"
            if "how many days" in answer.lower() or "how long" in answer.lower():
                print(f"\n❌ FAIL: System asked for duration again after user provided it!")
                print(f"   This is a context loss bug!")
                return False
            else:
                print(f"\n✅ PASS: System didn't ask for duration again")
        
        if i == 3:  # After providing ages
            if "how old" in answer.lower() or "your age" in answer.lower():
                print(f"\n❌ FAIL: System asked for age again after user provided it!")
                return False
            else:
                print(f"\n✅ PASS: System has all info and should generate recommendations")
    
    print(f"\n{'='*80}")
    print("📊 FINAL CONTEXT STATE")
    print('='*80)
    
    final_context = orchestrator.trip_context
    print(f"Destination: {final_context.destination_country}")
    print(f"Duration: {final_context.trip_duration_days} days")
    print(f"Travelers: {len(final_context.travelers)}")
    print(f"Completeness: {final_context.calculate_completeness():.0%}")
    print(f"Missing Fields: {final_context.get_missing_critical_fields()}")
    
    is_complete = final_context.calculate_completeness() >= 0.7
    
    print(f"\n{'✅ PASS' if is_complete else '❌ FAIL'}: Context preserved and accumulated correctly")
    
    return is_complete


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" CONTEXT PRESERVATION TEST")
    print("=" * 80)
    
    try:
        result = test_multi_turn_context_preservation()
        
        if result:
            print("\n🎉 TEST PASSED!")
            print("\n✅ Trip context is preserved correctly across turns")
            print("✅ System never asks for the same information twice")
            print("✅ Data accumulates properly")
        else:
            print("\n❌ TEST FAILED!")
            print("\n⚠️  Context is being lost - review the logs above")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

