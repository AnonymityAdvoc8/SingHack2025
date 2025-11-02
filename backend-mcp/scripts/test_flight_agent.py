"""
Test Flight API Agent
Tests flight booking lookup and extraction
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.flight_api_agent import FlightAPIAgent

async def test_booking_lookup():
    """Test looking up flights by booking reference"""
    agent = FlightAPIAgent()
    
    print("🧪 Testing Flight Booking Lookup\n")
    print("=" * 80)
    
    # Test valid booking references
    test_refs = ["ABC123", "XYZ789", "LMN456"]
    
    passed = 0
    
    for ref in test_refs:
        booking = await agent.lookup_booking(ref)
        
        if booking:
            print(f"\n✅ Found Booking: {ref}")
            print(f"   Airline: {booking.get('airline')}")
            print(f"   Passengers: {len(booking.get('passengers', []))}")
            print(f"   Flights: {len(booking.get('flights', []))}")
            print(f"   Total Cost: {booking.get('currency')} ${booking.get('total_cost')}")
            print(f"   Status: {booking.get('status')}")
            passed += 1
        else:
            print(f"\n❌ Booking not found: {ref}")
    
    # Test invalid reference
    invalid = await agent.lookup_booking("INVALID999")
    
    if invalid is None:
        print(f"\n✅ Correctly returned None for invalid reference")
        invalid_handled = True
    else:
        print(f"\n❌ Should have returned None for invalid reference")
        invalid_handled = False
    
    print(f"\n📊 Results: {passed}/{len(test_refs)} bookings found")
    
    return passed == len(test_refs) and invalid_handled


async def test_trip_extraction():
    """Test extracting trip details from booking"""
    agent = FlightAPIAgent()
    
    print("\n\n🧪 Testing Trip Details Extraction\n")
    print("=" * 80)
    
    # Look up a booking
    booking = await agent.lookup_booking("ABC123")
    
    if not booking:
        print("❌ FAIL: Booking ABC123 not found")
        return False
    
    # Extract trip details
    trip_details = agent.extract_trip_details(booking)
    
    print("\nExtracted Trip Details:")
    print("-" * 80)
    print(f"Source: {trip_details.get('source')}")
    print(f"Booking Reference: {trip_details.get('booking_reference')}")
    print(f"Airline: {trip_details.get('airline')} ({trip_details.get('airline_code')})")
    print(f"\nDestination:")
    print(f"  City: {trip_details.get('destination_city')}")
    print(f"  Country: {trip_details.get('destination_country')}")
    print(f"  Region: {trip_details.get('destination_region')}")
    print(f"\nDates:")
    print(f"  Departure: {trip_details.get('departure_date')}")
    print(f"  Return: {trip_details.get('return_date')}")
    print(f"  Duration: {trip_details.get('trip_duration_days')} days")
    print(f"\nTravelers:")
    print(f"  Count: {trip_details.get('num_travelers')}")
    for i, traveler in enumerate(trip_details.get('travelers', []), 1):
        print(f"  {i}. {traveler.get('name')} (Age: {traveler.get('age')})")
    print(f"\nFlight Details:")
    print(f"  Class: {trip_details.get('flight_class')}")
    print(f"  Outbound: {trip_details.get('outbound_flight')}")
    print(f"  Return: {trip_details.get('return_flight')}")
    print(f"\nTrip Value:")
    print(f"  Cost: {trip_details.get('currency')} ${trip_details.get('flight_cost')}")
    print(f"  Purpose: {trip_details.get('trip_purpose')}")
    
    # Verify essential fields
    essential_fields = [
        'destination_country', 'departure_date', 'return_date',
        'num_travelers', 'trip_duration_days', 'source'
    ]
    
    missing_fields = [f for f in essential_fields if not trip_details.get(f)]
    
    if missing_fields:
        print(f"\n❌ FAIL: Missing fields: {', '.join(missing_fields)}")
        return False
    else:
        print(f"\n✅ PASS: All essential fields present")
        return True


async def test_display_formatting():
    """Test formatting booking for display"""
    agent = FlightAPIAgent()
    
    print("\n\n🧪 Testing Display Formatting\n")
    print("=" * 80)
    
    # Look up bookings with different characteristics
    test_refs = ["ABC123", "XYZ789"]  # Economy and Business class
    
    for ref in test_refs:
        booking = await agent.lookup_booking(ref)
        
        if booking:
            formatted = agent.format_booking_for_display(booking)
            
            print(f"\nBooking Reference: {ref}")
            print("-" * 80)
            print(formatted)
            print("-" * 80)
            
            # Check formatting quality
            has_emojis = any(emoji in formatted for emoji in ["✈️", "🛫", "🛬", "📋", "💰"])
            has_structure = "Outbound:" in formatted and "Return:" in formatted
            has_dates = booking['flights'][0]['departure'].split('T')[0] in formatted
            
            if has_emojis and has_structure:
                print("✅ Good formatting (emojis + structure)")
            else:
                print("❌ Poor formatting")
    
    return True


async def test_booking_verification():
    """Test booking status verification"""
    agent = FlightAPIAgent()
    
    print("\n\n🧪 Testing Booking Verification\n")
    print("=" * 80)
    
    # Test valid booking
    valid_result = await agent.verify_booking_status("ABC123")
    
    print(f"Valid Booking (ABC123):")
    print(f"  Found: {valid_result.get('found')}")
    print(f"  Status: {valid_result.get('status')}")
    print(f"  Airline: {valid_result.get('airline')}")
    
    # Test invalid booking
    invalid_result = await agent.verify_booking_status("NOTFOUND")
    
    print(f"\nInvalid Booking (NOTFOUND):")
    print(f"  Found: {invalid_result.get('found')}")
    print(f"  Error: {invalid_result.get('error')}")
    
    # Verify results
    valid_check = valid_result.get('found') == True and valid_result.get('status') == 'Confirmed'
    invalid_check = invalid_result.get('found') == False and invalid_result.get('error') is not None
    
    passed = valid_check and invalid_check
    
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}: Verification works correctly")
    
    return passed


async def test_airport_mapping():
    """Test airport code to country mapping"""
    agent = FlightAPIAgent()
    
    print("\n\n🧪 Testing Airport Code Mapping\n")
    print("=" * 80)
    
    # Test various bookings to see airport mapping
    test_cases = [
        ("ABC123", "NRT", "Japan", "Tokyo"),
        ("LMN456", "DPS", "Indonesia", "Bali")
    ]
    
    passed = 0
    
    for ref, expected_code, expected_country, expected_city in test_cases:
        booking = await agent.lookup_booking(ref)
        
        if booking:
            trip = agent.extract_trip_details(booking)
            
            destination_country = trip.get('destination_country')
            destination_city = trip.get('destination_city')
            
            country_match = destination_country == expected_country
            city_match = destination_city == expected_city or expected_code in destination_city
            
            print(f"\n{ref}:")
            print(f"  Expected: {expected_city}, {expected_country}")
            print(f"  Got: {destination_city}, {destination_country}")
            print(f"  {'✅ MATCH' if country_match else '❌ MISMATCH'}")
            
            if country_match:
                passed += 1
    
    print(f"\n📊 Results: {passed}/{len(test_cases)} mappings correct")
    
    return passed == len(test_cases)


async def test_frequent_flyer():
    """Test frequent flyer history check"""
    agent = FlightAPIAgent()
    
    print("\n\n🧪 Testing Frequent Flyer History\n")
    print("=" * 80)
    
    # Test Singapore Airlines frequent flyer
    ff_data = await agent.check_frequent_flyer_history("SQ", "KF123456789")
    
    print("Singapore Airlines Frequent Flyer:")
    print(f"  Member Since: {ff_data.get('member_since', 'N/A')}")
    print(f"  Tier: {ff_data.get('tier', 'N/A')}")
    print(f"  Lifetime Flights: {ff_data.get('lifetime_flights', 0)}")
    print(f"  Favorite Destinations: {ff_data.get('favorite_destinations', [])}")
    print(f"  Suggestion: {ff_data.get('suggestion', 'None')}")
    
    # Test unknown airline
    unknown = await agent.check_frequent_flyer_history("XX", "UNKNOWN")
    
    print(f"\nUnknown Airline:")
    print(f"  Member Found: {unknown.get('member_found', False)}")
    
    # Verify SQ data exists
    has_data = ff_data.get('tier') is not None
    
    print(f"\n{'✅ PASS' if has_data else '❌ FAIL'}: Frequent flyer data retrieved")
    
    return has_data


async def run_all_tests():
    """Run all flight agent tests"""
    print("\n" + "=" * 80)
    print(" FLIGHT API AGENT - TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        test1 = await test_booking_lookup()
        test2 = await test_trip_extraction()
        test3 = await test_display_formatting()
        test4 = await test_booking_verification()
        test5 = await test_airport_mapping()
        test6 = await test_frequent_flyer()
        
        # Summary
        print("\n\n" + "=" * 80)
        print(" TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Booking Lookup: {'PASSED' if test1 else 'FAILED'}")
        print(f"✅ Trip Extraction: {'PASSED' if test2 else 'FAILED'}")
        print(f"✅ Display Formatting: {'PASSED' if test3 else 'FAILED'}")
        print(f"✅ Booking Verification: {'PASSED' if test4 else 'FAILED'}")
        print(f"✅ Airport Mapping: {'PASSED' if test5 else 'FAILED'}")
        print(f"✅ Frequent Flyer: {'PASSED' if test6 else 'FAILED'}")
        
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

