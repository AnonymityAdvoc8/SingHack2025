"""
TravelMate AI - Quote Service  
Real quote generation with pricing logic (simplified for hackathon)
"""

from typing import List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from app.schemas.trip import (
    QuoteRequestSchema,
    QuoteResponseSchema,
    QuoteItemSchema,
    TripDetailsSchema
)
from app.services.eligibility_service import EligibilityService
from app.mcp.resources import MCPResources
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuoteService:
    """Service for generating insurance quotes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.resources = MCPResources(db)
        self.eligibility_service = EligibilityService(db)
    
    def generate_quote(
        self,
        quote_request: QuoteRequestSchema
    ) -> QuoteResponseSchema:
        """
        Generate real insurance quotes for eligible policies
        
        Args:
            quote_request: Quote request with trip details
            
        Returns:
            Quote response with pricing for all eligible policies
        """
        logger.info("generate_quote", 
                   destination=quote_request.trip_details.destination_country,
                   travelers=len(quote_request.trip_details.travelers))
        
        trip_details = quote_request.trip_details
        
        # Get policies to quote
        policy_ids = quote_request.policy_ids
        policies = self.resources.get_normalized_policies(policy_ids)
        
        # Check eligibility for each policy
        eligibility_results = self.eligibility_service.check_eligibility(
            trip_details,
            policy_id=None  # Check all
        )
        
        # Create eligibility map
        eligibility_map = {
            result.policy_id: result
            for result in eligibility_results
        }
        
        # Generate quotes
        quotes = []
        for policy in policies:
            eligibility = eligibility_map.get(policy.policy_id)
            
            if not eligibility:
                continue
            
            quote_item = self._generate_policy_quote(
                policy,
                trip_details,
                eligibility
            )
            quotes.append(quote_item)
        
        # Generate quote ID
        quote_id = f"Q-{uuid.uuid4().hex[:12].upper()}"
        
        # Determine recommended policy
        recommended_policy_id = self._determine_recommendation(quotes, trip_details)
        recommendation_rationale = self._generate_recommendation_rationale(
            quotes,
            trip_details,
            recommended_policy_id
        )
        
        return QuoteResponseSchema(
            quote_id=quote_id,
            trip_details=trip_details,
            quotes=quotes,
            recommended_policy_id=recommended_policy_id,
            recommendation_rationale=recommendation_rationale,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7)  # Quotes valid for 7 days
        )
    
    def _generate_policy_quote(
        self,
        policy: Any,
        trip_details: TripDetailsSchema,
        eligibility: Any
    ) -> QuoteItemSchema:
        """Generate quote for a specific policy"""
        
        # Calculate premium (simplified but realistic logic)
        base_premium_per_day_per_person = self._get_base_premium(policy, trip_details)
        
        num_travelers = len(trip_details.travelers)
        duration_days = trip_details.trip_duration_days
        
        # Base calculation
        total_premium = base_premium_per_day_per_person * num_travelers * duration_days
        
        # Age adjustments
        for traveler in trip_details.travelers:
            if traveler.age > 65:
                total_premium *= 1.5  # 50% surcharge for seniors
            elif traveler.age < 18:
                total_premium *= 0.7  # 30% discount for children
        
        # Destination risk factor
        high_risk_destinations = ["USA", "Canada", "Japan"]
        if trip_details.destination_country in high_risk_destinations:
            total_premium *= 1.3
        
        # Activity risk factor
        if trip_details.has_high_risk_activities:
            total_premium *= 1.4
        
        # Pre-existing conditions factor
        if any(t.has_pre_existing_conditions for t in trip_details.travelers):
            if policy.general_conditions and policy.general_conditions.pre_existing_covered:
                total_premium *= 1.8  # Higher premium but covered
        
        # Round to nearest dollar
        total_premium = round(total_premium, 2)
        
        # Build coverage summary
        coverage_summary = {
            "total_benefits": len(policy.benefits),
            "medical_coverage": sum(
                b.coverage_limit for b in policy.benefits
                if b.coverage_limit and "medical" in b.benefit_name.lower()
            ),
            "trip_cancellation": any(
                "cancellation" in b.benefit_name.lower()
                for b in policy.benefits
            ),
            "pre_existing_covered": (
                policy.general_conditions.pre_existing_covered
                if policy.general_conditions else False
            )
        }
        
        # Recommendation score (0-1)
        recommendation_score = self._calculate_recommendation_score(
            policy,
            trip_details,
            eligibility
        )
        
        return QuoteItemSchema(
            policy_id=policy.policy_id,
            policy_name=policy.policy_name,
            premium=total_premium,
            currency="SGD",
            coverage_summary=coverage_summary,
            is_eligible=eligibility.is_eligible,
            ineligibility_reasons=eligibility.reasons,
            recommendation_score=recommendation_score
        )
    
    def _get_base_premium(self, policy: Any, trip_details: TripDetailsSchema) -> float:
        """Calculate base premium per person per day"""
        
        # Simple heuristic based on total coverage
        total_coverage = sum(
            b.coverage_limit for b in policy.benefits
            if b.coverage_limit is not None
        )
        
        # Base rate: roughly 0.5% of coverage per trip
        if total_coverage > 0:
            base_per_trip = total_coverage * 0.005
            base_per_day = base_per_trip / max(trip_details.trip_duration_days, 1)
            base_per_person_per_day = base_per_day / max(len(trip_details.travelers), 1)
            
            # Ensure minimum and maximum
            base_per_person_per_day = max(2.0, min(50.0, base_per_person_per_day))
            
            return base_per_person_per_day
        
        # Fallback default
        return 5.0
    
    def _calculate_recommendation_score(
        self,
        policy: Any,
        trip_details: TripDetailsSchema,
        eligibility: Any
    ) -> float:
        """Calculate how well this policy fits the user's needs (0-1)"""
        
        if not eligibility.is_eligible:
            return 0.0
        
        score = 0.5  # Base score
        
        # Reward comprehensive coverage
        if len(policy.benefits) > 30:
            score += 0.2
        elif len(policy.benefits) > 20:
            score += 0.1
        
        # Reward pre-existing coverage if needed
        has_pre_existing = any(
            t.has_pre_existing_conditions
            for t in trip_details.travelers
        )
        if has_pre_existing and policy.general_conditions:
            if policy.general_conditions.pre_existing_covered:
                score += 0.2
            else:
                score -= 0.3
        
        # Reward high medical coverage for risky destinations
        high_risk_destinations = ["USA", "Canada"]
        if trip_details.destination_country in high_risk_destinations:
            medical_coverage = sum(
                b.coverage_limit for b in policy.benefits
                if b.coverage_limit and "medical" in b.benefit_name.lower()
            )
            if medical_coverage > 100000:
                score += 0.15
        
        # Ensure score is in valid range
        return max(0.0, min(1.0, score))
    
    def _determine_recommendation(
        self,
        quotes: List[QuoteItemSchema],
        trip_details: TripDetailsSchema
    ) -> Optional[str]:
        """Determine which policy to recommend"""
        
        # Filter to eligible policies only
        eligible_quotes = [q for q in quotes if q.is_eligible]
        
        if not eligible_quotes:
            return None
        
        # Recommend based on recommendation score
        best_quote = max(eligible_quotes, key=lambda q: q.recommendation_score or 0)
        return best_quote.policy_id
    
    def _generate_recommendation_rationale(
        self,
        quotes: List[QuoteItemSchema],
        trip_details: TripDetailsSchema,
        recommended_policy_id: Optional[str]
    ) -> Optional[str]:
        """Generate human-readable recommendation rationale"""
        
        if not recommended_policy_id:
            return "No eligible policies found for your trip requirements."
        
        recommended = next(
            (q for q in quotes if q.policy_id == recommended_policy_id),
            None
        )
        
        if not recommended:
            return None
        
        rationale_parts = [
            f"We recommend {recommended.policy_name} for your trip to {trip_details.destination_country}."
        ]
        
        # Add reasons
        if recommended.coverage_summary.get("pre_existing_covered"):
            rationale_parts.append("It covers pre-existing conditions.")
        
        medical = recommended.coverage_summary.get("medical_coverage", 0)
        if medical > 100000:
            rationale_parts.append(f"It provides comprehensive medical coverage up to ${medical:,.0f}.")
        
        rationale_parts.append(f"Total premium: ${recommended.premium:.2f} SGD for {trip_details.trip_duration_days} days.")
        
        return " ".join(rationale_parts)

