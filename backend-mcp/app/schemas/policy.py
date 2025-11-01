"""
TravelMate AI - Policy Schemas
Pydantic schemas for policy data serialization
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class GeneralConditionSchema(BaseModel):
    """Layer 1: General Conditions"""
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    residency_required: bool = True
    residency_countries: Optional[List[str]] = None
    trip_start_location: Optional[str] = None
    trip_duration_min_days: Optional[int] = None
    trip_duration_max_days: Optional[int] = None
    pre_existing_covered: bool = False
    pre_existing_conditions: Optional[str] = None
    high_risk_activities_excluded: Optional[List[str]] = None
    destination_restrictions: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class BenefitSchema(BaseModel):
    """Layer 2 & 3: Benefits Structure and Conditions"""
    benefit_name: str
    benefit_code: Optional[str] = None
    benefit_category: Optional[str] = None
    coverage_limit: Optional[float] = None
    currency: str = "SGD"
    sub_limits: Optional[Dict[str, Any]] = None
    eligibility_conditions: Optional[str] = None
    waiting_period_days: int = 0
    documentation_required: Optional[List[str]] = None
    benefit_specific_exclusions: Optional[str] = None
    
    class Config:
        from_attributes = True


class OperationalDetailSchema(BaseModel):
    """Layer 4: Operational Details"""
    deductible_amount: float = 0
    deductible_currency: str = "SGD"
    copay_percentage: float = 0
    claim_submission_method: Optional[List[str]] = None
    claim_documents_required: Optional[List[str]] = None
    claim_time_limit_days: Optional[int] = None
    has_provider_network: bool = False
    provider_network_details: Optional[str] = None
    emergency_hotline: Optional[str] = None
    claims_email: Optional[str] = None
    claims_portal_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PolicySchema(BaseModel):
    """Complete policy with all 4 layers"""
    policy_id: str
    policy_name: str
    version: str = "1.0"
    product_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 4-layer taxonomy
    general_conditions: Optional[GeneralConditionSchema] = None
    benefits: List[BenefitSchema] = []
    operational_details: Optional[OperationalDetailSchema] = None
    
    # Metadata
    benefit_count: int = 0
    
    class Config:
        from_attributes = True


class PolicyComparisonSchema(BaseModel):
    """Policy comparison result"""
    policies: List[PolicySchema]
    comparison_matrix: Dict[str, Any]
    recommendation: Optional[str] = None


class PolicyQuestionAnswerSchema(BaseModel):
    """Answer to policy question with citations"""
    question: str
    answer: str
    citations: List[str] = []
    confidence: float = Field(ge=0, le=1)
    related_policies: List[str] = []

