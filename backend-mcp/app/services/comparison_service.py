"""
TravelMate AI - Policy Comparison Service
Multi-dimensional policy comparison with intelligent analysis
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.schemas.policy import PolicySchema, PolicyComparisonSchema
from app.mcp.resources import MCPResources
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PolicyComparisonService:
    """Service for comparing insurance policies"""
    
    def __init__(self, db: Session):
        self.db = db
        self.resources = MCPResources(db)
    
    def compare_policies(
        self,
        policy_ids: List[str],
        comparison_criteria: Optional[List[str]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> PolicyComparisonSchema:
        """
        Compare multiple policies across various dimensions
        
        Args:
            policy_ids: List of policy IDs to compare
            comparison_criteria: Specific criteria to focus on
            user_context: User trip details for personalized comparison
            
        Returns:
            Comprehensive comparison with recommendation
        """
        logger.info("compare_policies", policy_ids=policy_ids, criteria=comparison_criteria)
        
        # Get normalized policies
        policies = self.resources.get_normalized_policies(policy_ids)
        
        if len(policies) < 2:
            logger.warning("insufficient_policies_for_comparison", count=len(policies))
        
        # Build comparison matrix
        comparison_matrix = self._build_comparison_matrix(
            policies,
            comparison_criteria,
            user_context
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(policies, comparison_matrix, user_context)
        
        return PolicyComparisonSchema(
            policies=policies,
            comparison_matrix=comparison_matrix,
            recommendation=recommendation
        )
    
    def _build_comparison_matrix(
        self,
        policies: List[PolicySchema],
        criteria: Optional[List[str]],
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build detailed comparison matrix"""
        
        matrix = {
            "general_comparison": self._compare_general_conditions(policies),
            "benefits_comparison": self._compare_benefits(policies),
            "coverage_limits": self._compare_coverage_limits(policies),
            "exclusions": self._compare_exclusions(policies),
            "operational": self._compare_operational(policies),
            "value_assessment": self._assess_value(policies)
        }
        
        # Add user-specific comparison if context provided
        if user_context:
            matrix["personalized_fit"] = self._assess_personalized_fit(policies, user_context)
        
        return matrix
    
    def _compare_general_conditions(self, policies: List[PolicySchema]) -> Dict[str, Any]:
        """Compare Layer 1: General Conditions"""
        comparison = {}
        
        for policy in policies:
            gc = policy.general_conditions
            if gc:
                comparison[policy.policy_id] = {
                    "policy_name": policy.policy_name,
                    "age_range": f"{gc.age_min or 'N/A'} - {gc.age_max or 'N/A'} years",
                    "trip_duration": f"{gc.trip_duration_min_days or 0} - {gc.trip_duration_max_days or 'unlimited'} days",
                    "pre_existing_covered": gc.pre_existing_covered,
                    "trip_start_location": gc.trip_start_location or "Not specified",
                    "high_risk_activities_count": len(gc.high_risk_activities_excluded),
                    "destination_restrictions_count": len(gc.destination_restrictions)
                }
        
        return comparison
    
    def _compare_benefits(self, policies: List[PolicySchema]) -> Dict[str, Any]:
        """Compare Layer 2 & 3: Benefits"""
        # Get all unique benefit names
        all_benefit_names = set()
        for policy in policies:
            for benefit in policy.benefits:
                all_benefit_names.add(benefit.benefit_name)
        
        comparison = {}
        for benefit_name in sorted(all_benefit_names):
            comparison[benefit_name] = {}
            for policy in policies:
                # Find benefit in policy
                benefit = next(
                    (b for b in policy.benefits if b.benefit_name == benefit_name),
                    None
                )
                if benefit:
                    comparison[benefit_name][policy.policy_id] = {
                        "policy_name": policy.policy_name,
                        "coverage_limit": benefit.coverage_limit,
                        "currency": benefit.currency,
                        "has_sub_limits": len(benefit.sub_limits) > 0 if benefit.sub_limits else False,
                        "waiting_period_days": benefit.waiting_period_days
                    }
                else:
                    comparison[benefit_name][policy.policy_id] = {
                        "policy_name": policy.policy_name,
                        "coverage_limit": None,
                        "covered": False
                    }
        
        return comparison
    
    def _compare_coverage_limits(self, policies: List[PolicySchema]) -> Dict[str, Any]:
        """Compare absolute coverage limits"""
        limits = {}
        
        for policy in policies:
            total_coverage = sum(
                b.coverage_limit for b in policy.benefits
                if b.coverage_limit is not None
            )
            
            medical_coverage = sum(
                b.coverage_limit for b in policy.benefits
                if b.coverage_limit is not None and
                "medical" in b.benefit_name.lower()
            )
            
            limits[policy.policy_id] = {
                "policy_name": policy.policy_name,
                "total_benefits": len(policy.benefits),
                "total_coverage_value": total_coverage,
                "medical_coverage": medical_coverage,
                "has_unlimited_benefits": any(
                    b.coverage_limit is None or b.coverage_limit > 1000000
                    for b in policy.benefits
                )
            }
        
        return limits
    
    def _compare_exclusions(self, policies: List[PolicySchema]) -> Dict[str, Any]:
        """Compare exclusions across policies"""
        exclusions = {}
        
        for policy in policies:
            gc = policy.general_conditions
            if gc:
                exclusions[policy.policy_id] = {
                    "policy_name": policy.policy_name,
                    "high_risk_activities": gc.high_risk_activities_excluded,
                    "destination_restrictions": gc.destination_restrictions,
                    "benefit_specific_exclusions_count": sum(
                        1 for b in policy.benefits
                        if b.benefit_specific_exclusions
                    )
                }
        
        return exclusions
    
    def _compare_operational(self, policies: List[PolicySchema]) -> Dict[str, Any]:
        """Compare Layer 4: Operational details"""
        operational = {}
        
        for policy in policies:
            od = policy.operational_details
            if od:
                operational[policy.policy_id] = {
                    "policy_name": policy.policy_name,
                    "deductible": od.deductible_amount,
                    "copay_percentage": od.copay_percentage,
                    "claim_time_limit_days": od.claim_time_limit_days,
                    "has_provider_network": od.has_provider_network,
                    "emergency_hotline": od.emergency_hotline,
                    "claim_submission_methods": od.claim_submission_method
                }
        
        return operational
    
    def _assess_value(self, policies: List[PolicySchema]) -> Dict[str, Any]:
        """Assess value for money"""
        # Simple value assessment (can be enhanced with actual pricing)
        value = {}
        
        for policy in policies:
            total_coverage = sum(
                b.coverage_limit for b in policy.benefits
                if b.coverage_limit is not None
            )
            
            value[policy.policy_id] = {
                "policy_name": policy.policy_name,
                "total_coverage": total_coverage,
                "benefits_count": len(policy.benefits),
                "coverage_per_benefit": total_coverage / len(policy.benefits) if policy.benefits else 0,
                "comprehensiveness_score": len(policy.benefits) / 50  # Normalize to 0-1
            }
        
        return value
    
    def _assess_personalized_fit(
        self,
        policies: List[PolicySchema],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess how well each policy fits user's needs"""
        fit = {}
        
        # Extract user requirements
        user_age = user_context.get("age")
        trip_duration = user_context.get("trip_duration_days")
        has_pre_existing = user_context.get("has_pre_existing_conditions", False)
        destination = user_context.get("destination")
        
        for policy in policies:
            gc = policy.general_conditions
            if not gc:
                continue
            
            fit_score = 1.0
            reasons = []
            
            # Check age eligibility
            if user_age:
                if gc.age_min and user_age < gc.age_min:
                    fit_score *= 0
                    reasons.append(f"Below minimum age ({gc.age_min})")
                elif gc.age_max and user_age > gc.age_max:
                    fit_score *= 0
                    reasons.append(f"Above maximum age ({gc.age_max})")
            
            # Check trip duration
            if trip_duration:
                if gc.trip_duration_max_days and trip_duration > gc.trip_duration_max_days:
                    fit_score *= 0.5
                    reasons.append(f"Trip exceeds max duration ({gc.trip_duration_max_days} days)")
            
            # Check pre-existing conditions
            if has_pre_existing and not gc.pre_existing_covered:
                fit_score *= 0.3
                reasons.append("Pre-existing conditions not covered")
            
            # Check destination restrictions
            if destination and destination in gc.destination_restrictions:
                fit_score *= 0
                reasons.append(f"Destination {destination} is restricted")
            
            fit[policy.policy_id] = {
                "policy_name": policy.policy_name,
                "fit_score": fit_score,
                "is_eligible": fit_score > 0.5,
                "reasons": reasons if fit_score < 1.0 else ["Fully eligible"]
            }
        
        return fit
    
    def _generate_recommendation(
        self,
        policies: List[PolicySchema],
        comparison_matrix: Dict[str, Any],
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate natural language recommendation"""
        
        if not policies:
            return "No policies available for comparison."
        
        if len(policies) == 1:
            return f"Only {policies[0].policy_name} is available for your consideration."
        
        # Simple recommendation logic (can be enhanced with LLM)
        if user_context and "personalized_fit" in comparison_matrix:
            fit_scores = comparison_matrix["personalized_fit"]
            best_fit = max(
                fit_scores.items(),
                key=lambda x: x[1]["fit_score"]
            )
            
            best_policy_id = best_fit[0]
            best_policy = next(p for p in policies if p.policy_id == best_policy_id)
            
            return f"Based on your requirements, {best_policy.policy_name} appears to be the best fit with a fit score of {best_fit[1]['fit_score']:.1%}. It provides comprehensive coverage for your specific needs."
        
        # Fallback to coverage-based recommendation
        coverage_limits = comparison_matrix["coverage_limits"]
        best_coverage = max(
            coverage_limits.items(),
            key=lambda x: x[1]["total_coverage_value"]
        )
        
        best_policy = next(p for p in policies if p.policy_id == best_coverage[0])
        return f"{best_policy.policy_name} offers the highest total coverage value across all benefits."

