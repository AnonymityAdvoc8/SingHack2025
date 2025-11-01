"""
TravelMate AI - Trip and Quote Schemas
Pydantic schemas for trip details and insurance quotes
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class TripPurpose(str, Enum):
    """Trip purpose types"""
    LEISURE = "leisure"
    BUSINESS = "business"
    STUDY = "study"
    MEDICAL = "medical"


class ActivityType(str, Enum):
    """Activity types"""
    GENERAL = "general"
    SKIING = "skiing"
    SCUBA_DIVING = "scuba_diving"
    HIKING = "hiking"
    WATER_SPORTS = "water_sports"
    EXTREME_SPORTS = "extreme_sports"


class TravelerSchema(BaseModel):
    """Individual traveler information"""
    name: Optional[str] = None
    age: int = Field(gt=0, lt=120)
    has_pre_existing_conditions: bool = False
    pre_existing_conditions_description: Optional[str] = None


class TripDetailsSchema(BaseModel):
    """Trip information extracted from user conversation"""
    destination_country: str
    destination_region: Optional[str] = None
    departure_date: date
    return_date: date
    trip_duration_days: int = Field(gt=0)
    trip_purpose: TripPurpose = TripPurpose.LEISURE
    
    # Travelers
    travelers: List[TravelerSchema]
    
    # Activities
    planned_activities: List[ActivityType] = [ActivityType.GENERAL]
    has_high_risk_activities: bool = False
    
    # Investment
    estimated_trip_cost: Optional[float] = None
    currency: str = "SGD"


class QuoteRequestSchema(BaseModel):
    """Quote request"""
    trip_details: TripDetailsSchema
    policy_ids: Optional[List[str]] = None  # If None, quote all eligible
    requested_by_user_id: Optional[str] = None


class QuoteItemSchema(BaseModel):
    """Individual quote for a policy"""
    policy_id: str
    policy_name: str
    premium: float
    currency: str = "SGD"
    coverage_summary: dict
    is_eligible: bool = True
    ineligibility_reasons: List[str] = []
    recommendation_score: Optional[float] = None  # 0-1 based on trip risk
    api_metadata: Optional[Dict[str, Any]] = None  # Store API-specific data (quote_id, offer_id, etc.)


class QuoteResponseSchema(BaseModel):
    """Quote response with multiple options"""
    quote_id: str
    trip_details: TripDetailsSchema
    quotes: List[QuoteItemSchema]
    recommended_policy_id: Optional[str] = None
    recommendation_rationale: Optional[str] = None
    created_at: datetime
    expires_at: datetime


class EligibilityCheckSchema(BaseModel):
    """Eligibility check request"""
    trip_details: TripDetailsSchema
    policy_id: Optional[str] = None  # If None, check all policies


class EligibilityResultSchema(BaseModel):
    """Eligibility check result"""
    policy_id: str
    policy_name: str
    is_eligible: bool
    eligible_travelers: List[int] = []  # Indexes of eligible travelers
    ineligible_travelers: List[int] = []
    reasons: List[str] = []
    warnings: List[str] = []


class ScenarioAnalysisSchema(BaseModel):
    """Scenario analysis request"""
    scenario_description: str
    trip_details: Optional[TripDetailsSchema] = None
    policy_ids: Optional[List[str]] = None


class ScenarioAnalysisResultSchema(BaseModel):
    """Scenario analysis result"""
    scenario_description: str
    coverage_analysis: Dict[str, Any]
    covered_by_policies: List[str] = []
    not_covered_by_policies: List[str] = []
    coverage_gaps: List[str] = []
    recommendations: List[str] = []

