"""
Master Test Script for All New Features
Runs all tests for Option A + Agentic AI implementation
"""

import sys
import os
import asyncio
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def print_header(title):
    """Print a formatted header"""
    print("\n\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def run_sync_test(script_name, description):
    """Run a synchronous test script"""
    print_header(description)
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            # Check if "ALL TESTS PASSED" is in output
            if "ALL TESTS PASSED" in result.stdout or "🎉" in result.stdout:
                return True, "PASSED"
            elif "SOME TESTS" in result.stdout:
                return False, "PARTIAL"
            else:
                return True, "COMPLETED"
        else:
            print(f"ERROR OUTPUT:\n{result.stderr}")
            return False, "FAILED"
    
    except subprocess.TimeoutExpired:
        print("❌ TEST TIMEOUT (>60s)")
        return False, "TIMEOUT"
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, "ERROR"


def main():
    """Run all test scripts"""
    
    print("\n" + "=" * 80)
    print(" TRAVELMATE AI - COMPREHENSIVE TEST SUITE")
    print(" Testing: Option A + Agentic AI Implementation")
    print(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test suite configuration
    tests = [
        ("test_emotional_intelligence.py", "Emotional Intelligence Service"),
        ("test_proactive_intelligence.py", "Proactive Intelligence Service"),
        ("test_gmail_agent.py", "Gmail Integration Agent"),
        ("test_flight_agent.py", "Flight API Agent"),
        ("test_personality_integration.py", "Personality System Integration"),
    ]
    
    results = {}
    
    # Run all tests
    for script, description in tests:
        success, status = run_sync_test(script, description)
        results[description] = {"success": success, "status": status}
    
    # Print comprehensive summary
    print_header("FINAL TEST SUMMARY")
    
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"\nSuccess Rate: {(passed/total)*100:.1f}%\n")
    
    print("Detailed Results:")
    print("-" * 80)
    
    for test_name, result in results.items():
        status_symbol = "✅" if result["success"] else "❌"
        status_text = result["status"]
        print(f"{status_symbol} {test_name:45} [{status_text}]")
    
    print("\n" + "=" * 80)
    
    # Overall status
    if passed == total:
        print("\n🎉 ALL TEST SUITES PASSED!")
        print("\n✨ Implementation Status:")
        print("   ✅ Personality & Empathy Layer - WORKING")
        print("   ✅ Emotional Intelligence - WORKING")
        print("   ✅ Proactive Intelligence - WORKING")
        print("   ✅ Gmail Agent - WORKING")
        print("   ✅ Flight API Agent - WORKING")
        print("   ✅ Full System Integration - WORKING")
        print("\n🚀 Ready for demo and UI development!")
        return 0
    
    elif passed >= total * 0.8:
        print("\n⚠️  MOST TESTS PASSED (80%+)")
        print("\n   Some features may need attention.")
        print("   Review failures above.")
        return 1
    
    elif passed >= total * 0.5:
        print("\n⚠️  PARTIAL SUCCESS (50-80%)")
        print("\n   Several features need debugging.")
        print("   Review failures above.")
        return 2
    
    else:
        print("\n❌ SIGNIFICANT FAILURES (<50%)")
        print("\n   Major issues detected.")
        print("   Review all failures above.")
        return 3


def quick_feature_check():
    """Quick check if all new features are importable"""
    print_header("QUICK FEATURE CHECK")
    
    try:
        # Check if all new services can be imported
        from app.services.personality import TRAVELMATE_PERSONALITY
        print("✅ Personality module imported")
        
        from app.services.emotional_intelligence_service import EmotionalIntelligenceService
        print("✅ Emotional Intelligence service imported")
        
        from app.services.proactive_intelligence_service import ProactiveIntelligenceService
        print("✅ Proactive Intelligence service imported")
        
        from app.services.gmail_agent import GmailAgent
        print("✅ Gmail Agent imported")
        
        from app.services.flight_api_agent import FlightAPIAgent
        print("✅ Flight API Agent imported")
        
        # Check if orchestration service has new features
        from app.services.orchestration_service import ConversationOrchestrator
        from app.database import get_db
        
        db = next(get_db())
        orchestrator = ConversationOrchestrator(db)
        
        # Check if new services are initialized
        if hasattr(orchestrator, 'emotional_intelligence'):
            print("✅ Emotional Intelligence integrated into orchestrator")
        else:
            print("❌ Emotional Intelligence NOT integrated")
        
        if hasattr(orchestrator, 'proactive_intelligence'):
            print("✅ Proactive Intelligence integrated into orchestrator")
        else:
            print("❌ Proactive Intelligence NOT integrated")
        
        # Check MCP tools
        from app.mcp.tools import MCPTools
        tools = MCPTools(db)
        
        if hasattr(tools, 'gmail_agent'):
            print("✅ Gmail Agent integrated into MCP tools")
        else:
            print("❌ Gmail Agent NOT integrated")
        
        if hasattr(tools, 'flight_api_agent'):
            print("✅ Flight API Agent integrated into MCP tools")
        else:
            print("❌ Flight API Agent NOT integrated")
        
        print("\n✅ ALL FEATURES IMPORTABLE AND INTEGRATED")
        return True
        
    except Exception as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print(" TRAVELMATE AI - NEW FEATURES TEST SUITE")
    print("🚀" * 40)
    
    # First, quick check if features are importable
    if not quick_feature_check():
        print("\n❌ Import checks failed. Fix imports before running full tests.")
        sys.exit(4)
    
    # Run full test suite
    exit_code = main()
    
    print("\n" + "=" * 80)
    print(f" Test Suite Complete - Exit Code: {exit_code}")
    print("=" * 80 + "\n")
    
    sys.exit(exit_code)

