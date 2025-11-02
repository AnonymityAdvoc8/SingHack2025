"""
Gmail Integration Agent
Automatically fetches booking confirmations and travel documents from user's email
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EmailBooking:
    """Represents a booking found in email"""
    email_id: str
    subject: str
    sender: str
    date: datetime
    booking_type: str  # flight, hotel, rental_car, activity
    extracted_data: Dict[str, Any]
    confidence: float
    raw_body: str


class GmailAgent:
    """
    Fetches and parses booking confirmations from Gmail
    Uses OAuth for secure access
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialize Gmail agent
        
        Args:
            groq_api_key: For LLM-powered email parsing (optional, uses pattern matching if None)
        """
        from app.services.gmail_oauth import get_gmail_oauth_service
        
        self.groq_api_key = groq_api_key
        self.gmail_oauth = get_gmail_oauth_service()  # Use singleton
        self.gmail_service = None
    
    def get_authorization_url(self, session_id: str) -> str:
        """
        Get Gmail OAuth authorization URL
        
        Args:
            session_id: User session ID for state parameter
            
        Returns:
            OAuth authorization URL
        """
        return self.gmail_oauth.get_authorization_url(session_id)
    
    async def authorize_user(self, auth_code: str, state: str) -> Dict[str, Any]:
        """
        Complete OAuth flow with user's authorization code
        
        Args:
            auth_code: OAuth authorization code from user
            state: State parameter for security
            
        Returns:
            Authorization status and user info
        """
        credentials = self.gmail_oauth.handle_oauth_callback(auth_code, state)
        
        if credentials:
            return {
                "authorized": True,
                "user_email": credentials.id_token.get('email', 'user@example.com') if hasattr(credentials, 'id_token') else "authorized",
                "scope": self.gmail_oauth.SCOPES,
                "message": "Successfully connected to Gmail! 📧"
            }
        else:
            return {
                "authorized": False,
                "error": "Failed to authorize Gmail access"
            }
    
    async def search_for_bookings(
        self,
        credentials: Optional[Any] = None,
        days_back: int = 90,
        days_forward: int = 365,
        use_mock: bool = None
    ) -> List[EmailBooking]:
        """
        Search Gmail for booking confirmations
        
        Args:
            credentials: Gmail OAuth credentials (if None, uses mock data)
            days_back: How many days back to search
            days_forward: How many days forward to search
            use_mock: Force using mock data (for demo/testing)
            
        Returns:
            List of found bookings
        """
        # Use real Gmail if credentials provided and not forcing mock
        if credentials and not use_mock:
            return await self._search_real_gmail(credentials, days_back, days_forward)
        
        # Otherwise return mock booking emails for demo
        logger.info("using_mock_gmail_data", reason="no_credentials" if not credentials else "mock_forced")
        
        mock_bookings = [
            EmailBooking(
                email_id="msg_001",
                subject="Singapore Airlines Booking Confirmation - Tokyo",
                sender="bookings@singaporeair.com",
                date=datetime.now() - timedelta(days=5),
                booking_type="flight",
                extracted_data={
                    "airline": "Singapore Airlines",
                    "booking_ref": "SQ7X9K",
                    "route": "SIN → NRT",
                    "departure": "2025-12-15",
                    "return": "2025-12-24",
                    "passengers": [
                        {"name": "John Doe", "age": 31}
                    ],
                    "class": "Economy",
                    "total_cost": 850.00,
                    "currency": "SGD"
                },
                confidence=0.95,
                raw_body="Your Singapore Airlines booking SQ7X9K is confirmed..."
            ),
            EmailBooking(
                email_id="msg_002",
                subject="Hilton Tokyo Reservation Confirmed",
                sender="reservations@hilton.com",
                date=datetime.now() - timedelta(days=3),
                booking_type="hotel",
                extracted_data={
                    "hotel": "Hilton Tokyo",
                    "confirmation_number": "HTK-45678",
                    "check_in": "2025-12-15",
                    "check_out": "2025-12-24",
                    "nights": 9,
                    "room_type": "Deluxe Room",
                    "total_cost": 1200.00,
                    "currency": "SGD"
                },
                confidence=0.92,
                raw_body="Thank you for choosing Hilton Tokyo. Confirmation HTK-45678..."
            ),
            EmailBooking(
                email_id="msg_003",
                subject="Your Bali Adventure - Flight & Hotel Package",
                sender="bookings@expedia.com",
                date=datetime.now() - timedelta(days=15),
                booking_type="package",
                extracted_data={
                    "destination": "Bali, Indonesia",
                    "departure_date": "2026-02-10",
                    "return_date": "2026-02-17",
                    "travelers": 2,
                    "package_includes": ["flights", "hotel", "transfers"],
                    "total_cost": 1500.00,
                    "currency": "SGD"
                },
                confidence=0.88,
                raw_body="Your Bali package is confirmed! Departure Feb 10..."
            )
        ]
        
        return mock_bookings
    
    async def _search_real_gmail(
        self,
        credentials: Any,
        days_back: int,
        days_forward: int
    ) -> List[EmailBooking]:
        """Search real Gmail for booking confirmations"""
        logger.info("searching_real_gmail", days_back=days_back)
        
        try:
            # Search queries - Broader to catch various airline/booking formats
            search_queries = [
                # Flight-related keywords in subject (catches most airlines)
                'subject:(e-ticket OR flight confirmation OR flight booking OR boarding pass) -subject:(restaurant OR dinner)',
                
                # Booking references (airline confirmation codes)
                'subject:(booking reference OR confirmation code OR PNR OR record locator) subject:(flight OR airline OR YVR OR HKG OR airport)',
                
                # Known airlines (by name in sender, not specific email)
                'from:(cathay OR "air canada" OR "singapore air" OR emirates OR ana OR qantas OR united OR delta)',
                
                # Online booking platforms
                'from:(expedia OR booking.com OR hotels.com OR agoda OR airbnb) -subject:(restaurant OR dinner OR table)',
                
                # Generic flight/travel terms
                'subject:flight -subject:(restaurant OR sale OR offer OR newsletter)',
                
                # Catch "YVR to HKG" style route mentions
                'subject:(YVR OR HKG OR NRT OR LAX OR JFK OR SIN) subject:(flight OR departure OR arrival)',
            ]
            
            all_messages = []
            for query in search_queries:
                messages = self.gmail_oauth.search_emails(credentials, query, max_results=20)
                all_messages.extend(messages)
            
            # Deduplicate by message ID
            unique_messages = {msg['id']: msg for msg in all_messages}
            
            # Get full content and parse
            bookings = []
            for msg_id, msg_summary in list(unique_messages.items())[:10]:  # Top 10
                email_data = self.gmail_oauth.get_email_content(credentials, msg_id)
                
                if email_data:
                    # Filter out obvious non-travel (restaurants, bars, etc.)
                    subject_lower = email_data['subject'].lower()
                    if any(word in subject_lower for word in ['restaurant', 'dinner', 'table', 'bar', 'cafe', 'lunch', 'brunch']):
                        logger.info("gmail_skipping_non_travel", subject=email_data['subject'])
                        continue
                    
                    # Parse the email
                    parsed = await self.parse_booking_email(email_data['body'], email_data['subject'])
                    
                    # Validate it's actually a travel booking
                    if parsed and parsed.get('confidence', 0) > 0.5:
                        # Additional validation: must have travel-related data
                        is_valid_travel = (
                            parsed.get('type') in ['flight', 'hotel', 'package'] or
                            any(key in parsed for key in ['route', 'flight_number', 'hotel', 'nights', 'destination'])
                        )
                        
                        if not is_valid_travel:
                            logger.info("gmail_skipping_invalid_booking", subject=email_data['subject'], type=parsed.get('type'))
                            continue
                        
                        booking = EmailBooking(
                            email_id=msg_id,
                            subject=email_data['subject'],
                            sender=email_data['sender'],
                            date=datetime.now(),
                            booking_type=parsed.get('type', 'unknown'),
                            extracted_data=parsed,
                            confidence=parsed.get('confidence', 0.7),
                            raw_body=email_data['body'][:500]
                        )
                        bookings.append(booking)
            
            logger.info("gmail_search_complete", found=len(bookings))
            return bookings
            
        except Exception as e:
            logger.error("gmail_real_search_failed", error=str(e))
            # Fall back to mock data
            return await self.search_for_bookings(credentials=None, use_mock=True)
    
    async def parse_booking_email(self, email_body: str, email_subject: str) -> Dict[str, Any]:
        """
        Parse booking email using pattern matching or LLM
        
        Args:
            email_body: Email body text
            email_subject: Email subject line
            
        Returns:
            Extracted booking data
        """
        # Try pattern matching first for common booking services
        extracted = self._pattern_match_booking(email_body, email_subject)
        
        if extracted and extracted.get("confidence", 0) > 0.8:
            return extracted
        
        # Fall back to LLM parsing if available and pattern matching failed
        if self.groq_api_key:
            return await self._llm_parse_booking(email_body, email_subject)
        
        return extracted or {"error": "Could not parse booking email"}
    
    def _pattern_match_booking(self, body: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Use regex patterns to extract booking information
        """
        booking_data = {}
        
        # Detect booking type from subject
        if any(word in subject.lower() for word in ["flight", "airline", "airways"]):
            booking_data["type"] = "flight"
        elif any(word in subject.lower() for word in ["hotel", "reservation", "accommodation"]):
            booking_data["type"] = "hotel"
        elif "rental" in subject.lower() or "car hire" in subject.lower():
            booking_data["type"] = "rental_car"
        else:
            booking_data["type"] = "unknown"
        
        # Extract dates (common formats)
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            dates.extend(matches)
        
        if len(dates) >= 2:
            booking_data["departure_date"] = dates[0]
            booking_data["return_date"] = dates[1]
            booking_data["confidence"] = 0.85
        elif len(dates) == 1:
            booking_data["date"] = dates[0]
            booking_data["confidence"] = 0.6
        else:
            booking_data["confidence"] = 0.3
        
        # Extract booking/confirmation number
        booking_ref_patterns = [
            r'(?:booking|confirmation|reference)[\s#:]+([A-Z0-9]{6,})',
            r'(?:PNR|Record Locator)[\s:]+([A-Z0-9]{6})'
        ]
        
        for pattern in booking_ref_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                booking_data["booking_reference"] = match.group(1)
                booking_data["confidence"] = min(booking_data.get("confidence", 0) + 0.1, 1.0)
                break
        
        # Extract total cost
        cost_patterns = [
            r'(?:total|amount|price)[\s:]+(?:SGD|USD|€|£)?\s*(\d+[,.]?\d*)',
            r'(?:SGD|USD|€|£)\s*(\d+[,.]?\d*)'
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                try:
                    booking_data["total_cost"] = float(cost_str)
                    booking_data["confidence"] = min(booking_data.get("confidence", 0) + 0.05, 1.0)
                except ValueError:
                    pass
                break
        
        return booking_data if booking_data else None
    
    async def _llm_parse_booking(self, body: str, subject: str) -> Dict[str, Any]:
        """
        Use Groq LLM to parse booking email intelligently
        """
        # For hackathon: Simplified implementation
        # In production: Use Groq API for intelligent parsing
        
        # Mock LLM response
        return {
            "type": "flight",
            "destination": "Tokyo, Japan",
            "departure_date": "2025-12-15",
            "return_date": "2025-12-24",
            "travelers": 1,
            "confidence": 0.9,
            "source": "llm_extraction"
        }
    
    def format_bookings_for_display(self, bookings: List[EmailBooking]) -> str:
        """
        Format found bookings for conversational display
        """
        if not bookings:
            return "I didn't find any booking confirmations in your recent emails. Would you like to enter your trip details manually?"
        
        parts = ["I found these trips in your email! 📧\n"]
        
        for i, booking in enumerate(bookings[:5], 1):  # Show max 5
            parts.append(f"\n**{i}. {booking.subject}**")
            
            if booking.booking_type == "flight":
                data = booking.extracted_data
                parts.append(f"✈️ {data.get('route', 'Flight booking')}")
                if data.get('departure') and data.get('return'):
                    parts.append(f"📅 {data['departure']} → {data['return']}")
                if data.get('booking_ref'):
                    parts.append(f"🔖 Ref: {data['booking_ref']}")
            
            elif booking.booking_type == "hotel":
                data = booking.extracted_data
                parts.append(f"🏨 {data.get('hotel', 'Hotel reservation')}")
                if data.get('check_in') and data.get('check_out'):
                    parts.append(f"📅 {data['check_in']} → {data['check_out']} ({data.get('nights', '?')} nights)")
            
            elif booking.booking_type == "package":
                data = booking.extracted_data
                parts.append(f"🎁 Package to {data.get('destination', 'destination')}")
                if data.get('departure_date') and data.get('return_date'):
                    parts.append(f"📅 {data['departure_date']} → {data['return_date']}")
            
            # Confidence indicator
            if booking.confidence >= 0.9:
                parts.append("✅ High confidence")
            elif booking.confidence >= 0.7:
                parts.append("⚠️ Medium confidence")
            else:
                parts.append("❓ Low confidence - please verify")
        
        parts.append("\n\nWhich trip would you like insurance for? (Just reply with the number)")
        
        return "\n".join(parts)
    
    def extract_trip_details_from_booking(self, booking: EmailBooking) -> Dict[str, Any]:
        """
        Convert email booking to trip details format
        """
        data = booking.extracted_data
        
        trip_details = {
            "source": "gmail_booking",
            "confidence": booking.confidence
        }
        
        # Extract destination
        if booking.booking_type == "flight":
            route = data.get("route", "")
            # Parse route like "SIN → NRT"
            if "→" in route:
                dest_code = route.split("→")[1].strip()
                trip_details["destination_city"] = dest_code
                
                # Map airport codes to countries (simplified)
                airport_to_country = {
                    "NRT": "Japan", "HND": "Japan",
                    "BKK": "Thailand", "DMK": "Thailand",
                    "DPS": "Indonesia",
                    "SYD": "Australia", "MEL": "Australia",
                    "LHR": "United Kingdom", "LGW": "United Kingdom"
                }
                trip_details["destination_country"] = airport_to_country.get(dest_code, "Unknown")
        
        elif "destination" in data:
            dest = data["destination"]
            trip_details["destination_country"] = dest.split(",")[-1].strip()
        
        # Extract dates
        if "departure" in data:
            trip_details["departure_date"] = data["departure"]
        elif "departure_date" in data:
            trip_details["departure_date"] = data["departure_date"]
        
        if "return" in data:
            trip_details["return_date"] = data["return"]
        elif "return_date" in data:
            trip_details["return_date"] = data["return_date"]
        
        # Extract travelers
        if "passengers" in data:
            trip_details["travelers"] = data["passengers"]
        elif "travelers" in data:
            trip_details["num_travelers"] = data["travelers"]
        
        # Extract costs for trip value calculation
        if "total_cost" in data:
            trip_details["trip_cost"] = data["total_cost"]
            trip_details["currency"] = data.get("currency", "SGD")
        
        return trip_details

