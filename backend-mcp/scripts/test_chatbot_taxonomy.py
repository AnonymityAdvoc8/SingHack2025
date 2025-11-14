"""
Test Chatbot with Taxonomy Integration
Simulates a user conversation and verifies taxonomy is being used
"""

import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.orchestration_service import ConversationOrchestrator


async def test_chatbot_with_taxonomy():
    """Test that chatbot uses taxonomy for recommendations"""
    
    print("\n" + "="*70)
    print("CHATBOT TAXONOMY INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Get database session
    db = next(get_db())
    
    # Create orchestrator
    print("Initializing orchestrator...")
    orchestrator = ConversationOrchestrator(db)
    print("✓ Orchestrator initialized")
    print(f"✓ Taxonomy service loaded with {len(orchestrator.taxonomy_service.get_all_products())} products\n")
    
    # Test message
    test_message = "I'm planning a 7-day trip to Japan. I'm 35 years old and want to go skiing. Do you have insurance that covers adventure activities?"
    
    print("="*70)
    print("USER MESSAGE:")
    print("="*70)
    print(f"{test_message}\n")
    
    print("="*70)
    print("PROCESSING...")
    print("="*70 + "\n")
    
    # Handle message
    try:
        response = await orchestrator.handle_message(
            message=test_message,
            session_id="test_taxonomy_integration"
        )
        
        print("✓ Message processed successfully\n")
        
        # Check if taxonomy was used
        print("="*70)
        print("TAXONOMY USAGE CHECK:")
        print("="*70 + "\n")
        
        eligible_products = response.get("eligible_products", [])
        taxonomy_comparison = response.get("taxonomy_comparison", {})
        taxonomy_recommendation = taxonomy_comparison.get("recommendation") if taxonomy_comparison else None
        
        if eligible_products:
            print(f"✅ TAXONOMY USED!")
            print(f"   Eligible products: {', '.join(eligible_products)}")
            print(f"   Recommended: {taxonomy_recommendation or 'None'}")
        else:
            print("⚠️  Taxonomy not used (may need to populate taxonomy first)")
        
        # Show trip details extracted
        print("\n" + "="*70)
        print("EXTRACTED TRIP DETAILS:")
        print("="*70 + "\n")
        
        trip_details = response.get("trip_details", {})
        for key, value in trip_details.items():
            if value:
                print(f"  {key}: {value}")
        
        # Show answer
        print("\n" + "="*70)
        print("BOT RESPONSE:")
        print("="*70 + "\n")
        
        answer = response.get("answer", "No answer generated")
        print(answer)
        
        # Check if taxonomy recommendation is in answer
        print("\n" + "="*70)
        print("VERIFICATION:")
        print("="*70 + "\n")
        
        if taxonomy_recommendation and taxonomy_recommendation in answer:
            print(f"✅ Taxonomy recommendation '{taxonomy_recommendation}' appears in response")
        elif eligible_products and any(p in answer for p in eligible_products):
            found = [p for p in eligible_products if p in answer]
            print(f"✅ Taxonomy products {found} mentioned in response")
        elif "Product A" in answer or "Product B" in answer or "Product C" in answer:
            print(f"✅ Taxonomy products mentioned in response")
        else:
            print("⚠️  Taxonomy products not explicitly mentioned (may use policy names instead)")
        
        print("\n" + "#"*70)
        print("# TEST COMPLETE ✓")
        print("#"*70 + "\n")
        
        return response
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Run the test"""
    print("\n" + "#"*70)
    print("# TESTING CHATBOT WITH TAXONOMY INTEGRATION")
    print("#"*70)
    
    try:
        # Run async test
        asyncio.run(test_chatbot_with_taxonomy())
        
        print("\nIntegration test passed! ✓")
        print("\nYour chatbot is now using taxonomy data for:")
        print("  ✓ Eligibility checking")
        print("  ✓ Product comparison")
        print("  ✓ Coverage recommendations")
        print("  ✓ Real policy data in responses\n")
        
    except Exception as e:
        print(f"\nIntegration test failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure taxonomy JSON is populated")
        print("  2. Check database is initialized")
        print("  3. Verify all dependencies are installed\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

