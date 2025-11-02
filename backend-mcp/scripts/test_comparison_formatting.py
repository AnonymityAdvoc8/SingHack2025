"""
Test improved comparison formatting
Verifies that comparison output is well-formatted with tables and sections
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_comparison_formatting():
    """Test that policy comparison is formatted nicely"""
    print("="*80)
    print("TEST: Improved Comparison Formatting")
    print("="*80)
    
    messages = [
        {"role": "user", "content": "What's the difference between Scootsurance and TravelEasy?"}
    ]
    
    print(f"\n📤 User: {messages[0]['content']}")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": "travelmate-ai", "messages": messages, "stream": False},
        timeout=60
    ).json()
    
    answer = response['choices'][0]['message']['content']
    
    print(f"\n💬 Comparison Output:")
    print("="*80)
    print(answer)
    print("="*80)
    
    # Verify formatting elements
    has_table = "|" in answer and "---" in answer
    has_sections = "###" in answer or "##" in answer
    has_bullet_points = "\n- " in answer or "\n  - " in answer
    has_clear_structure = "Quick Comparison" in answer or "Detailed Breakdown" in answer
    
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    print(f"✅ Has table format: {has_table}")
    print(f"✅ Has sections (headers): {has_sections}")
    print(f"✅ Has bullet points: {has_bullet_points}")
    print(f"✅ Has clear structure: {has_clear_structure}")
    
    all_good = has_table and has_sections and has_bullet_points and has_clear_structure
    
    if all_good:
        print("\n🎉 PASSED: Comparison is well-formatted!")
        return True
    else:
        print("\n❌ FAILED: Comparison formatting needs improvement")
        return False

if __name__ == "__main__":
    result = test_comparison_formatting()
    exit(0 if result else 1)

