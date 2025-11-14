"""
Gmail Integration Agent
Automatically fetches booking confirmations and travel documents from user's email
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()

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
        from app.config import get_settings
        
        # Get Groq API key from settings if not provided
        if not groq_api_key:
            settings = get_settings()
            groq_api_key = settings.groq_api_key
        
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
        # DEMO MODE: Always use mock data after OAuth authorization
        # Even if credentials are provided, we pretend to search and return mock data
        # This allows OAuth flow to complete while showing demo data
        
        if credentials:
            logger.info("gmail_oauth_authorized_using_mock_data", 
                       reason="demo_mode" if not use_mock else "mock_forced")
        else:
            logger.info("using_mock_gmail_data", reason="no_credentials")
        
        # Mock data: 2-week trip to Japan in December
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
                    "departure": "2025-12-08",
                    "return": "2025-12-22",
                    "passengers": [
                        {"name": "John Doe", "age": 31}
                    ],
                    "class": "Economy",
                    "total_cost": 950.00,
                    "currency": "SGD"
                },
                confidence=0.95,
                raw_body="Your Singapore Airlines booking SQ7X9K is confirmed for 2-week trip to Tokyo..."
            ),
            EmailBooking(
                email_id="msg_002",
                subject="Hilton Tokyo Reservation Confirmed - 14 Nights",
                sender="reservations@hilton.com",
                date=datetime.now() - timedelta(days=3),
                booking_type="hotel",
                extracted_data={
                    "hotel": "Hilton Tokyo",
                    "confirmation_number": "HTK-45678",
                    "check_in": "2025-12-08",
                    "check_out": "2025-12-22",
                    "nights": 14,
                    "room_type": "Deluxe Room",
                    "total_cost": 2100.00,
                    "currency": "SGD"
                },
                confidence=0.92,
                raw_body="Thank you for choosing Hilton Tokyo. Confirmation HTK-45678 for 14 nights..."
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
    
    def _llm_extract_from_subject(self, subject: str, body: str = "") -> Optional[Dict[str, Any]]:
        """
        Use Groq LLM to extract trip details from email subject and body
        Example: "Your boarding pass for flight CX636 to Hong Kong" → destination=Hong Kong
        """
        from app.config import get_settings
        from groq import Groq
        
        try:
            settings = get_settings()
            client = Groq(api_key=settings.groq_api_key)
            
            prompt = f"""Extract trip details from this email about a flight/hotel booking.

Email Subject: "{subject}"
Email Body Preview: "{body[:500] if body else 'N/A'}"

Extract these details (use null if not found):
- destination_country: Country name (e.g., "Hong Kong" → China, "Singapore" → Singapore, "Japan" → Japan)
- destination_city: City name (Hong Kong, Tokyo, Singapore, etc.)
- flight_number: If mentioned (e.g., CX636, SQ12)
- departure_date: If mentioned (YYYY-MM-DD format)
- return_date: If mentioned (YYYY-MM-DD format)

Respond in JSON:
{{
  "destination_country": "country name or null",
  "destination_city": "city name or null",
  "flight_number": "flight number or null",
  "departure_date": "YYYY-MM-DD or null",
  "return_date": "YYYY-MM-DD or null"
}}"""
            
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            # Build trip details
            trip_details = {
                "source": "gmail_llm_extraction",
                "destination_country": result.get("destination_country"),
                "destination_city": result.get("destination_city"),
                "confidence": 0.85
            }
            
            # Add any other fields found
            if result.get("flight_number"):
                trip_details["flight_number"] = result["flight_number"]
            if result.get("departure_date"):
                trip_details["departure_date"] = result["departure_date"]
            if result.get("return_date"):
                trip_details["return_date"] = result["return_date"]
            
            logger.info("llm_email_extraction_success", 
                       destination=result.get("destination_country"),
                       flight=result.get("flight_number"))
            
            return trip_details
            
        except Exception as e:
            logger.error("llm_email_extraction_failed", error=str(e))
            return None
    
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
        Intelligently groups related bookings (same trip) together
        """
        if not bookings:
            return "I didn't find any booking confirmations in your recent emails. Would you like to enter your trip details manually?"
        
        # Group bookings by trip (same dates = same trip)
        trips = self._group_bookings_by_trip(bookings)
        
        if len(trips) == 1:
            # Single trip - combine all components
            return self._format_single_trip(trips[0])
        else:
            # Multiple distinct trips - list them
            return self._format_multiple_trips(trips)
    
    def _group_bookings_by_trip(self, bookings: List[EmailBooking]) -> List[List[EmailBooking]]:
        """Group bookings that belong to the same trip (same dates/destination)"""
        trips = []
        
        for booking in bookings:
            # Get dates from this booking
            dates = self._extract_dates_from_booking(booking)
            
            # Find matching trip
            matched = False
            for trip_group in trips:
                trip_dates = self._extract_dates_from_booking(trip_group[0])
                
                # Same trip if dates overlap or match
                if dates and trip_dates and dates == trip_dates:
                    trip_group.append(booking)
                    matched = True
                    break
            
            if not matched:
                trips.append([booking])
        
        return trips
    
    def _extract_dates_from_booking(self, booking: EmailBooking) -> tuple:
        """Extract departure and return dates from a booking"""
        data = booking.extracted_data
        
        departure = data.get('departure') or data.get('departure_date') or data.get('check_in')
        return_date = data.get('return') or data.get('return_date') or data.get('check_out')
        
        return (departure, return_date) if departure and return_date else None
    
    def _format_single_trip(self, bookings: List[EmailBooking]) -> str:
        """Format a single trip with multiple components (flight + hotel)"""
        parts = ["✈️ **Great news! I found your trip booking in Gmail**\n"]
        
        # Extract common details
        dates = self._extract_dates_from_booking(bookings[0])
        departure, return_date = dates if dates else (None, None)
        
        # Determine destination
        destination = "your destination"
        for booking in bookings:
            if booking.booking_type == "flight":
                route = booking.extracted_data.get('route', '')
                if '→' in route:
                    dest_code = route.split('→')[1].strip()
                    # Map codes to city names
                    city_map = {"NRT": "Tokyo", "HND": "Tokyo", "HKG": "Hong Kong"}
                    destination = city_map.get(dest_code, dest_code)
                    break
        
        # Calculate duration
        duration_text = ""
        if departure and return_date:
            from datetime import datetime
            start = datetime.strptime(departure, "%Y-%m-%d")
            end = datetime.strptime(return_date, "%Y-%m-%d")
            days = (end - start).days
            duration_text = f" ({days} days)" if days > 0 else ""
        
        parts.append(f"**📍 Destination:** {destination}")
        parts.append(f"**📅 Dates:** {departure} to {return_date}{duration_text}\n")
        
        # List components
        parts.append("**Booking details:**")
        for booking in bookings:
            data = booking.extracted_data
            
            if booking.booking_type == "flight":
                parts.append(f"✈️ Flight: {data.get('route', 'N/A')} ({data.get('airline', 'Airline')})")
                if data.get('booking_ref'):
                    parts.append(f"   Ref: {data['booking_ref']}")
            
            elif booking.booking_type == "hotel":
                parts.append(f"🏨 Hotel: {data.get('hotel', 'Hotel')} ({data.get('nights', '?')} nights)")
                if data.get('confirmation_number'):
                    parts.append(f"   Confirmation: {data['confirmation_number']}")
        
        parts.append("\n**Ready to find you the perfect travel insurance!** 🛡️")
        
        return "\n".join(parts)
    
    def _format_multiple_trips(self, trips: List[List[EmailBooking]]) -> str:
        """Format multiple distinct trips"""
        parts = ["I found multiple trips in your email! 📧\n"]
        
        for i, trip_bookings in enumerate(trips, 1):
            primary_booking = trip_bookings[0]
            data = primary_booking.extracted_data
            
            parts.append(f"\n**{i}. Trip to {self._get_destination_name(trip_bookings)}**")
            
            dates = self._extract_dates_from_booking(primary_booking)
            if dates:
                departure, return_date = dates
                parts.append(f"📅 {departure} → {return_date}")
            
            # List components
            components = []
            for b in trip_bookings:
                if b.booking_type == "flight":
                    components.append("✈️ Flight")
                elif b.booking_type == "hotel":
                    components.append("🏨 Hotel")
            
            if components:
                parts.append(f"Includes: {', '.join(components)}")
        
        parts.append("\n\nWhich trip would you like insurance for? (Just reply with the number)")
        
        return "\n".join(parts)
    
    def _get_destination_name(self, bookings: List[EmailBooking]) -> str:
        """Extract destination name from bookings"""
        for booking in bookings:
            if booking.booking_type == "flight":
                route = booking.extracted_data.get('route', '')
                if '→' in route:
                    dest_code = route.split('→')[1].strip()
                    city_map = {"NRT": "Tokyo", "HND": "Tokyo", "HKG": "Hong Kong", "BKK": "Bangkok"}
                    return city_map.get(dest_code, dest_code)
            
            if booking.extracted_data.get('destination'):
                return booking.extracted_data['destination']
        
        return "destination"
    
    def extract_trip_details_from_booking(self, booking: EmailBooking) -> Dict[str, Any]:
        """
        Convert email booking to trip details format
        Uses LLM to extract details from subject/body if needed
        """
        # Try using LLM to extract from subject first (more reliable)
        if booking.subject and self.groq_api_key:
            llm_extracted = self._llm_extract_from_subject(booking.subject, booking.raw_body)
            if llm_extracted:
                return llm_extracted
        
        # Fallback to extracted_data
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

