"""
TravelMate AI - Claims Analytics Service
Analyze historical claims data for risk scoring and intelligent recommendations
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.msig_claims import MSIGClaim
from app.claims.claims_db import get_claims_session
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()


class ClaimsAnalyticsService:
    """
    Analyze historical MSIG claims data for:
    - Destination risk scoring
    - Activity risk analysis
    - Average claim amounts
    - Claim frequency patterns
    - Product tier recommendations
    """
    
    def __init__(self, session: Session = None):
        """Initialize with database session"""
        self.session = session
    
    def get_destination_risk_profile(self, destination: str) -> Dict[str, Any]:
        """
        Analyze claims history for a specific destination
        
        Args:
            destination: Country/region name
            
        Returns:
            Risk profile with claim frequency, average amounts, common claim types
        """
        logger.info("claims_destination_analysis", destination=destination)
        
        try:
            # Get all claims for destination
            claims = self.session.query(MSIGClaim).filter(
                MSIGClaim.destination.ilike(f"%{destination}%")
            ).all()
            
            if not claims:
                logger.warning("claims_no_data_for_destination", destination=destination)
                return {
                    "destination": destination,
                    "total_claims": 0,
                    "risk_level": "unknown",
                    "message": "No historical claims data available for this destination"
                }
            
            # Calculate statistics
            total_claims = len(claims)
            total_incurred = sum(float(c.net_incurred or 0) for c in claims)
            avg_claim_amount = total_incurred / total_claims if total_claims > 0 else 0
            
            # Claim types distribution
            claim_types = {}
            for claim in claims:
                claim_type = claim.claim_type or "Unknown"
                claim_types[claim_type] = claim_types.get(claim_type, 0) + 1
            
            # Sort by frequency
            top_claim_types = sorted(
                claim_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Risk level (based on avg claim amount)
            if avg_claim_amount > 10000:
                risk_level = "high"
            elif avg_claim_amount > 5000:
                risk_level = "moderate"
            else:
                risk_level = "low"
            
            logger.info(
                "claims_destination_analysis_complete",
                destination=destination,
                total_claims=total_claims,
                avg_claim_amount=avg_claim_amount,
                risk_level=risk_level
            )
            
            return {
                "destination": destination,
                "total_claims": total_claims,
                "total_incurred_sgd": round(total_incurred, 2),
                "avg_claim_amount_sgd": round(avg_claim_amount, 2),
                "risk_level": risk_level,
                "top_claim_types": [
                    {"type": claim_type, "count": count, "percentage": round(count / total_claims * 100, 1)}
                    for claim_type, count in top_claim_types
                ],
                "recommendation": self._generate_destination_recommendation(avg_claim_amount, risk_level)
            }
            
        except Exception as e:
            logger.error("claims_destination_analysis_error", destination=destination, error=str(e))
            return {
                "destination": destination,
                "error": str(e),
                "risk_level": "unknown"
            }
    
    def get_claim_type_statistics(self, claim_type: str) -> Dict[str, Any]:
        """
        Analyze claims by type (e.g., medical, baggage, cancellation)
        
        Args:
            claim_type: Type of claim to analyze
            
        Returns:
            Statistics for this claim type
        """
        logger.info("claims_type_analysis", claim_type=claim_type)
        
        try:
            claims = self.session.query(MSIGClaim).filter(
                MSIGClaim.claim_type.ilike(f"%{claim_type}%")
            ).all()
            
            if not claims:
                return {
                    "claim_type": claim_type,
                    "total_claims": 0,
                    "message": "No historical claims data for this type"
                }
            
            total_claims = len(claims)
            total_incurred = sum(float(c.net_incurred or 0) for c in claims)
            avg_claim_amount = total_incurred / total_claims
            
            # Calculate percentiles
            amounts = sorted([float(c.net_incurred or 0) for c in claims])
            p50 = amounts[len(amounts) // 2] if amounts else 0
            p75 = amounts[int(len(amounts) * 0.75)] if amounts else 0
            p90 = amounts[int(len(amounts) * 0.90)] if amounts else 0
            
            return {
                "claim_type": claim_type,
                "total_claims": total_claims,
                "avg_claim_amount_sgd": round(avg_claim_amount, 2),
                "median_claim_sgd": round(p50, 2),
                "p75_claim_sgd": round(p75, 2),
                "p90_claim_sgd": round(p90, 2),
                "total_incurred_sgd": round(total_incurred, 2)
            }
            
        except Exception as e:
            logger.error("claims_type_analysis_error", claim_type=claim_type, error=str(e))
            return {"claim_type": claim_type, "error": str(e)}
    
    def get_comprehensive_risk_analysis(
        self,
        destination: str,
        claim_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive risk analysis combining destination and claim type data
        
        Args:
            destination: Destination country/region
            claim_types: Optional list of claim types to analyze
            
        Returns:
            Comprehensive risk analysis with recommendations
        """
        logger.info("claims_comprehensive_analysis", destination=destination, claim_types=claim_types)
        
        # Get destination profile
        dest_profile = self.get_destination_risk_profile(destination)
        
        # Get claim type stats if specified
        claim_type_stats = []
        if claim_types:
            for claim_type in claim_types:
                stats = self.get_claim_type_statistics(claim_type)
                if stats.get("total_claims", 0) > 0:
                    claim_type_stats.append(stats)
        
        # Generate comprehensive recommendation
        recommendation = self._generate_comprehensive_recommendation(
            dest_profile,
            claim_type_stats
        )
        
        return {
            "destination_profile": dest_profile,
            "claim_type_analysis": claim_type_stats,
            "overall_risk_level": dest_profile.get("risk_level", "unknown"),
            "recommendation": recommendation,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _generate_destination_recommendation(self, avg_claim_amount: float, risk_level: str) -> str:
        """Generate recommendation based on destination risk"""
        if risk_level == "high":
            return f"High-risk destination with average claims of SGD ${avg_claim_amount:,.0f}. We recommend comprehensive coverage with high medical limits (>$100K) and emergency evacuation."
        elif risk_level == "moderate":
            return f"Moderate-risk destination with average claims of SGD ${avg_claim_amount:,.0f}. Standard coverage recommended with medical limits around $50K-$100K."
        else:
            return f"Lower-risk destination with average claims of SGD ${avg_claim_amount:,.0f}. Basic coverage may be sufficient, but consider your activities."
    
    def _generate_comprehensive_recommendation(
        self,
        dest_profile: Dict[str, Any],
        claim_type_stats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive recommendation combining all factors"""
        
        # Base recommendation on destination risk
        risk_level = dest_profile.get("risk_level", "unknown")
        avg_claim = dest_profile.get("avg_claim_amount_sgd", 0)
        
        # Adjust based on specific claim types
        recommended_medical_limit = 50000  # default
        if risk_level == "high" or avg_claim > 10000:
            recommended_medical_limit = 100000
        elif risk_level == "low" and avg_claim < 3000:
            recommended_medical_limit = 30000
        
        # Check claim type stats for specific recommendations
        high_value_types = []
        for stat in claim_type_stats:
            if stat.get("p90_claim_sgd", 0) > recommended_medical_limit:
                high_value_types.append(stat["claim_type"])
        
        return {
            "recommended_medical_limit_sgd": recommended_medical_limit,
            "risk_level": risk_level,
            "key_considerations": [
                f"Average claim in this destination: SGD ${avg_claim:,.0f}",
                f"Risk level: {risk_level.upper()}",
                f"Recommended minimum medical coverage: SGD ${recommended_medical_limit:,.0f}"
            ] + (
                [f"High-value claims common for: {', '.join(high_value_types)}"]
                if high_value_types else []
            ),
            "policy_tier_suggestion": self._suggest_policy_tier(risk_level, avg_claim)
        }
    
    def _suggest_policy_tier(self, risk_level: str, avg_claim: float) -> str:
        """Suggest appropriate policy tier based on risk and claims"""
        if risk_level == "high" or avg_claim > 15000:
            return "Premium (Comprehensive coverage recommended)"
        elif risk_level == "moderate" or avg_claim > 5000:
            return "Standard (Balanced coverage)"
        else:
            return "Basic (Essential coverage)"

