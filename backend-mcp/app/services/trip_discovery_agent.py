"""
Trip Discovery Agent
Autonomously discovers trip details from multiple sources
Coordinates Gmail, Flight API, Calendar, and Payment integrations
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DiscoveredTrip:
    """A trip discovered from any source"""
    trip_id: str
    source: str  # gmail, flight_api, calendar, payment
    destination: Optional[str] = None
    dates: Optional[Dict[str, str]] = None
    travelers: Optional[List[Dict]] = None
    cost: Optional[float] = None
    confidence: float = 0.0
    raw_data: Dict[str, Any] = None
    display_summary: str = ""


class TripDiscoveryAgent:
    """
    Autonomous agent that discovers trips from all available sources
    Runs parallel searches and consolidates results
    """
    
    def __init__(self, gmail_agent=None, flight_agent=None, calendar_agent=None):
        """
        Initialize with optional agents
        Agents are injected for flexibility
        """
        self.gmail_agent = gmail_agent
        self.flight_agent = flight_agent
        self.calendar_agent = calendar_agent
    
    async def discover_all_trips(
        self,
        user_id: Optional[str] = None,
        gmail_authorized: bool = False,
        calendar_authorized: bool = False
    ) -> List[DiscoveredTrip]:
        """
        Autonomously discover trips from all available sources
        Runs searches in parallel for speed
        
        Args:
            user_id: User identifier
            gmail_authorized: Whether user has authorized Gmail access
            calendar_authorized: Whether user has authorized Calendar access
            
        Returns:
            List of discovered trips, sorted by confidence
        """
        logger.info("trip_discovery_started", user_id=user_id)
        
        # Create parallel discovery tasks
        tasks = []
        
        # Gmail discovery (if authorized and agent available)
        if gmail_authorized and self.gmail_agent:
            tasks.append(self._discover_from_gmail())
        
        # Calendar discovery (if authorized and agent available)
        if calendar_authorized and self.calendar_agent:
            tasks.append(self._discover_from_calendar())
        
        # Always available: Flight API lookup (if user provides booking ref)
        # This is handled separately via direct lookup
        
        # Run all discoveries in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results (each discovery method returns a list)
            all_trips = []
            for result in results:
                if isinstance(result, list):
                    all_trips.extend(result)
                elif isinstance(result, Exception):
                    logger.error("discovery_task_failed", error=str(result))
            
            # Consolidate and deduplicate
            consolidated = self._consolidate_trips(all_trips)
            
            # Sort by confidence
            consolidated.sort(key=lambda t: t.confidence, reverse=True)
            
            logger.info("trip_discovery_completed", trips_found=len(consolidated))
            
            return consolidated
        
        return []
    
    async def _discover_from_gmail(self) -> List[DiscoveredTrip]:
        """Discover trips from Gmail bookings"""
        logger.info("discovering_from_gmail")
        
        try:
            bookings = await self.gmail_agent.search_for_bookings()
            
            trips = []
            for booking in bookings:
                trip = DiscoveredTrip(
                    trip_id=booking.email_id,
                    source="gmail",
                    destination=booking.extracted_data.get('destination') or 
                               booking.extracted_data.get('route', '').split('→')[1].strip() if '→' in booking.extracted_data.get('route', '') else None,
                    dates={
                        'departure': booking.extracted_data.get('departure') or booking.extracted_data.get('departure_date'),
                        'return': booking.extracted_data.get('return') or booking.extracted_data.get('return_date')
                    },
                    travelers=booking.extracted_data.get('passengers') or 
                             [{}] * booking.extracted_data.get('travelers', 1),
                    cost=booking.extracted_data.get('total_cost'),
                    confidence=booking.confidence,
                    raw_data=booking.extracted_data,
                    display_summary=f"📧 {booking.subject} ({booking.booking_type})"
                )
                trips.append(trip)
            
            return trips
            
        except Exception as e:
            logger.error("gmail_discovery_failed", error=str(e))
            return []
    
    async def _discover_from_calendar(self) -> List[DiscoveredTrip]:
        """Discover trips from Google Calendar"""
        logger.info("discovering_from_calendar")
        
        try:
            events = await self.calendar_agent.search_for_trips()
            
            trips = []
            for event in events:
                trip = DiscoveredTrip(
                    trip_id=event.event_id,
                    source="calendar",
                    destination=event.location,
                    dates={
                        'departure': event.start_date,
                        'return': event.end_date
                    },
                    travelers=None,  # Calendar doesn't have traveler info
                    cost=None,
                    confidence=event.confidence,
                    raw_data=event.raw_data,
                    display_summary=f"📅 {event.title}"
                )
                trips.append(trip)
            
            return trips
            
        except Exception as e:
            logger.error("calendar_discovery_failed", error=str(e))
            return []
    
    def _consolidate_trips(self, trips: List[DiscoveredTrip]) -> List[DiscoveredTrip]:
        """
        Consolidate trips that are likely the same (same dates + destination)
        Merge information from different sources
        """
        if not trips:
            return []
        
        consolidated = []
        used_indices = set()
        
        for i, trip1 in enumerate(trips):
            if i in used_indices:
                continue
            
            # Find matching trips
            matches = [trip1]
            
            for j, trip2 in enumerate(trips[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                # Check if trips match (same destination + overlapping dates)
                if self._trips_match(trip1, trip2):
                    matches.append(trip2)
                    used_indices.add(j)
            
            # Merge matched trips
            if len(matches) > 1:
                merged = self._merge_trip_sources(matches)
                consolidated.append(merged)
            else:
                consolidated.append(trip1)
            
            used_indices.add(i)
        
        return consolidated
    
    def _trips_match(self, trip1: DiscoveredTrip, trip2: DiscoveredTrip) -> bool:
        """Check if two trips are likely the same"""
        
        # Same destination?
        if trip1.destination and trip2.destination:
            if trip1.destination.lower() != trip2.destination.lower():
                return False
        
        # Overlapping dates?
        dates1 = trip1.dates or {}
        dates2 = trip2.dates or {}
        
        if dates1.get('departure') and dates2.get('departure'):
            if dates1['departure'] == dates2['departure']:
                return True
        
        return False
    
    def _merge_trip_sources(self, trips: List[DiscoveredTrip]) -> DiscoveredTrip:
        """Merge multiple sources into one trip"""
        
        # Start with highest confidence trip
        base = max(trips, key=lambda t: t.confidence)
        
        # Merge data from other sources
        for trip in trips:
            if trip == base:
                continue
            
            # Merge destination (prefer more specific)
            if not base.destination and trip.destination:
                base.destination = trip.destination
            
            # Merge dates
            if base.dates and trip.dates:
                if not base.dates.get('departure') and trip.dates.get('departure'):
                    base.dates['departure'] = trip.dates['departure']
                if not base.dates.get('return') and trip.dates.get('return'):
                    base.dates['return'] = trip.dates['return']
            elif not base.dates and trip.dates:
                base.dates = trip.dates
            
            # Merge travelers (prefer non-empty)
            if not base.travelers and trip.travelers:
                base.travelers = trip.travelers
            
            # Merge cost (prefer non-None)
            if not base.cost and trip.cost:
                base.cost = trip.cost
        
        # Update display summary to show multi-source
        sources = list(set([t.source for t in trips]))
        base.display_summary = f"Found in: {', '.join(sources)}"
        base.confidence = min(sum(t.confidence for t in trips) / len(trips) + 0.1, 1.0)
        
        return base
    
    def format_discovered_trips_for_display(self, trips: List[DiscoveredTrip]) -> str:
        """
        Format discovered trips for conversational display
        
        Returns:
            Markdown formatted trip list
        """
        if not trips:
            return "I didn't find any upcoming trips in your email or calendar. Would you like to tell me about your trip?"
        
        parts = ["I found these upcoming trips! 🔍\n"]
        
        for i, trip in enumerate(trips[:5], 1):  # Max 5 trips
            parts.append(f"\n**{i}. {self._format_trip_title(trip)}**")
            
            # Source icons
            source_icons = {
                'gmail': '📧',
                'calendar': '📅',
                'flight_api': '✈️',
                'payment': '💳'
            }
            icon = source_icons.get(trip.source, '📌')
            parts.append(f"{icon} {trip.display_summary}")
            
            # Dates
            if trip.dates:
                dep = trip.dates.get('departure', '?')
                ret = trip.dates.get('return', '?')
                parts.append(f"📅 {dep} → {ret}")
            
            # Cost
            if trip.cost:
                parts.append(f"💰 ${trip.cost:,.0f}")
            
            # Confidence indicator
            if trip.confidence >= 0.9:
                parts.append("✅ High confidence")
            elif trip.confidence >= 0.7:
                parts.append("⚠️  Medium confidence - please verify")
            else:
                parts.append("❓ Low confidence - please confirm details")
            
            parts.append("")  # Blank line
        
        parts.append("\nWhich trip would you like insurance for? (Reply with the number or tell me about a different trip)")
        
        return "\n".join(parts)
    
    def _format_trip_title(self, trip: DiscoveredTrip) -> str:
        """Generate a title for the trip"""
        if trip.destination:
            if trip.dates and trip.dates.get('departure'):
                # Extract month
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(trip.dates['departure'])
                    month = date_obj.strftime('%b')
                    return f"{trip.destination} ({month})"
                except:
                    return f"{trip.destination}"
            return trip.destination
        
        return "Trip"
    
    async def lookup_flight_by_booking_ref(self, booking_ref: str) -> Optional[DiscoveredTrip]:
        """
        Look up a specific flight by booking reference
        
        Args:
            booking_ref: Flight booking reference
            
        Returns:
            Discovered trip or None if not found
        """
        logger.info("flight_lookup_requested", booking_ref=booking_ref)
        
        if not self.flight_agent:
            return None
        
        try:
            booking = await self.flight_agent.lookup_booking(booking_ref)
            
            if not booking:
                return None
            
            # Extract trip details
            trip_details = self.flight_agent.extract_trip_details(booking)
            
            # Create discovered trip
            trip = DiscoveredTrip(
                trip_id=booking_ref,
                source="flight_api",
                destination=trip_details.get('destination_country'),
                dates={
                    'departure': trip_details.get('departure_date'),
                    'return': trip_details.get('return_date')
                },
                travelers=trip_details.get('travelers'),
                cost=trip_details.get('flight_cost'),
                confidence=0.95,  # High confidence from direct API
                raw_data=booking,
                display_summary=f"✈️ {booking.get('airline')} {booking_ref}"
            )
            
            logger.info("flight_lookup_success", booking_ref=booking_ref, destination=trip.destination)
            
            return trip
            
        except Exception as e:
            logger.error("flight_lookup_failed", error=str(e), booking_ref=booking_ref)
            return None

