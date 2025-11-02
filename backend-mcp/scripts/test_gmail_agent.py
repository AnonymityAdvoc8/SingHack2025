"""
Test Gmail Agent
Tests email scanning and booking extraction
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.gmail_agent import GmailAgent

async def test_gmail_authorization():
    """Test Gmail OAuth authorization flow (mock)"""
    agent = GmailAgent()
    
    print("🧪 Testing Gmail Authorization\n")
    print("=" * 80)
    
    # Mock authorization
    auth_result = await agent.authorize_user("mock_auth_code_123")
    
    print(f"Authorization Status: {auth_result.get('authorized')}")
    print(f"User Email: {auth_result.get('user_email')}")
    print(f"Scopes: {auth_result.get('scope')}")
    print(f"Message: {auth_result.get('message')}")
    
    passed = auth_result.get('authorized') == True
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Authorization flow completed")
    
    return passed


async def test_booking_search():
    """Test searching for booking confirmations"""
    agent = GmailAgent()
    
    print("\n\n🧪 Testing Booking Search\n")
    print("=" * 80)
    
    # Search for bookings (returns mock data)
    bookings = await agent.search_for_bookings(days_back=90, days_forward=365)
    
    print(f"\nFound {len(bookings)} bookings:")
    
    for i, booking in enumerate(bookings, 1):
        print(f"\n{i}. {booking.subject}")
        print(f"   Type: {booking.booking_type}")
        print(f"   From: {booking.sender}")
        print(f"   Confidence: {booking.confidence:.1%}")
        print(f"   Data: {list(booking.extracted_data.keys())}")
    
    # Verify we got expected bookings
    has_flight = any(b.booking_type == "flight" for b in bookings)
    has_hotel = any(b.booking_type == "hotel" for b in bookings)
    all_have_data = all(b.extracted_data for b in bookings)
    
    passed = has_flight and has_hotel and all_have_data and len(bookings) > 0
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Found diverse booking types with data")
    
    return passed


async def test_booking_display():
    """Test formatting bookings for display"""
    agent = GmailAgent()
    
    print("\n\n🧪 Testing Booking Display Formatting\n")
    print("=" * 80)
    
    # Get bookings
    bookings = await agent.search_for_bookings()
    
    # Format for display
    formatted = agent.format_bookings_for_display(bookings)
    
    print("\nFORMATTED OUTPUT:")
    print("-" * 80)
    print(formatted)
    print("-" * 80)
    
    # Check formatting
    has_emojis = any(emoji in formatted for emoji in ["✈️", "🏨", "📧", "📅"])
    has_numbers = "1." in formatted
    has_confidence = "confidence" in formatted.lower()
    
    passed = has_emojis and has_numbers
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Formatting includes emojis and numbering")
    
    return passed


async def test_trip_extraction():
    """Test extracting trip details from booking"""
    agent = GmailAgent()
    
    print("\n\n🧪 Testing Trip Details Extraction\n")
    print("=" * 80)
    
    # Get a booking
    bookings = await agent.search_for_bookings()
    
    if not bookings:
        print("❌ FAIL: No bookings found")
        return False
    
    # Test flight booking extraction
    flight_booking = next((b for b in bookings if b.booking_type == "flight"), None)
    
    if flight_booking:
        trip_details = agent.extract_trip_details_from_booking(flight_booking)
        
        print("\nFlight Booking Extracted:")
        print(f"Source: {trip_details.get('source')}")
        print(f"Destination Country: {trip_details.get('destination_country')}")
        print(f"Destination City: {trip_details.get('destination_city')}")
        print(f"Departure Date: {trip_details.get('departure_date')}")
        print(f"Return Date: {trip_details.get('return_date')}")
        print(f"Trip Cost: {trip_details.get('trip_cost')} {trip_details.get('currency')}")
        print(f"Confidence: {trip_details.get('confidence'):.1%}")
        
        # Verify essential fields
        has_destination = trip_details.get('destination_country') is not None
        has_dates = trip_details.get('departure_date') and trip_details.get('return_date')
        has_source = trip_details.get('source') == 'gmail_booking'
        
        passed = has_destination and has_dates and has_source
        
        print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Essential trip details extracted")
        
        return passed
    else:
        print("⚠️  SKIP: No flight booking found in mock data")
        return True


async def test_pattern_matching():
    """Test regex pattern matching for booking extraction"""
    agent = GmailAgent()
    
    print("\n\n🧪 Testing Pattern Matching\n")
    print("=" * 80)
    
    # Test email body samples
    test_cases = [
        {
            "subject": "Singapore Airlines Booking Confirmation",
            "body": """
                Your booking SQ7X9K is confirmed.
                Departure: 15/12/2025
                Return: 24/12/2025
                Total: SGD $850.00
            """,
            "expected_type": "flight",
            "should_find": ["booking_reference", "departure_date"]
        },
        {
            "subject": "Hilton Hotel Reservation Confirmed",
            "body": """
                Confirmation Number: HTK-45678
                Check-in: 2025-12-15
                Check-out: 2025-12-24
                Total: $1200.00
            """,
            "expected_type": "hotel",
            "should_find": ["booking_reference", "date"]
        }
    ]
    
    passed_count = 0
    
    for i, test in enumerate(test_cases, 1):
        result = await agent.parse_booking_email(test["body"], test["subject"])
        
        print(f"\nTest {i}: {test['subject']}")
        print(f"Expected Type: {test['expected_type']}")
        print(f"Detected Type: {result.get('type', 'unknown')}")
        print(f"Found Fields: {list(result.keys())}")
        print(f"Confidence: {result.get('confidence', 0):.1%}")
        
        # Check if expected fields were found
        found_fields = [field for field in test["should_find"] if field in result]
        
        if len(found_fields) > 0:
            print(f"✅ Found: {', '.join(found_fields)}")
            passed_count += 1
        else:
            print(f"❌ Missing expected fields")
    
    passed = passed_count == len(test_cases)
    
    print(f"\n{'✅ PASS' if passed else '⚠️  PARTIAL'}: {passed_count}/{len(test_cases)} patterns matched")
    
    return passed


async def test_empty_results():
    """Test handling of no bookings found"""
    agent = GmailAgent()
    
    print("\n\n🧪 Testing Empty Results Handling\n")
    print("=" * 80)
    
    # Format empty results
    formatted = agent.format_bookings_for_display([])
    
    print("FORMATTED OUTPUT (empty):")
    print("-" * 80)
    print(formatted)
    print("-" * 80)
    
    # Should have helpful message
    has_message = "didn't find" in formatted.lower() or "no booking" in formatted.lower()
    has_alternative = "manual" in formatted.lower() or "enter" in formatted.lower()
    
    passed = has_message
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Handles empty results gracefully")
    
    return passed


async def run_all_tests():
    """Run all Gmail agent tests"""
    print("\n" + "=" * 80)
    print(" GMAIL AGENT - TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        test1 = await test_gmail_authorization()
        test2 = await test_booking_search()
        test3 = await test_booking_display()
        test4 = await test_trip_extraction()
        test5 = await test_pattern_matching()
        test6 = await test_empty_results()
        
        # Summary
        print("\n\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Authorization: {'PASSED' if test1 else 'FAILED'}")
        print(f"✅ Booking Search: {'PASSED' if test2 else 'FAILED'}")
        print(f"✅ Display Formatting: {'PASSED' if test3 else 'FAILED'}")
        print(f"✅ Trip Extraction: {'PASSED' if test4 else 'FAILED'}")
        print(f"✅ Pattern Matching: {'PASSED' if test5 else 'FAILED'}")
        print(f"✅ Empty Results: {'PASSED' if test6 else 'FAILED'}")
        
        if test1 and test2 and test3 and test4 and test5 and test6:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())

