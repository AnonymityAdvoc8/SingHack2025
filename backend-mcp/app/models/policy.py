"""
TravelMate AI - Policy Data Models
SQLAlchemy models for storing normalized policy data
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Policy(Base):
    """
    Main policy table - stores policy metadata
    """
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(100), unique=True, index=True, nullable=False)
    policy_name = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0")
    product_type = Column(String(100))  # e.g., "Scootsurance", "TravelEasy"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Raw policy text for citations
    original_text = Column(Text)
    
    # Relationships
    general_conditions = relationship("GeneralCondition", back_populates="policy", cascade="all, delete-orphan")
    benefits = relationship("Benefit", back_populates="policy", cascade="all, delete-orphan")
    operational_details = relationship("OperationalDetail", back_populates="policy", cascade="all, delete-orphan")


class GeneralCondition(Base):
    """
    Layer 1: General Conditions
    Eligibility requirements and general exclusions
    """
    __tablename__ = "general_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    
    # Age eligibility
    age_min = Column(Integer)
    age_max = Column(Integer)
    
    # Residency
    residency_required = Column(Boolean, default=True)
    residency_countries = Column(JSON)  # List of allowed countries
    
    # Trip requirements
    trip_start_location = Column(String(100))  # e.g., "Singapore"
    trip_duration_min_days = Column(Integer)
    trip_duration_max_days = Column(Integer)
    
    # Pre-existing conditions
    pre_existing_covered = Column(Boolean, default=False)
    pre_existing_conditions = Column(Text)  # Description or rules
    
    # Activity exclusions
    high_risk_activities_excluded = Column(JSON)  # List of excluded activities
    
    # Destination restrictions
    destination_restrictions = Column(JSON)  # List of excluded or restricted countries
    
    # Original text citation
    original_text_section = Column(Text)
    
    # Relationship
    policy = relationship("Policy", back_populates="general_conditions")


class Benefit(Base):
    """
    Layer 2 & 3: Benefits Structure and Conditions
    Coverage limits, eligibility per benefit, and benefit-specific exclusions
    """
    __tablename__ = "benefits"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    
    # Benefit identification
    benefit_name = Column(String(255), nullable=False)  # e.g., "Medical Expenses"
    benefit_code = Column(String(50))
    benefit_category = Column(String(100))  # e.g., "Medical", "Trip Cancellation"
    
    # Coverage limits (Layer 2)
    coverage_limit = Column(Float)  # Maximum coverage amount
    currency = Column(String(10), default="SGD")
    sub_limits = Column(JSON)  # Dict of sub-limits, e.g., {"dental": 500, "optical": 300}
    
    # Benefit conditions (Layer 3)
    eligibility_conditions = Column(Text)
    waiting_period_days = Column(Integer, default=0)
    documentation_required = Column(JSON)  # List of required documents
    benefit_specific_exclusions = Column(Text)
    
    # Original text citation
    original_text_section = Column(Text)
    
    # Relationship
    policy = relationship("Policy", back_populates="benefits")


class OperationalDetail(Base):
    """
    Layer 4: Operational Details
    Deductibles, co-pays, claim procedures, time limits
    """
    __tablename__ = "operational_details"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    
    # Deductibles & co-pays
    deductible_amount = Column(Float, default=0)
    deductible_currency = Column(String(10), default="SGD")
    copay_percentage = Column(Float, default=0)  # e.g., 20 = 20% co-pay
    
    # Claim procedures
    claim_submission_method = Column(JSON)  # List: ["online", "email", "post"]
    claim_documents_required = Column(JSON)  # List of standard documents
    claim_time_limit_days = Column(Integer)  # Days to submit claim after incident
    
    # Provider networks
    has_provider_network = Column(Boolean, default=False)
    provider_network_details = Column(Text)
    
    # Contact information
    emergency_hotline = Column(String(50))
    claims_email = Column(String(255))
    claims_portal_url = Column(String(500))
    
    # Original text citation
    original_text_section = Column(Text)
    
    # Relationship
    policy = relationship("Policy", back_populates="operational_details")

