"""
TravelMate AI - MCP Resources Layer
Provides data access interfaces following MCP protocol
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.policy import Policy, GeneralCondition, Benefit, OperationalDetail
from app.schemas.policy import PolicySchema, GeneralConditionSchema, BenefitSchema, OperationalDetailSchema
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPResources:
    """MCP Resources Layer - Data Access Interfaces"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Resource 1: Normalized Policies
    def get_normalized_policies(self, policy_ids: Optional[List[str]] = None) -> List[PolicySchema]:
        """
        Get structured policy data for algorithmic processing
        
        Args:
            policy_ids: Optional list of policy IDs to filter
            
        Returns:
            List of normalized policy schemas
        """
        logger.info("get_normalized_policies", policy_ids=policy_ids)
        
        query = self.db.query(Policy)
        if policy_ids:
            query = query.filter(Policy.policy_id.in_(policy_ids))
        
        policies = query.all()
        
        result = []
        for policy in policies:
            # Get first general condition (should only be one)
            gc = policy.general_conditions[0] if policy.general_conditions else None
            od = policy.operational_details[0] if policy.operational_details else None
            
            policy_data = PolicySchema(
                policy_id=policy.policy_id,
                policy_name=policy.policy_name,
                version=policy.version,
                product_type=policy.product_type,
                created_at=policy.created_at,
                updated_at=policy.updated_at,
                general_conditions=GeneralConditionSchema.from_orm(gc) if gc else None,
                benefits=[BenefitSchema.from_orm(b) for b in policy.benefits],
                operational_details=OperationalDetailSchema.from_orm(od) if od else None,
                benefit_count=len(policy.benefits)
            )
            result.append(policy_data)
        
        logger.info("normalized_policies_retrieved", count=len(result))
        return result
    
    # Resource 2: Original Policy Text
    def get_original_policy_text(
        self,
        policy_id: str,
        section: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get raw policy language for citations and legal precision
        
        Args:
            policy_id: Policy identifier
            section: Optional section filter (e.g., "benefits", "conditions")
            
        Returns:
            Dictionary with original text and metadata
        """
        logger.info("get_original_policy_text", policy_id=policy_id, section=section)
        
        policy = self.db.query(Policy).filter(Policy.policy_id == policy_id).first()
        
        if not policy:
            logger.error("policy_not_found", policy_id=policy_id)
            return {"error": f"Policy {policy_id} not found"}
        
        # If section specified, try to find relevant portion
        if section:
            # This is a simple implementation - could be enhanced with better text parsing
            text_lower = policy.original_text.lower()
            section_lower = section.lower()
            
            # Try to find section in text
            if section_lower in text_lower:
                start_idx = text_lower.index(section_lower)
                # Get surrounding context (1000 chars before and after)
                context_start = max(0, start_idx - 1000)
                context_end = min(len(policy.original_text), start_idx + 2000)
                relevant_text = policy.original_text[context_start:context_end]
                
                return {
                    "policy_id": policy_id,
                    "policy_name": policy.policy_name,
                    "section": section,
                    "text": relevant_text,
                    "is_excerpt": True
                }
        
        # Return full text
        return {
            "policy_id": policy_id,
            "policy_name": policy.policy_name,
            "text": policy.original_text,
            "is_excerpt": False,
            "length": len(policy.original_text)
        }
    
    # Resource 3: User Session (In-memory for now, can use Redis)
    _sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_user_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get user conversation context
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data with conversation history and extracted info
        """
        logger.info("get_user_session", session_id=session_id)
        
        if session_id not in self._sessions:
            # Initialize new session
            self._sessions[session_id] = {
                "session_id": session_id,
                "conversation_history": [],
                "extracted_trip_details": None,
                "selected_policies": [],
                "current_quotes": None,
                "created_at": None,
                "updated_at": None
            }
        
        return self._sessions[session_id]
    
    def update_user_session(self, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user session with new data"""
        logger.info("update_user_session", session_id=session_id)
        
        session = self.get_user_session(session_id)
        session.update(data)
        self._sessions[session_id] = session
        
        return session
    
    # Resource 4: Taxonomy Schema
    def get_taxonomy_schema(self) -> Dict[str, Any]:
        """
        Get taxonomy structure for reference
        
        Returns:
            Taxonomy schema with layer definitions
        """
        logger.info("get_taxonomy_schema")
        
        return {
            "taxonomy_name": "Travel Insurance Product Taxonomy",
            "version": "1.0",
            "layers": {
                "layer_1_general_conditions": {
                    "description": "Eligibility requirements and general exclusions",
                    "fields": [
                        "age_min", "age_max",
                        "residency_required", "residency_countries",
                        "trip_start_location",
                        "trip_duration_min_days", "trip_duration_max_days",
                        "pre_existing_covered", "pre_existing_conditions",
                        "high_risk_activities_excluded",
                        "destination_restrictions"
                    ]
                },
                "layer_2_benefits_structure": {
                    "description": "Coverage limits and benefits",
                    "fields": [
                        "benefit_name", "benefit_code", "benefit_category",
                        "coverage_limit", "currency", "sub_limits"
                    ]
                },
                "layer_3_benefit_conditions": {
                    "description": "Benefit-specific eligibility and exclusions",
                    "fields": [
                        "eligibility_conditions", "waiting_period_days",
                        "documentation_required", "benefit_specific_exclusions"
                    ]
                },
                "layer_4_operational": {
                    "description": "Deductibles, claims procedures, operational details",
                    "fields": [
                        "deductible_amount", "copay_percentage",
                        "claim_submission_method", "claim_documents_required",
                        "claim_time_limit_days", "has_provider_network",
                        "emergency_hotline", "claims_email", "claims_portal_url"
                    ]
                }
            },
            "data_access_pattern": "dual",
            "access_methods": {
                "normalized": "get_normalized_policies() - For algorithmic processing",
                "original": "get_original_policy_text() - For citations and legal precision"
            }
        }

