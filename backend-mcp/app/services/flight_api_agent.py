"""
Flight API Mock Agent
Looks up flight bookings by booking reference number
Mocks integration with airline APIs
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import random


@dataclass
class FlightBooking:
    """Represents a flight booking"""
    booking_ref: str
    airline: str
    airline_code: str
    passengers: list
    flights: list
    total_cost: float
    currency: str
    booking_class: str
    status: str
    created_date: datetime


class FlightAPIAgent:
    """
    Mock flight API integration
    In production: Would connect to real airline APIs (Amadeus, Sabre, etc.)
    """
    
    # Mock database of flight bookings
    MOCK_BOOKINGS = {
        "ABC123": {
            "airline": "Singapore Airlines",
            "airline_code": "SQ",
            "booking_ref": "ABC123",
            "passengers": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "age": 31,
                    "seat": "12A",
                    "frequent_flyer": "KF123456789"
                }
            ],
            "flights": [
                {
                    "flight_number": "SQ12",
                    "from": "SIN",
                    "from_name": "Singapore Changi Airport",
                    "to": "NRT",
                    "to_name": "Tokyo Narita International Airport",
                    "departure": "2025-12-15T10:30:00",
                    "arrival": "2025-12-15T18:45:00",
                    "class": "Economy",
                    "aircraft": "Boeing 777-300ER"
                },
                {
                    "flight_number": "SQ11",
                    "from": "NRT",
                    "from_name": "Tokyo Narita International Airport",
                    "to": "SIN",
                    "to_name": "Singapore Changi Airport",
                    "departure": "2025-12-24T20:15:00",
                    "arrival": "2025-12-25T02:30:00",
                    "class": "Economy",
                    "aircraft": "Boeing 777-300ER"
                }
            ],
            "total_cost": 850.00,
            "currency": "SGD",
            "booking_class": "Economy",
            "status": "Confirmed",
            "created_date": datetime.now() - timedelta(days=5)
        },
        "XYZ789": {
            "airline": "ANA (All Nippon Airways)",
            "airline_code": "NH",
            "booking_ref": "XYZ789",
            "passengers": [
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "age": 28,
                    "seat": "14K",
                    "frequent_flyer": None
                },
                {
                    "first_name": "Bob",
                    "last_name": "Smith",
                    "age": 30,
                    "seat": "14J",
                    "frequent_flyer": "NH987654321"
                }
            ],
            "flights": [
                {
                    "flight_number": "NH843",
                    "from": "SIN",
                    "from_name": "Singapore Changi Airport",
                    "to": "HND",
                    "to_name": "Tokyo Haneda Airport",
                    "departure": "2026-01-10T08:00:00",
                    "arrival": "2026-01-10T16:15:00",
                    "class": "Business",
                    "aircraft": "Boeing 787-9"
                },
                {
                    "flight_number": "NH844",
                    "from": "HND",
                    "from_name": "Tokyo Haneda Airport",
                    "to": "SIN",
                    "to_name": "Singapore Changi Airport",
                    "departure": "2026-01-17T18:30:00",
                    "arrival": "2026-01-18T00:45:00",
                    "class": "Business",
                    "aircraft": "Boeing 787-9"
                }
            ],
            "total_cost": 2400.00,
            "currency": "SGD",
            "booking_class": "Business",
            "status": "Confirmed",
            "created_date": datetime.now() - timedelta(days=12)
        },
        "LMN456": {
            "airline": "Scoot Airlines",
            "airline_code": "TR",
            "booking_ref": "LMN456",
            "passengers": [
                {
                    "first_name": "Alice",
                    "last_name": "Wong",
                    "age": 25,
                    "seat": "8B",
                    "frequent_flyer": None
                }
            ],
            "flights": [
                {
                    "flight_number": "TR509",
                    "from": "SIN",
                    "from_name": "Singapore Changi Airport",
                    "to": "DPS",
                    "to_name": "Ngurah Rai International Airport (Bali)",
                    "departure": "2026-02-10T07:15:00",
                    "arrival": "2026-02-10T10:00:00",
                    "class": "Economy",
                    "aircraft": "Boeing 787-8"
                },
                {
                    "flight_number": "TR510",
                    "from": "DPS",
                    "from_name": "Ngurah Rai International Airport (Bali)",
                    "to": "SIN",
                    "to_name": "Singapore Changi Airport",
                    "departure": "2026-02-17T11:00:00",
                    "arrival": "2026-02-17T13:45:00",
                    "class": "Economy",
                    "aircraft": "Boeing 787-8"
                }
            ],
            "total_cost": 420.00,
            "currency": "SGD",
            "booking_class": "Economy",
            "status": "Confirmed",
            "created_date": datetime.now() - timedelta(days=20)
        }
    }
    
    # Airport code to country/city mapping
    AIRPORT_MAPPING = {
        "SIN": {"city": "Singapore", "country": "Singapore"},
        "NRT": {"city": "Tokyo", "country": "Japan"},
        "HND": {"city": "Tokyo", "country": "Japan"},
        "DPS": {"city": "Bali", "country": "Indonesia"},
        "BKK": {"city": "Bangkok", "country": "Thailand"},
        "SYD": {"city": "Sydney", "country": "Australia"},
        "LHR": {"city": "London", "country": "United Kingdom"},
        "JFK": {"city": "New York", "country": "USA"},
        "LAX": {"city": "Los Angeles", "country": "USA"}
    }
    
    async def lookup_booking(self, booking_ref: str) -> Optional[Dict[str, Any]]:
        """
        Look up flight booking by reference number
        
        Args:
            booking_ref: Booking reference/PNR
            
        Returns:
            Flight booking details or None if not found
        """
        # Normalize booking reference
        booking_ref = booking_ref.upper().strip()
        
        # Look up in mock database
        booking = self.MOCK_BOOKINGS.get(booking_ref)
        
        if booking:
            return booking
        
        # If not found, return None
        return None
    
    async def verify_booking_status(self, booking_ref: str) -> Dict[str, Any]:
        """
        Verify booking status (confirmed, cancelled, etc.)
        """
        booking = await self.lookup_booking(booking_ref)
        
        if not booking:
            return {
                "found": False,
                "error": "Booking not found. Please check your reference number."
            }
        
        return {
            "found": True,
            "status": booking["status"],
            "airline": booking["airline"],
            "booking_ref": booking["booking_ref"]
        }
    
    def extract_trip_details(self, booking: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract trip details from flight booking for insurance quotation
        """
        if not booking or not booking.get("flights"):
            return {}
        
        flights = booking["flights"]
        outbound = flights[0]  # First flight
        inbound = flights[-1]  # Last flight (return)
        
        # Parse dates
        departure_date = datetime.fromisoformat(outbound["departure"])
        return_date = datetime.fromisoformat(inbound["arrival"])
        
        # Calculate trip duration
        duration = (return_date - departure_date).days
        
        # Get destination
        destination_code = outbound["to"]
        destination_info = self.AIRPORT_MAPPING.get(destination_code, {})
        
        # Extract passengers
        passengers = booking.get("passengers", [])
        travelers = []
        for pax in passengers:
            travelers.append({
                "name": f"{pax.get('first_name', '')} {pax.get('last_name', '')}".strip(),
                "age": pax.get("age", 35),
                "has_pre_existing_conditions": False  # User would need to confirm
            })
        
        # Extract costs for trip value
        total_cost = booking.get("total_cost", 0)
        
        return {
            "source": "flight_booking_api",
            "booking_reference": booking.get("booking_ref"),
            "airline": booking.get("airline"),
            
            # Destination
            "destination_city": destination_info.get("city", destination_code),
            "destination_country": destination_info.get("country", "Unknown"),
            "destination_region": self._get_region(destination_info.get("country", "")),
            
            # Dates
            "departure_date": departure_date.strftime("%Y-%m-%d"),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "trip_duration_days": duration,
            
            # Travelers
            "travelers": travelers,
            "num_travelers": len(travelers),
            
            # Flight details
            "flight_class": booking.get("booking_class", "Economy"),
            "airline_code": booking.get("airline_code"),
            "outbound_flight": outbound.get("flight_number"),
            "return_flight": inbound.get("flight_number"),
            
            # Trip value (for coverage calculation)
            "flight_cost": total_cost,
            "currency": booking.get("currency", "SGD"),
            
            # Additional context
            "trip_purpose": "Leisure",  # Default, user can override
            "planned_activities": ["general"]  # Will be asked
        }
    
    def _get_region(self, country: str) -> str:
        """Map country to region for insurance purposes"""
        region_mapping = {
            "Japan": "Asia",
            "Thailand": "Asia",
            "Indonesia": "Asia",
            "Singapore": "Asia",
            "Australia": "Oceania",
            "United Kingdom": "Europe",
            "USA": "North America"
        }
        return region_mapping.get(country, "Worldwide")
    
    def format_booking_for_display(self, booking: Dict[str, Any]) -> str:
        """
        Format flight booking for conversational display
        """
        if not booking:
            return "❌ Booking not found. Please check your reference number and try again."
        
        parts = []
        
        # Header
        parts.append(f"✈️ **{booking['airline']} Booking Found!**\n")
        parts.append(f"📋 Reference: {booking['booking_ref']}\n")
        
        # Passengers
        passengers = booking.get("passengers", [])
        if passengers:
            if len(passengers) == 1:
                pax = passengers[0]
                parts.append(f"👤 Passenger: {pax['first_name']} {pax['last_name']}")
            else:
                parts.append(f"👥 Passengers: {len(passengers)} travelers")
                for pax in passengers:
                    parts.append(f"  • {pax['first_name']} {pax['last_name']}")
        
        parts.append("")
        
        # Flights
        flights = booking.get("flights", [])
        if flights:
            outbound = flights[0]
            parts.append("**Outbound:**")
            parts.append(f"🛫 {outbound['flight_number']}: {outbound['from_name']} → {outbound['to_name']}")
            
            dep_time = datetime.fromisoformat(outbound['departure']).strftime("%b %d, %Y at %I:%M %p")
            parts.append(f"📅 {dep_time}")
            parts.append(f"💺 Class: {booking['booking_class']}\n")
            
            if len(flights) > 1:
                inbound = flights[-1]
                parts.append("**Return:**")
                parts.append(f"🛬 {inbound['flight_number']}: {inbound['from_name']} → {inbound['to_name']}")
                
                ret_time = datetime.fromisoformat(inbound['departure']).strftime("%b %d, %Y at %I:%M %p")
                parts.append(f"📅 {ret_time}\n")
        
        # Total cost
        parts.append(f"💰 Total: {booking['currency']} ${booking['total_cost']:,.2f}")
        parts.append(f"✅ Status: {booking['status']}\n")
        
        # Call to action
        parts.append("Perfect! Let me find the best insurance coverage for this trip. ✨")
        
        return "\n".join(parts)
    
    async def check_frequent_flyer_history(
        self,
        airline_code: str,
        ff_number: str
    ) -> Dict[str, Any]:
        """
        Mock: Check frequent flyer history for travel patterns
        In production: Would call airline loyalty API
        """
        # Mock response based on airline
        if airline_code == "SQ":  # Singapore Airlines
            return {
                "member_since": "2018-03-15",
                "tier": "Gold",
                "lifetime_flights": 45,
                "favorite_destinations": ["Tokyo", "London", "Sydney"],
                "average_trips_per_year": 6,
                "typical_booking_class": "Economy",
                "suggestion": "Based on your travel history, an annual policy might save you money!"
            }
        
        return {
            "member_found": False,
            "suggestion": None
        }

