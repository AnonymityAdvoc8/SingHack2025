"""
TravelMate AI - Taxonomy Mapper
Map policy text to 3-layer taxonomy using Groq LLM
Aligned with Taxonomy_Hackathon.json structure
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from groq import Groq
from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TaxonomyMapper:
    """Map policy documents to standardized 3-layer taxonomy"""
    
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
    
    def _safe_json_parse(self, json_str: str) -> Any:
        """
        Safely parse JSON with error handling and cleaning
        Attempts multiple strategies to fix common JSON issues
        """
        # Strategy 1: Direct parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning("json_parse_failed_attempting_fix", error=str(e))
        
        # Strategy 2: Try to fix common issues
        try:
            # Remove any trailing commas before ] or }
            import re
            cleaned = re.sub(r',(\s*[}\]])', r'\1', json_str)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Use ast.literal_eval as fallback for simple cases
        try:
            import ast
            return ast.literal_eval(json_str)
        except:
            pass
        
        # Strategy 4: Last resort - return empty structure
        logger.error("json_parse_all_strategies_failed", preview=json_str[:200])
        raise ValueError(f"Unable to parse JSON after multiple attempts. First 200 chars: {json_str[:200]}")
    
    def map_policy_to_taxonomy(
        self,
        policy_text: str,
        product_key: str  # "Product A", "Product B", or "Product C"
    ) -> Dict[str, Any]:
        """
        Map policy text to 3-layer taxonomy structure using LLM
        
        Args:
            policy_text: Raw policy text from PDF
            product_key: Product identifier ("Product A", "Product B", "Product C")
            
        Returns:
            Mapped taxonomy data for the product
        """
        logger.info("mapping_policy_to_taxonomy", product=product_key)
        
        # Extract all layers
        layer_1 = self._map_layer_1_general_conditions(policy_text, product_key)
        layer_2 = self._map_layer_2_benefits(policy_text, product_key)
        layer_3 = self._map_layer_3_benefit_conditions(policy_text, product_key)
        
        return {
            "product_key": product_key,
            "layer_1_general_conditions": layer_1,
            "layer_2_benefits": layer_2,
            "layer_3_benefit_specific_conditions": layer_3
        }
    
    def _map_layer_1_general_conditions(
        self,
        policy_text: str,
        product_key: str
    ) -> List[Dict[str, Any]]:
        """
        Extract Layer 1: General Conditions
        Returns a list of conditions matching taxonomy structure
        """
        
        # Get the list of Layer 1 conditions from template
        template_conditions = self.taxonomy_template.get("layers", {}).get("layer_1_general_conditions", [])
        condition_names = [c["condition"] for c in template_conditions]
        
        prompt = f"""You are an expert travel insurance policy analyst. Extract Layer 1 General Conditions from this policy.

IMPORTANT: For each condition below, determine:
1. Does this condition exist in the policy? (true/false)
2. The exact text from the policy (if it exists)
3. Specific parameters (ages, days, amounts, etc.)

CONDITIONS TO EXTRACT:
{json.dumps(condition_names, indent=2)}

For EACH condition, provide:
- condition_exist: true or false
- original_text: the exact quoted text from policy (or empty string if doesn't exist)
- parameters: specific values like {{"min_age": 18, "max_age": 70}}, {{"days": 90}}, {{"activities": ["skiing", "diving"]}}, etc.

Format as JSON array:
[
    {{
        "condition": "trip_start_singapore",
        "condition_exist": true,
        "original_text": "Coverage begins when you depart from Singapore...",
        "parameters": {{"departure_location": "Singapore"}}
    }},
    {{
        "condition": "age_eligibility",
        "condition_exist": true,
        "original_text": "You must be between 18 and 70 years old...",
        "parameters": {{"min_age": 18, "max_age": 70, "unit": "years"}}
    }},
    ...
]

Policy Text (first 12000 chars):
{policy_text[:12000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyst. Extract data accurately with exact citations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            # Clean and parse JSON
            parsed = self._safe_json_parse(result.strip())
            logger.info("layer_1_mapped", product=product_key, conditions_found=len(parsed))
            return parsed
            
        except Exception as e:
            logger.error("layer_1_mapping_failed", product=product_key, error=str(e))
            raise
    
    def _map_layer_2_benefits(
        self,
        policy_text: str,
        product_key: str
    ) -> List[Dict[str, Any]]:
        """
        Extract Layer 2: Benefits
        Returns a list of benefits with their existence and parameters
        """
        
        # Get the list of Layer 2 benefits from template
        template_benefits = self.taxonomy_template.get("layers", {}).get("layer_2_benefits", [])
        benefit_names = [b["benefit_name"] for b in template_benefits]
        
        prompt = f"""You are an expert travel insurance policy analyst. Extract Layer 2 Benefits from this policy.

IMPORTANT: For each benefit below, determine:
1. Does this benefit exist in the policy? (true/false)
2. Coverage limits and parameters (amounts in SGD, sub-limits, etc.)

BENEFITS TO CHECK:
{json.dumps(benefit_names, indent=2)}

For EACH benefit, provide:
- benefit_name: exact name from list above
- condition_exist: true or false
- parameters: coverage limits and details like:
  {{"coverage_limit": 500000, "currency": "SGD", "sub_limits": {{"dental": 500}}}}

Format as JSON array:
[
    {{
        "benefit_name": "overseas_medical_expenses",
        "condition_exist": true,
        "parameters": {{
            "coverage_limit": 1000000,
            "currency": "SGD",
            "sub_limits": {{"dental": 1000, "optical": 500}}
        }}
    }},
    {{
        "benefit_name": "trip_cancellation",
        "condition_exist": true,
        "parameters": {{
            "coverage_limit": 10000,
            "currency": "SGD"
        }}
    }},
    ...
]

Policy Text (first 12000 chars):
{policy_text[:12000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyst. Extract benefit data accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            parsed = self._safe_json_parse(result.strip())
            logger.info("layer_2_mapped", product=product_key, benefits_found=len(parsed))
            return parsed
            
        except Exception as e:
            logger.error("layer_2_mapping_failed", product=product_key, error=str(e))
            raise
    
    def _map_layer_3_benefit_conditions(
        self,
        policy_text: str,
        product_key: str
    ) -> List[Dict[str, Any]]:
        """
        Extract Layer 3: Benefit-Specific Conditions
        Returns a list of conditions tied to specific benefits
        Process in batches to avoid JSON parsing issues
        """
        
        # Get the list of Layer 3 conditions from template
        template_conditions = self.taxonomy_template.get("layers", {}).get("layer_3_benefit_specific_conditions", [])
        
        # Group by benefit for better extraction
        conditions_by_benefit = {}
        for cond in template_conditions:
            benefit = cond.get("benefit_name")
            if benefit not in conditions_by_benefit:
                conditions_by_benefit[benefit] = []
            conditions_by_benefit[benefit].append(cond["condition"])
        
        all_results = []
        benefit_names = list(conditions_by_benefit.keys())
        
        # Process top 20 most important benefits (to avoid massive JSON)
        # Focus on common benefits that are likely in all policies
        priority_benefits = [
            "overseas_medical_expenses",
            "trip_cancellation",
            "trip_curtailment",
            "travel_delay",
            "delayed_baggage",
            "loss_damage_personal_belongings",
            "personal_liability",
            "emergency_medical_evacuation_repatriation",
            "accidental_death_permanent_disablement",
            "trip_disruption"
        ]
        
        # Add remaining benefits
        for benefit in benefit_names:
            if benefit not in priority_benefits:
                priority_benefits.append(benefit)
        
        # Take top 20
        benefits_to_process = priority_benefits[:20]
        
        # Create a focused conditions dict
        focused_conditions = {b: conditions_by_benefit[b] for b in benefits_to_process if b in conditions_by_benefit}
        
        prompt = f"""You are an expert travel insurance policy analyst. Extract Layer 3 Benefit-Specific Conditions.

CRITICAL: Return ONLY valid JSON. Escape all quotes in text strings using backslash.

For the benefits below, check if their conditions exist in the policy:

CONDITIONS TO CHECK:
{json.dumps(focused_conditions, indent=2)[:3000]}

Return a JSON array. For EACH condition:
- benefit_name: benefit it applies to
- condition: condition name  
- condition_exist: true or false
- original_text: short excerpt (MAX 100 chars, escape quotes!)
- parameters: extracted values

EXAMPLE:
[
  {{
    "benefit_name": "overseas_medical_expenses",
    "condition": "medical_expenses_incurred_within_time_limit",
    "condition_exist": true,
    "original_text": "Claims within 90 days",
    "parameters": {{"days": 90}}
  }}
]

Policy Text (first 10000 chars):
{policy_text[:10000]}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance analyst. Return ONLY valid JSON with escaped quotes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8000
            )
            
            result = response.choices[0].message.content
            
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            parsed = self._safe_json_parse(result.strip())
            logger.info("layer_3_mapped", product=product_key, conditions_found=len(parsed))
            
            # Return the parsed results
            return parsed if isinstance(parsed, list) else []
            
        except Exception as e:
            logger.error("layer_3_mapping_failed", product=product_key, error=str(e))
            # Return empty list instead of crashing - Layer 3 is nice-to-have
            logger.warning("layer_3_returning_empty", product=product_key)
            return []

