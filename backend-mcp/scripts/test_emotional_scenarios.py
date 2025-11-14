#!/usr/bin/env python3
"""
Comprehensive Emotional Intelligence Testing
Tests warmth, empathy, and personalization across diverse scenarios
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestration_service import ConversationOrchestrator
from app.database import get_db


def print_test(number: int, title: str, user_message: str, expected_qualities: list):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"Test {number}: {title}")
    print(f"{'='*70}")
    print(f"USER: \"{user_message}\"")
    print(f"\nEXPECTED QUALITIES:")
    for quality in expected_qualities:
        print(f"  - {quality}")
    print()


def assess_response(response_text: str, expected_qualities: list, scenario_name: str):
    """Assess response quality"""
    response_lower = response_text.lower()
    
    score = 0
    max_score = len(expected_qualities)
    feedback = []
    
    # Check each expected quality
    for quality in expected_qualities:
        quality_lower = quality.lower()
        
        if "celebrates" in quality_lower and any(word in response_lower for word in ["congratulations", "congrats", "celebrate", "wonderful"]):
            score += 1
            feedback.append(f"✅ {quality}")
        elif "warm" in quality_lower and any(word in response_lower for word in ["beautiful", "perfect", "amazing", "wonderful", "lovely"]):
            score += 1
            feedback.append(f"✅ {quality}")
        elif "emoji" in quality_lower and any(emoji in response_text for emoji in ["❤️", "💕", "🎉", "✨", "😊"]):
            score += 1
            feedback.append(f"✅ {quality}")
        elif "empathize" in quality_lower and any(word in response_lower for word in ["understand", "i hear you", "i get it", "makes sense"]):
            score += 1
            feedback.append(f"✅ {quality}")
        elif "reassure" in quality_lower and any(word in response_lower for word in ["peace of mind", "protected", "covered", "simple", "help"]):
            score += 1
            feedback.append(f"✅ {quality}")
        elif "enthusias" in quality_lower and ("!" in response_text or "exciting" in response_lower or "amazing" in response_lower):
            score += 1
            feedback.append(f"✅ {quality}")
        elif "specific" in quality_lower or "personal" in quality_lower:
            # Check if response mentions specific details
            if any(detail in response_text for detail in ["Tokyo", "Paris", "Bali", "50", "honeymoon", "family", "solo"]):
                score += 1
                feedback.append(f"✅ {quality}")
            else:
                feedback.append(f"❌ {quality}")
        else:
            # Generic check - assume quality met if response is > 50 chars and appropriate
            if len(response_text) > 50 and not response_text.startswith("Please check") and "🚨" not in response_text:
                score += 0.5
                feedback.append(f"⚠️ {quality} (partially)")
    
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    
    print("SYSTEM RESPONSE:")
    print(f"\"{response_text}\"")
    print(f"\nASSESSMENT ({percentage:.0f}%):")
    for item in feedback:
        print(f"  {item}")
    
    if percentage >= 90:
        print(f"\n✅ EXCELLENT - {scenario_name}")
        return "excellent"
    elif percentage >= 70:
        print(f"\n⚠️ GOOD - {scenario_name}")
        return "good"
    elif percentage >= 50:
        print(f"\n⚠️ NEEDS IMPROVEMENT - {scenario_name}")
        return "needs_improvement"
    else:
        print(f"\n❌ POOR - {scenario_name}")
        return "poor"


async def test_scenario(scenario_num: int, title: str, user_message: str, expected_qualities: list, session_id: str):
    """Test a single emotional scenario"""
    print_test(scenario_num, title, user_message, expected_qualities)
    
    db = next(get_db())
    orchestrator = ConversationOrchestrator(db)
    
    try:
        response = await orchestrator.handle_message(
            message=user_message,
            session_id=session_id,
            context=None
        )
        
        answer = response.get("answer", "No response generated")
        result = assess_response(answer, expected_qualities, title)
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return "error"


async def main():
    """Run comprehensive emotional intelligence tests"""
    print("\n" + "🧪"*35)
    print("  COMPREHENSIVE EMOTIONAL INTELLIGENCE TEST SUITE")
    print("  Testing Warmth, Empathy, Sympathy & Personalization")
    print("🧪"*35)
    
    results = {}
    
    # Test 1: Celebration - 50th Anniversary
    results['anniversary'] = await test_scenario(
        1,
        "50th Anniversary (Celebration + Joy)",
        "Hey, my wife and I are celebrating our 50th anniversary in Paris. We need help for insurance",
        [
            "Celebrates the milestone warmly",
            "Uses celebratory emoji (❤️ or 💕)",
            "Personalizes to Paris",
            "Shows genuine happiness"
        ],
        "test_anniversary"
    )
    
    # Test 2: Honeymoon - Young Couple
    results['honeymoon'] = await test_scenario(
        2,
        "Honeymoon (Excitement + Romance)",
        "We just got married! Looking for insurance for our Bali honeymoon",
        [
            "Congratulates on marriage",
            "Matches excitement/enthusiasm",
            "Uses romantic emoji",
            "Personalizes to Bali/honeymoon"
        ],
        "test_honeymoon"
    )
    
    # Test 3: Worried Parent
    results['worried_parent'] = await test_scenario(
        3,
        "Worried Parent (Anxiety + Protection)",
        "I'm really worried about taking my kids to Thailand. What if something happens? They're only 5 and 7.",
        [
            "Empathizes with parental concern",
            "Reassures with data or coverage",
            "Addresses safety concerns gently",
            "Warm and supportive tone"
        ],
        "test_worried_parent"
    )
    
    # Test 4: Solo Adventure - Overwhelmed
    results['overwhelmed'] = await test_scenario(
        4,
        "Overwhelmed Solo Traveler (Confused + Stressed)",
        "This is so confusing. I'm going backpacking alone for the first time and don't know what coverage I need. There are too many options!",
        [
            "Empathizes with confusion",
            "Simplifies the complexity",
            "Reassures they'll help",
            "Doesn't add more complexity"
        ],
        "test_overwhelmed"
    )
    
    # Test 5: Elderly Couple - Cautious
    results['elderly'] = await test_scenario(
        5,
        "Elderly Couple (Cautious + Health Concerns)",
        "My husband and I are 78 and 75. We want to visit our grandkids in Australia but we both have some health issues.",
        [
            "Shows understanding of age/health concerns",
            "Warm and respectful tone",
            "Addresses health coverage appropriately",
            "Personalizes to family visit"
        ],
        "test_elderly"
    )
    
    # Test 6: Skeptical Traveler
    results['skeptical'] = await test_scenario(
        6,
        "Skeptical Traveler (Doubt + Resistance)",
        "My friend went to Japan without insurance and was fine. Do I really need this? Seems like a waste of money.",
        [
            "Acknowledges their skepticism respectfully",
            "Provides data-backed reasoning",
            "Doesn't sound pushy or salesy",
            "Shows transparency"
        ],
        "test_skeptical"
    )
    
    # Test 7: Family Vacation - Excited
    results['family'] = await test_scenario(
        7,
        "Family Disney Trip (High Energy + Excitement)",
        "We're taking the kids to Tokyo Disneyland! They don't know yet - it's a surprise! So excited!!",
        [
            "Matches high enthusiasm",
            "Celebrates family moment",
            "Shows excitement for them",
            "Mentions kids/Disneyland specifically"
        ],
        "test_family_excited"
    )
    
    # Test 8: Business Trip - Impatient
    results['business'] = await test_scenario(
        8,
        "Business Traveler (Impatient + Practical)",
        "Quick question - need insurance for Singapore business trip next week. What's the fastest option?",
        [
            "Gets to the point quickly",
            "Professional but still warm",
            "Doesn't waste time",
            "Acknowledges urgency"
        ],
        "test_business_impatient"
    )
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70 + "\n")
    
    excellent = sum(1 for r in results.values() if r == "excellent")
    good = sum(1 for r in results.values() if r == "good")
    needs_improvement = sum(1 for r in results.values() if r == "needs_improvement")
    poor = sum(1 for r in results.values() if r == "poor")
    
    total = len(results)
    
    print(f"✅ EXCELLENT: {excellent}/{total}")
    print(f"⚠️ GOOD: {good}/{total}")
    print(f"⚠️ NEEDS IMPROVEMENT: {needs_improvement}/{total}")
    print(f"❌ POOR: {poor}/{total}")
    
    pass_rate = ((excellent + good) / total * 100) if total > 0 else 0
    
    print(f"\nOVERALL PASS RATE: {pass_rate:.0f}%")
    
    if pass_rate >= 80:
        print("\n🎉🎉🎉 EMOTIONAL INTELLIGENCE SYSTEM: EXCELLENT! 🎉🎉🎉")
        print("Your system shows genuine warmth, empathy, and personalization!")
    elif pass_rate >= 60:
        print("\n⚠️ EMOTIONAL INTELLIGENCE SYSTEM: GOOD")
        print("System works well but has room for improvement")
    else:
        print("\n❌ EMOTIONAL INTELLIGENCE SYSTEM: NEEDS WORK")
        print("System requires tuning for better emotional responses")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

