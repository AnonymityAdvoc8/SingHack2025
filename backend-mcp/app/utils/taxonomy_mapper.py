"""
TravelMate AI - Taxonomy Mapper
Map policy text to 4-layer taxonomy using Groq LLM
"""

import json
from pathlib import Path
from typing import Dict, Any
from groq import Groq
from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TaxonomyMapper:
    """Map policy documents to standardized taxonomy"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.taxonomy_template = self._load_taxonomy_template()
    
    def _load_taxonomy_template(self) -> Dict[str, Any]:
        """Load the taxonomy template"""
        try:
            with open(settings.taxonomy_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("failed_to_load_taxonomy", error=str(e))
            raise
    
    def map_policy_to_taxonomy(
        self,
        policy_text: str,
        policy_name: str,
        layer: str = "all"
    ) -> Dict[str, Any]:
        """
        Map policy text to taxonomy structure using LLM
        
        Args:
            policy_text: Raw policy text
            policy_name: Name of policy (e.g., "Scootsurance")
            layer: Which layer to map ("all", "layer_1", "layer_2", etc.)
            
        Returns:
            Mapped taxonomy data
        """
        logger.info("mapping_policy_to_taxonomy", policy=policy_name, layer=layer)
        
        if layer == "all" or layer == "layer_1":
            layer_1 = self._map_layer_1_general_conditions(policy_text, policy_name)
        else:
            layer_1 = {}
        
        if layer == "all" or layer == "layer_2":
            layer_2 = self._map_layer_2_benefits_structure(policy_text, policy_name)
        else:
            layer_2 = {}
        
        if layer == "all" or layer == "layer_3":
            layer_3 = self._map_layer_3_benefit_conditions(policy_text, policy_name)
        else:
            layer_3 = {}
        
        if layer == "all" or layer == "layer_4":
            layer_4 = self._map_layer_4_operational(policy_text, policy_name)
        else:
            layer_4 = {}
        
        return {
            "policy_name": policy_name,
            "layer_1_general_conditions": layer_1,
            "layer_2_benefits_structure": layer_2,
            "layer_3_benefit_conditions": layer_3,
            "layer_4_operational": layer_4
        }
    
    def _map_layer_1_general_conditions(
        self,
        policy_text: str,
        policy_name: str
    ) -> Dict[str, Any]:
        """Extract Layer 1: General Conditions"""
        
        prompt = f"""You are an insurance policy analyst. Extract the following information from the policy document:

Policy: {policy_name}

Extract these LAYER 1 fields:
1. Age eligibility (minimum and maximum age)
2. Residency requirements (which countries/residency required)
3. Trip start location requirements (must start from Singapore?)
4. Trip duration limits (minimum and maximum days)
5. Pre-existing condition coverage (yes/no and details)
6. High-risk activity exclusions (list of excluded activities like skiing, scuba diving)
7. Destination restrictions (any excluded or restricted countries)

For each field, provide:
- The extracted value
- The exact text from the policy (citation)

Format your response as JSON with this structure:
{{
    "age_min": <number>,
    "age_max": <number>,
    "age_citation": "<exact text>",
    "residency_required": <boolean>,
    "residency_countries": ["Singapore", ...],
    "residency_citation": "<exact text>",
    "trip_start_location": "<location>",
    "trip_start_citation": "<exact text>",
    "trip_duration_min_days": <number>,
    "trip_duration_max_days": <number>,
    "trip_duration_citation": "<exact text>",
    "pre_existing_covered": <boolean>,
    "pre_existing_conditions": "<details>",
    "pre_existing_citation": "<exact text>",
    "high_risk_activities_excluded": ["activity1", "activity2", ...],
    "activities_citation": "<exact text>",
    "destination_restrictions": ["country1", ...],
    "destination_citation": "<exact text>"
}}

Policy Text:
{policy_text[:8000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyst. Extract information accurately and cite sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON from response (may be wrapped in markdown)
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            parsed = json.loads(result.strip())
            logger.info("layer_1_mapped", policy=policy_name)
            return parsed
            
        except Exception as e:
            logger.error("layer_1_mapping_failed", policy=policy_name, error=str(e))
            raise
    
    def _map_layer_2_benefits_structure(
        self,
        policy_text: str,
        policy_name: str
    ) -> Dict[str, Any]:
        """Extract Layer 2: Benefits Structure (coverage limits)"""
        
        prompt = f"""You are an insurance policy analyst. Extract the BENEFITS and COVERAGE LIMITS from this policy.

Policy: {policy_name}

Extract all benefits with their coverage limits. Common benefits include:
- Medical expenses
- Emergency medical evacuation
- Trip cancellation
- Trip curtailment
- Baggage loss/delay
- Travel delay
- Personal accident
- Personal liability

For EACH benefit, extract:
1. Benefit name
2. Coverage limit (maximum amount in SGD)
3. Sub-limits (if any, like dental, optical for medical)
4. Exact policy text (citation)

Format as JSON:
{{
    "benefits": [
        {{
            "benefit_name": "Medical Expenses",
            "benefit_code": "MED001",
            "coverage_limit": 500000,
            "currency": "SGD",
            "sub_limits": {{
                "dental": 500,
                "optical": 300
            }},
            "citation": "<exact text from policy>"
        }},
        ...
    ]
}}

Policy Text:
{policy_text[:8000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyst. Extract benefits and limits accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            parsed = json.loads(result.strip())
            logger.info("layer_2_mapped", policy=policy_name, benefits=len(parsed.get("benefits", [])))
            return parsed
            
        except Exception as e:
            logger.error("layer_2_mapping_failed", policy=policy_name, error=str(e))
            raise
    
    def _map_layer_3_benefit_conditions(
        self,
        policy_text: str,
        policy_name: str
    ) -> Dict[str, Any]:
        """Extract Layer 3: Benefit-specific conditions and exclusions"""
        
        prompt = f"""You are an insurance policy analyst. For each benefit in the policy, extract CONDITIONS and EXCLUSIONS.

Policy: {policy_name}

For each benefit, extract:
1. Eligibility conditions (who can claim)
2. Waiting periods (days before coverage starts)
3. Documentation required (receipts, medical reports, etc.)
4. Benefit-specific exclusions (what's NOT covered under this benefit)

Format as JSON:
{{
    "benefit_conditions": [
        {{
            "benefit_name": "Medical Expenses",
            "eligibility_conditions": "<conditions>",
            "waiting_period_days": 0,
            "documentation_required": ["medical receipts", "doctor report"],
            "exclusions": "<specific exclusions for this benefit>",
            "citation": "<exact text>"
        }},
        ...
    ]
}}

Policy Text:
{policy_text[:8000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyst. Extract benefit conditions accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            parsed = json.loads(result.strip())
            logger.info("layer_3_mapped", policy=policy_name)
            return parsed
            
        except Exception as e:
            logger.error("layer_3_mapping_failed", policy=policy_name, error=str(e))
            raise
    
    def _map_layer_4_operational(
        self,
        policy_text: str,
        policy_name: str
    ) -> Dict[str, Any]:
        """Extract Layer 4: Operational details"""
        
        prompt = f"""You are an insurance policy analyst. Extract OPERATIONAL details from this policy.

Policy: {policy_name}

Extract:
1. Deductibles/excess (amount insured must pay first)
2. Co-pay percentage (% of claim insured pays)
3. Claim submission methods (online, email, post)
4. Required documents for claims
5. Time limits for claim submission (days after incident)
6. Provider networks (if any)
7. Emergency hotline
8. Claims email
9. Claims portal URL

Format as JSON:
{{
    "deductible_amount": <number>,
    "deductible_currency": "SGD",
    "copay_percentage": <number>,
    "claim_submission_methods": ["online", "email"],
    "claim_documents_required": ["passport copy", "receipts", ...],
    "claim_time_limit_days": <number>,
    "has_provider_network": <boolean>,
    "provider_network_details": "<details>",
    "emergency_hotline": "<phone>",
    "claims_email": "<email>",
    "claims_portal_url": "<url>",
    "citation": "<exact text>"
}}

Policy Text:
{policy_text[:8000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyst. Extract operational details accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            parsed = json.loads(result.strip())
            logger.info("layer_4_mapped", policy=policy_name)
            return parsed
            
        except Exception as e:
            logger.error("layer_4_mapping_failed", policy=policy_name, error=str(e))
            raise

