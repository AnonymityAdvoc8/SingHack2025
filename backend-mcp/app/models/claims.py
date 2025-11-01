"""
TravelMate AI - Claims Data Models
Historical claims data for risk analysis
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from datetime import datetime
from app.database import Base


class Claim(Base):
    """
    Historical claims data for predictive analytics
    """
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(100), unique=True, index=True)
    
    # Traveler information
    traveler_age = Column(Integer)
    traveler_age_group = Column(String(20))  # e.g., "18-30", "31-50", "51-65", "65+"
    
    # Trip information
    destination_country = Column(String(100), index=True)
    destination_region = Column(String(100))  # e.g., "Asia", "Europe"
    trip_duration_days = Column(Integer)
    trip_purpose = Column(String(50))  # e.g., "leisure", "business"
    
    # Activity information
    activity_type = Column(String(100), index=True)  # e.g., "skiing", "scuba", "general"
    high_risk_activity = Column(Boolean, default=False)
    
    # Claim details
    claim_type = Column(String(100), index=True)  # e.g., "medical", "cancellation", "baggage"
    claim_amount = Column(Float)
    claim_currency = Column(String(10), default="SGD")
    claim_status = Column(String(50))  # e.g., "approved", "rejected", "pending"
    
    # Incident information
    incident_date = Column(DateTime)
    incident_description = Column(Text)
    incident_category = Column(String(100))  # e.g., "injury", "illness", "theft"
    
    # Medical claims specific
    medical_condition = Column(String(255))
    hospitalization_days = Column(Integer, default=0)
    
    # Timestamps
    claim_submitted_at = Column(DateTime)
    claim_processed_at = Column(DateTime)
    
    # Additional data
    additional_metadata = Column(JSON)  # Flexible storage for additional fields (renamed from 'metadata')
    
    created_at = Column(DateTime, default=datetime.utcnow)

