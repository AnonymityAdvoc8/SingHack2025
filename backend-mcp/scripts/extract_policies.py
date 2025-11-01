"""
TravelMate AI - Policy Extraction Script (PHASE 1)
Extract all 3 policy PDFs and map to 4-layer taxonomy

This script:
1. Reads 3 policy PDFs from assets/Policy_Wordings/
2. Extracts text using pdfplumber
3. Maps to 4-layer taxonomy using Groq LLM
4. Stores in SQLite database with dual-access pattern (normalized + raw text)

Policies:
- Scootsurance QSR022206_updated.pdf
- TravelEasy Policy QTD032212.pdf
- TravelEasy Pre-Ex Policy QTD032212-PX.pdf
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.models.policy import Policy, GeneralCondition, Benefit, OperationalDetail
from app.config import get_settings
from app.utils.pdf_extractor import PDFExtractor
from app.utils.taxonomy_mapper import TaxonomyMapper
from app.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# Policy definitions
POLICIES = [
    {
        "policy_id": "scootsurance_qsr022206",
        "policy_name": "Scootsurance",
        "filename": "Scootsurance QSR022206_updated.pdf",
        "product_type": "Scootsurance"
    },
    {
        "policy_id": "traveleasy_qtd032212",
        "policy_name": "TravelEasy Standard",
        "filename": "TravelEasy Policy QTD032212.pdf",
        "product_type": "TravelEasy"
    },
    {
        "policy_id": "traveleasy_preex_qtd032212px",
        "policy_name": "TravelEasy Pre-Existing",
        "filename": "TravelEasy Pre-Ex Policy QTD032212-PX.pdf",
        "product_type": "TravelEasy Pre-Ex"
    }
]


def extract_policy_text(filename: str) -> str:
    """Extract text from policy PDF"""
    pdf_path = settings.policy_wordings_dir / filename
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"Policy PDF not found: {pdf_path}")
    
    extractor = PDFExtractor()
    return extractor.extract_text(pdf_path)


def map_to_taxonomy(policy_text: str, policy_name: str) -> Dict[str, Any]:
    """Map policy text to 4-layer taxonomy"""
    mapper = TaxonomyMapper()
    return mapper.map_policy_to_taxonomy(policy_text, policy_name, layer="all")


def store_policy_in_db(
    db: SessionLocal,
    policy_def: Dict[str, Any],
    policy_text: str,
    taxonomy_data: Dict[str, Any]
):
    """Store policy data in database with dual-access pattern"""
    
    logger.info("storing_policy", policy_id=policy_def["policy_id"])
    
    # Create main policy record
    policy = Policy(
        policy_id=policy_def["policy_id"],
        policy_name=policy_def["policy_name"],
        product_type=policy_def["product_type"],
        version="1.0",
        original_text=policy_text  # Store raw text for citations
    )
    db.add(policy)
    db.flush()  # Get policy.id
    
    # Layer 1: General Conditions
    layer_1 = taxonomy_data.get("layer_1_general_conditions", {})
    if layer_1:
        general_condition = GeneralCondition(
            policy_id=policy.id,
            age_min=layer_1.get("age_min"),
            age_max=layer_1.get("age_max"),
            residency_required=layer_1.get("residency_required", True),
            residency_countries=layer_1.get("residency_countries", []),
            trip_start_location=layer_1.get("trip_start_location"),
            trip_duration_min_days=layer_1.get("trip_duration_min_days"),
            trip_duration_max_days=layer_1.get("trip_duration_max_days"),
            pre_existing_covered=layer_1.get("pre_existing_covered", False),
            pre_existing_conditions=layer_1.get("pre_existing_conditions", ""),
            high_risk_activities_excluded=layer_1.get("high_risk_activities_excluded", []),
            destination_restrictions=layer_1.get("destination_restrictions", []),
            original_text_section=layer_1.get("age_citation", "") + "\n" + layer_1.get("residency_citation", "")
        )
        db.add(general_condition)
    
    # Layer 2 & 3: Benefits
    layer_2 = taxonomy_data.get("layer_2_benefits_structure", {})
    layer_3 = taxonomy_data.get("layer_3_benefit_conditions", {})
    
    benefits_list = layer_2.get("benefits", [])
    conditions_list = layer_3.get("benefit_conditions", [])
    
    # Create a mapping of benefit names to conditions
    conditions_map = {bc["benefit_name"]: bc for bc in conditions_list}
    
    for benefit_data in benefits_list:
        benefit_name = benefit_data.get("benefit_name")
        conditions = conditions_map.get(benefit_name, {})
        
        benefit = Benefit(
            policy_id=policy.id,
            benefit_name=benefit_name,
            benefit_code=benefit_data.get("benefit_code", ""),
            benefit_category=benefit_data.get("benefit_category", ""),
            coverage_limit=benefit_data.get("coverage_limit"),
            currency=benefit_data.get("currency", "SGD"),
            sub_limits=benefit_data.get("sub_limits", {}),
            eligibility_conditions=conditions.get("eligibility_conditions", ""),
            waiting_period_days=conditions.get("waiting_period_days", 0),
            documentation_required=conditions.get("documentation_required", []),
            benefit_specific_exclusions=conditions.get("exclusions", ""),
            original_text_section=benefit_data.get("citation", "")
        )
        db.add(benefit)
    
    # Layer 4: Operational Details
    layer_4 = taxonomy_data.get("layer_4_operational", {})
    if layer_4:
        operational = OperationalDetail(
            policy_id=policy.id,
            deductible_amount=layer_4.get("deductible_amount", 0),
            deductible_currency=layer_4.get("deductible_currency", "SGD"),
            copay_percentage=layer_4.get("copay_percentage", 0),
            claim_submission_method=layer_4.get("claim_submission_methods", []),
            claim_documents_required=layer_4.get("claim_documents_required", []),
            claim_time_limit_days=layer_4.get("claim_time_limit_days"),
            has_provider_network=layer_4.get("has_provider_network", False),
            provider_network_details=layer_4.get("provider_network_details", ""),
            emergency_hotline=layer_4.get("emergency_hotline", ""),
            claims_email=layer_4.get("claims_email", ""),
            claims_portal_url=layer_4.get("claims_portal_url", ""),
            original_text_section=layer_4.get("citation", "")
        )
        db.add(operational)
    
    db.commit()
    logger.info("policy_stored", policy_id=policy_def["policy_id"])


def main():
    """Main extraction script"""
    print("=" * 80)
    print("🚀 TravelMate AI - Phase 1: Policy Extraction")
    print("=" * 80)
    print()
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    print("✅ Database ready")
    print()
    
    db = SessionLocal()
    
    try:
        for i, policy_def in enumerate(POLICIES, 1):
            print(f"\n{'=' * 80}")
            print(f"📄 Processing Policy {i}/3: {policy_def['policy_name']}")
            print(f"{'=' * 80}")
            
            # Step 1: Extract text
            print(f"📖 Step 1/3: Extracting text from PDF...")
            policy_text = extract_policy_text(policy_def["filename"])
            print(f"✅ Extracted {len(policy_text):,} characters")
            
            # Step 2: Map to taxonomy
            print(f"🧠 Step 2/3: Mapping to 4-layer taxonomy using Groq LLM...")
            print(f"   (This may take 1-2 minutes per layer...)")
            taxonomy_data = map_to_taxonomy(policy_text, policy_def["policy_name"])
            print(f"✅ Taxonomy mapping complete")
            
            # Step 3: Store in database
            print(f"💾 Step 3/3: Storing in database...")
            store_policy_in_db(db, policy_def, policy_text, taxonomy_data)
            print(f"✅ Policy stored: {policy_def['policy_id']}")
            
        print("\n" + "=" * 80)
        print("🎉 Phase 1 Complete!")
        print("=" * 80)
        print()
        print("✅ All 3 policies extracted and mapped to 4-layer taxonomy")
        print("✅ Dual-access pattern: Normalized data + raw text citations")
        print("✅ Data stored in SQLite database: travelmate.db")
        print()
        
        # Show summary
        policies = db.query(Policy).all()
        print(f"📊 Summary:")
        print(f"   Total policies: {len(policies)}")
        for policy in policies:
            print(f"   - {policy.policy_name} ({policy.policy_id})")
            benefit_count = len(policy.benefits)
            print(f"     └─ Benefits: {benefit_count}")
        
    except Exception as e:
        logger.error("extraction_failed", error=str(e))
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

