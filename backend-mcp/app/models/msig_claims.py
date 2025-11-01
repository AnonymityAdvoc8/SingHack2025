"""
TravelMate AI - MSIG Claims Database Model
PostgreSQL database schema for historical claims data
"""

from sqlalchemy import Column, String, Date, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MSIGClaim(Base):
    """
    MSIG travel insurance claims data model
    Data source: PostgreSQL RDS (hackathon_db)
    Schema: hackathon.claims
    """
    
    __tablename__ = "claims"
    __table_args__ = {"schema": "hackathon"}
    
    # Primary Key
    claim_number = Column(String(50), primary_key=True, index=True)
    
    # Product Information
    product_category = Column(String(100))
    product_name = Column(String(200))
    
    # Claim Status
    claim_status = Column(String(100))
    
    # Dates
    accident_date = Column(Date)
    report_date = Column(Date)
    closed_date = Column(Date, nullable=True)
    
    # Location
    destination = Column(String(100), index=True)
    
    # Claim Classification
    claim_type = Column(String(100), index=True)
    cause_of_loss = Column(String(100))
    loss_type = Column(String(100))
    
    # Financial Details (Before Reinsurance)
    gross_incurred = Column(DECIMAL(10, 2))
    gross_paid = Column(DECIMAL(10, 2))
    gross_reserve = Column(DECIMAL(10, 2))
    
    # Financial Details (After Reinsurance)
    net_incurred = Column(DECIMAL(10, 2))
    net_paid = Column(DECIMAL(10, 2))
    net_reserve = Column(DECIMAL(10, 2))
    
    def __repr__(self):
        return f"<MSIGClaim(claim_number={self.claim_number}, destination={self.destination}, claim_type={self.claim_type}, net_incurred={self.net_incurred})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "claim_number": self.claim_number,
            "product_category": self.product_category,
            "product_name": self.product_name,
            "claim_status": self.claim_status,
            "accident_date": self.accident_date.isoformat() if self.accident_date else None,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "closed_date": self.closed_date.isoformat() if self.closed_date else None,
            "destination": self.destination,
            "claim_type": self.claim_type,
            "cause_of_loss": self.cause_of_loss,
            "loss_type": self.loss_type,
            "gross_incurred": float(self.gross_incurred) if self.gross_incurred else 0.0,
            "gross_paid": float(self.gross_paid) if self.gross_paid else 0.0,
            "gross_reserve": float(self.gross_reserve) if self.gross_reserve else 0.0,
            "net_incurred": float(self.net_incurred) if self.net_incurred else 0.0,
            "net_paid": float(self.net_paid) if self.net_paid else 0.0,
            "net_reserve": float(self.net_reserve) if self.net_reserve else 0.0,
        }

