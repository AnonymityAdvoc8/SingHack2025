"""
TravelMate AI - Eligibility Service
Real eligibility checking against policy conditions
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.schemas.trip import TripDetailsSchema, EligibilityResultSchema
from app.mcp.resources import MCPResources
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EligibilityService:
    """Service for checking user eligibility against policies"""
    
    def __init__(self, db: Session):
        self.db = db
        self.resources = MCPResources(db)
    
    def check_eligibility(
        self,
        trip_details: TripDetailsSchema,
        policy_id: Optional[str] = None
    ) -> List[EligibilityResultSchema]:
        """
        Check eligibility for one or all policies
        
        Args:
            trip_details: User's trip information
            policy_id: Specific policy to check, or None for all
            
        Returns:
            List of eligibility results
        """
        logger.info("check_eligibility", policy_id=policy_id, travelers=len(trip_details.travelers))
        
        # Get policies to check
        policy_ids = [policy_id] if policy_id else None
        policies = self.resources.get_normalized_policies(policy_ids)
        
        results = []
        for policy in policies:
            result = self._check_policy_eligibility(policy, trip_details)
            results.append(result)
        
        return results
    
    def _check_policy_eligibility(
        self,
        policy,
        trip_details: TripDetailsSchema
    ) -> EligibilityResultSchema:
        """Check eligibility for a specific policy"""
        
        gc = policy.general_conditions
        if not gc:
            # No conditions means universally eligible (unlikely but handle it)
            return EligibilityResultSchema(
                policy_id=policy.policy_id,
                policy_name=policy.policy_name,
                is_eligible=True,
                eligible_travelers=list(range(len(trip_details.travelers))),
                ineligible_travelers=[],
                reasons=["No specific eligibility restrictions"],
                warnings=[]
            )
        
        eligible_travelers = []
        ineligible_travelers = []
        reasons = []
        warnings = []
        
        # Check each traveler
        for idx, traveler in enumerate(trip_details.travelers):
            traveler_eligible = True
            traveler_reasons = []
            
            # Age check
            if gc.age_min is not None and traveler.age < gc.age_min:
                traveler_eligible = False
                traveler_reasons.append(f"Traveler {idx+1}: Age {traveler.age} below minimum {gc.age_min}")
            
            if gc.age_max is not None and traveler.age > gc.age_max:
                traveler_eligible = False
                traveler_reasons.append(f"Traveler {idx+1}: Age {traveler.age} above maximum {gc.age_max}")
            
            # Pre-existing conditions check
            if traveler.has_pre_existing_conditions and not gc.pre_existing_covered:
                traveler_eligible = False
                traveler_reasons.append(f"Traveler {idx+1}: Pre-existing conditions not covered")
            elif traveler.has_pre_existing_conditions and gc.pre_existing_covered:
                warnings.append(f"Traveler {idx+1}: Pre-existing conditions require special documentation")
            
            if traveler_eligible:
                eligible_travelers.append(idx)
            else:
                ineligible_travelers.append(idx)
                reasons.extend(traveler_reasons)
        
        # Trip duration check
        if gc.trip_duration_min_days and trip_details.trip_duration_days < gc.trip_duration_min_days:
            reasons.append(f"Trip duration {trip_details.trip_duration_days} days below minimum {gc.trip_duration_min_days}")
        
        if gc.trip_duration_max_days and trip_details.trip_duration_days > gc.trip_duration_max_days:
            reasons.append(f"Trip duration {trip_details.trip_duration_days} days exceeds maximum {gc.trip_duration_max_days}")
        
        # Destination restrictions
        if gc.destination_restrictions and trip_details.destination_country in gc.destination_restrictions:
            reasons.append(f"Destination {trip_details.destination_country} is restricted")
        
        # High-risk activities check
        if gc.high_risk_activities_excluded:
            for activity in trip_details.planned_activities:
                activity_name = activity.value
                if activity_name in gc.high_risk_activities_excluded:
                    warnings.append(f"Activity '{activity_name}' may not be covered - check exclusions")
        
        # Trip start location check
        if gc.trip_start_location and gc.trip_start_location.lower() != "singapore":
            warnings.append(f"Policy requires trip to start from {gc.trip_start_location}")
        
        # Overall eligibility
        is_eligible = (
            len(eligible_travelers) > 0 and
            len(reasons) == len([r for r in reasons if "Traveler" in r])  # Only traveler-specific reasons
        )
        
        if not is_eligible and not reasons:
            reasons = ["Policy requirements not met"]
        
        return EligibilityResultSchema(
            policy_id=policy.policy_id,
            policy_name=policy.policy_name,
            is_eligible=is_eligible,
            eligible_travelers=eligible_travelers,
            ineligible_travelers=ineligible_travelers,
            reasons=reasons if not is_eligible else [],
            warnings=warnings
        )

