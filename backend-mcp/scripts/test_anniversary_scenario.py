#!/usr/bin/env python3
"""
Test the 50th Anniversary Paris Scenario
Debug why the response is bureaucratic instead of warm
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestration_service import ConversationOrchestrator
from app.database import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


async def test_anniversary_scenario():
    """Test the 50th anniversary Paris scenario"""
    
    print_section("Testing: 50th Anniversary Paris Scenario")
    
    # User message
    user_message = "Hey, my wife and I are celebrating our 50th anniversary in Paris. We need help for insurance"
    
    print(f"USER MESSAGE:\n{user_message}\n")
    
    # Create orchestrator
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    # Process message
    print("Processing message...\n")
    
    try:
        response = await orchestrator.handle_message(
            message=user_message,
            session_id="test_anniversary_session",
            context=None
        )
        
        # Show the answer
        print_section("SYSTEM RESPONSE")
        print(response.get("answer", "No answer generated"))
        
        # Show emotional analysis
        print_section("Emotional Analysis")
        emotional_context = response.get("emotional_context", {})
        if emotional_context:
            print(f"Detected Emotion: {emotional_context.get('detected_emotion')}")
            print(f"Intensity: {emotional_context.get('intensity', 'N/A')}")
            print(f"Secondary Emotions: {emotional_context.get('secondary_emotions', [])}")
            print(f"Concerns: {emotional_context.get('concerns', [])}")
            print(f"Confidence: {emotional_context.get('confidence')}")
        else:
            print("❌ No emotional context detected!")
        
        # Show intent
        print_section("Intent Classification")
        print(f"Intent: {response.get('intent', 'unknown')}")
        
        # Show trip details extracted
        print_section("Trip Details Extracted")
        trip_details = response.get("trip_details", {})
        if trip_details:
            print(f"Destination: {trip_details.get('destination_country', 'Not extracted')}")
            print(f"Travelers: {trip_details.get('num_travelers', trip_details.get('travelers', 'Not extracted'))}")
            print(f"Completeness: {trip_details.get('is_complete', False)}")
        else:
            print("❌ No trip details extracted!")
        
        # Check if response is appropriate
        print_section("Response Quality Check")
        answer_lower = response.get("answer", "").lower()
        
        # Good indicators
        good_signs = []
        if "congratulations" in answer_lower or "congrats" in answer_lower or "celebrate" in answer_lower:
            good_signs.append("✅ Celebrates anniversary")
        if "50" in response.get("answer", "") or "fifty" in answer_lower:
            good_signs.append("✅ Acknowledges milestone")
        if any(emoji in response.get("answer", "") for emoji in ["🎉", "❤️", "✨", "💕"]):
            good_signs.append("✅ Uses celebratory emoji")
        if "paris" in answer_lower and ("romantic" in answer_lower or "beautiful" in answer_lower or "perfect" in answer_lower):
            good_signs.append("✅ Personalizes for Paris")
        
        # Bad indicators
        bad_signs = []
        if "🚨" in response.get("answer", ""):
            bad_signs.append("❌ Uses warning emoji (inappropriate for celebration)")
        if response.get("answer", "").lower().startswith("please check") or response.get("answer", "").lower().startswith("be advised"):
            bad_signs.append("❌ Starts with bureaucratic language")
        if "advisory" in answer_lower or "alert" in answer_lower in answer_lower[:200]:
            bad_signs.append("❌ Leads with travel warnings (bad priority)")
        if not any(word in answer_lower for word in ["congratulations", "celebrate", "wonderful", "exciting", "amazing"]):
            bad_signs.append("❌ Missing celebratory language")
        
        print("\nGood Signs:")
        if good_signs:
            for sign in good_signs:
                print(f"  {sign}")
        else:
            print("  ⚠️ No good signs detected")
        
        print("\nBad Signs:")
        if bad_signs:
            for sign in bad_signs:
                print(f"  {sign}")
        else:
            print("  ✅ No bad signs detected")
        
        # Overall assessment
        print_section("Overall Assessment")
        if len(good_signs) >= 3 and len(bad_signs) == 0:
            print("✅ EXCELLENT - Response is warm, personal, and appropriate!")
        elif len(good_signs) >= 2 and len(bad_signs) <= 1:
            print("⚠️ GOOD - Response is decent but could be improved")
        elif len(good_signs) >= 1:
            print("⚠️ NEEDS IMPROVEMENT - Response misses the emotional context")
        else:
            print("❌ POOR - Response is bureaucratic and inappropriate for celebration")
        
    except Exception as e:
        print(f"\n❌ Error processing message: {str(e)}\n")
        import traceback
        traceback.print_exc()


async def main():
    """Run the test"""
    print("\n" + "🎂"*35)
    print("  50th ANNIVERSARY PARIS SCENARIO TEST")
    print("  Testing emotional intelligence & personalization")
    print("🎂"*35)
    
    await test_anniversary_scenario()
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

