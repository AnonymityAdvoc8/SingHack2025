"""
Trip Context Manager
Persistent state management for trip details across conversation turns
Ensures we never lose information or ask for the same thing twice
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TripContext:
    """Persistent trip context that accumulates across conversation"""
    
    # Core trip data
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    destination_region: Optional[str] = None
    
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    trip_duration_days: Optional[int] = None
    
    travelers: List[Dict[str, Any]] = field(default_factory=list)
    num_travelers: Optional[int] = None
    
    planned_activities: List[str] = field(default_factory=list)
    has_high_risk_activities: bool = False
    
    trip_purpose: Optional[str] = None
    trip_cost: Optional[float] = None
    currency: Optional[str] = None
    
    # Discovery metadata
    source: Optional[str] = None  # conversation, gmail, flight_api, calendar
    booking_reference: Optional[str] = None
    airline: Optional[str] = None
    
    # Completeness tracking
    is_complete: bool = False
    missing_fields: List[str] = field(default_factory=list)
    confidence: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def merge(self, new_data: Dict[str, Any]) -> 'TripContext':
        """
        Merge new data into existing context
        Never overwrites with None/empty - only adds/updates with actual values
        
        Args:
            new_data: New trip data to merge
            
        Returns:
            Self (for chaining)
        """
        # Update simple fields (only if new value is not None/empty)
        simple_fields = [
            'destination_country', 'destination_city', 'destination_region',
            'departure_date', 'return_date', 'trip_duration_days',
            'trip_purpose', 'trip_cost', 'currency', 'source',
            'booking_reference', 'airline', 'num_travelers', 'has_high_risk_activities'
        ]
        
        for field_name in simple_fields:
            new_value = new_data.get(field_name)
            if new_value is not None and new_value != '':
                # Only update if we don't have it OR new value is more specific
                current_value = getattr(self, field_name)
                if current_value is None or current_value == '' or (isinstance(new_value, str) and len(str(new_value)) > len(str(current_value))):
                    setattr(self, field_name, new_value)
        
        # Merge travelers list (more complex)
        new_travelers = new_data.get('travelers', [])
        if new_travelers and isinstance(new_travelers, list):
            # If we don't have travelers yet, use new ones
            if not self.travelers:
                self.travelers = new_travelers
            else:
                # Merge traveler data (match by index or name)
                for i, new_traveler in enumerate(new_travelers):
                    if i < len(self.travelers):
                        # Update existing traveler with new info
                        for key, value in new_traveler.items():
                            if value is not None and (self.travelers[i].get(key) is None or self.travelers[i].get(key) == ''):
                                self.travelers[i][key] = value
                    else:
                        # Add new traveler
                        self.travelers.append(new_traveler)
        
        # Merge activities (append unique)
        new_activities = new_data.get('planned_activities', [])
        if new_activities and isinstance(new_activities, list):
            for activity in new_activities:
                if activity and activity not in self.planned_activities and activity != "general":
                    self.planned_activities.append(activity)
        
        # Update metadata
        if new_data.get('is_complete'):
            self.is_complete = True
        
        self.missing_fields = new_data.get('missing_fields', self.missing_fields)
        
        if new_data.get('confidence'):
            # Take maximum confidence
            self.confidence = max(self.confidence, new_data.get('confidence', 0))
        
        self.updated_at = datetime.now()
        
        return self
    
    def to_dict(self, include_defaults: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary for API/storage
        
        Args:
            include_defaults: If True, fill in sensible defaults for quote generation
        """
        data = {
            'destination_country': self.destination_country,
            'destination_city': self.destination_city,
            'destination_region': self.destination_region,
            'departure_date': self.departure_date,
            'return_date': self.return_date,
            'trip_duration_days': self.trip_duration_days,
            'travelers': self.travelers,
            'num_travelers': self.num_travelers or len(self.travelers),
            'planned_activities': self.planned_activities or ['general'],
            'has_high_risk_activities': self.has_high_risk_activities,
            'trip_purpose': self.trip_purpose,
            'trip_cost': self.trip_cost,
            'currency': self.currency,
            'source': self.source,
            'booking_reference': self.booking_reference,
            'airline': self.airline,
            'is_complete': self.is_complete,
            'missing_fields': self.missing_fields,
            'confidence': self.confidence
        }
        
        # Add sensible defaults for quote generation if needed
        if include_defaults:
            from datetime import datetime, timedelta
            
            # If we have duration but no dates, calculate dates from today
            if data['trip_duration_days'] and not data['departure_date']:
                future_date = datetime.now() + timedelta(days=30)
                data['departure_date'] = future_date.strftime('%Y-%m-%d')
                data['return_date'] = (future_date + timedelta(days=data['trip_duration_days'])).strftime('%Y-%m-%d')
            
            # Default trip purpose (lowercase for enum)
            if not data['trip_purpose']:
                data['trip_purpose'] = 'leisure'
            
            # Default currency
            if not data['currency']:
                data['currency'] = 'SGD'
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TripContext':
        """Create TripContext from dictionary"""
        return cls(
            destination_country=data.get('destination_country'),
            destination_city=data.get('destination_city'),
            destination_region=data.get('destination_region'),
            departure_date=data.get('departure_date'),
            return_date=data.get('return_date'),
            trip_duration_days=data.get('trip_duration_days'),
            travelers=data.get('travelers', []),
            num_travelers=data.get('num_travelers'),
            planned_activities=data.get('planned_activities', []),
            has_high_risk_activities=data.get('has_high_risk_activities', False),
            trip_purpose=data.get('trip_purpose'),
            trip_cost=data.get('trip_cost'),
            currency=data.get('currency'),
            source=data.get('source'),
            booking_reference=data.get('booking_reference'),
            airline=data.get('airline'),
            is_complete=data.get('is_complete', False),
            missing_fields=data.get('missing_fields', []),
            confidence=data.get('confidence', 0.0)
        )
    
    def get_missing_critical_fields(self) -> List[str]:
        """
        Identify critical missing fields needed for quote
        For quote generation, we only REQUIRE: destination, duration OR dates, and ages
        
        Returns:
            List of missing field names
        """
        missing = []
        
        if not self.destination_country:
            missing.append('destination_country')
        
        # We need EITHER duration OR both dates (not both required)
        has_duration_or_dates = self.trip_duration_days or (self.departure_date and self.return_date)
        if not has_duration_or_dates:
            if not self.trip_duration_days:
                missing.append('return_date_or_duration')
            # Don't add departure_date if we have duration - it's optional for quoting
        
        if not self.travelers and not self.num_travelers:
            missing.append('travelers_count')
        
        # Check if travelers have age info (CRITICAL for quote)
        if self.travelers:
            for i, traveler in enumerate(self.travelers):
                if traveler.get('age') is None:
                    missing.append(f'traveler_{i+1}_age')
        elif self.num_travelers and self.num_travelers > 0:
            # Have count but no traveler objects with ages
            for i in range(self.num_travelers):
                missing.append(f'traveler_{i+1}_age')
        
        return missing
    
    def calculate_completeness(self) -> float:
        """
        Calculate how complete the trip data is (0.0 to 1.0)
        """
        total_fields = 8  # destination, dates, duration, travelers, age, activities, purpose
        filled_fields = 0
        
        if self.destination_country:
            filled_fields += 1
        if self.departure_date:
            filled_fields += 1
        if self.return_date or self.trip_duration_days:
            filled_fields += 1
        if self.travelers or self.num_travelers:
            filled_fields += 1
        if self.travelers and all(t.get('age') for t in self.travelers):
            filled_fields += 1
        if self.planned_activities and self.planned_activities != ['general']:
            filled_fields += 1
        if self.trip_purpose:
            filled_fields += 1
        
        # Source adds confidence
        if self.source and self.source != 'conversation':
            filled_fields += 0.5  # Bonus for verified source
        
        return min(filled_fields / total_fields, 1.0)

