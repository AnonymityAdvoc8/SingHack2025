"""
Populate Taxonomy JSON from Policy PDFs
Main script to extract policy data and populate Taxonomy_Hackathon.json
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_pdf_text import PDFTextExtractor
from app.utils.taxonomy_mapper import TaxonomyMapper
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaxonomyPopulator:
    """Populate taxonomy JSON with data from policy PDFs"""
    
    def __init__(self, taxonomy_file: str):
        """
        Initialize populator
        
        Args:
            taxonomy_file: Path to Taxonomy_Hackathon.json
        """
        self.taxonomy_file = Path(taxonomy_file)
        self.taxonomy_data = self._load_taxonomy()
        self.mapper = TaxonomyMapper()
    
    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load the taxonomy template"""
        with open(self.taxonomy_file, 'r') as f:
            return json.load(f)
    
    def _save_taxonomy(self) -> None:
        """Save the populated taxonomy"""
        with open(self.taxonomy_file, 'w') as f:
            json.dump(self.taxonomy_data, f, indent=2)
        print(f"✓ Saved taxonomy to: {self.taxonomy_file}")
    
    def populate_from_policy(
        self,
        policy_pdf: str,
        product_key: str
    ) -> None:
        """
        Populate taxonomy data for one product from its policy PDF
        
        Args:
            policy_pdf: Path to policy PDF file
            product_key: "Product A", "Product B", or "Product C"
        """
        print(f"\n{'='*70}")
        print(f"PROCESSING: {product_key}")
        print(f"PDF: {Path(policy_pdf).name}")
        print(f"{'='*70}\n")
        
        # Extract text from PDF
        print("Step 1: Extracting text from PDF...")
        extractor = PDFTextExtractor(policy_pdf)
        policy_text = extractor.extract_text(max_pages=50)  # Limit to first 50 pages
        print(f"✓ Extracted {len(policy_text):,} characters\n")
        
        # Map to taxonomy using LLM
        print("Step 2: Mapping policy to taxonomy using AI...")
        mapped_data = self.mapper.map_policy_to_taxonomy(policy_text, product_key)
        
        # Populate Layer 1: General Conditions
        print("\nStep 3: Populating Layer 1 (General Conditions)...")
        self._populate_layer_1(mapped_data["layer_1_general_conditions"], product_key)
        
        # Populate Layer 2: Benefits
        print("Step 4: Populating Layer 2 (Benefits)...")
        self._populate_layer_2(mapped_data["layer_2_benefits"], product_key)
        
        # Populate Layer 3: Benefit-Specific Conditions
        print("Step 5: Populating Layer 3 (Benefit-Specific Conditions)...")
        self._populate_layer_3(mapped_data["layer_3_benefit_specific_conditions"], product_key)
        
        print(f"\n✓ Completed mapping for {product_key}")
    
    def _populate_layer_1(self, conditions: List[Dict], product_key: str) -> None:
        """Populate Layer 1 general conditions"""
        layer_1 = self.taxonomy_data["layers"]["layer_1_general_conditions"]
        
        populated_count = 0
        for extracted_condition in conditions:
            condition_name = extracted_condition["condition"]
            
            # Find matching condition in taxonomy
            for template_condition in layer_1:
                if template_condition["condition"] == condition_name:
                    # Update the product data
                    template_condition["products"][product_key] = {
                        "condition_exist": extracted_condition["condition_exist"],
                        "original_text": extracted_condition.get("original_text", ""),
                        "parameters": extracted_condition.get("parameters", {})
                    }
                    
                    if extracted_condition["condition_exist"]:
                        populated_count += 1
                    break
        
        print(f"  ✓ Populated {populated_count} conditions for {product_key}")
    
    def _populate_layer_2(self, benefits: List[Dict], product_key: str) -> None:
        """Populate Layer 2 benefits"""
        layer_2 = self.taxonomy_data["layers"]["layer_2_benefits"]
        
        populated_count = 0
        for extracted_benefit in benefits:
            benefit_name = extracted_benefit["benefit_name"]
            
            # Find matching benefit in taxonomy
            for template_benefit in layer_2:
                if template_benefit["benefit_name"] == benefit_name:
                    # Update the product data
                    template_benefit["products"][product_key] = {
                        "condition_exist": extracted_benefit["condition_exist"],
                        "parameters": extracted_benefit.get("parameters", {})
                    }
                    
                    if extracted_benefit["condition_exist"]:
                        populated_count += 1
                    break
        
        print(f"  ✓ Populated {populated_count} benefits for {product_key}")
    
    def _populate_layer_3(self, conditions: List[Dict], product_key: str) -> None:
        """Populate Layer 3 benefit-specific conditions"""
        layer_3 = self.taxonomy_data["layers"]["layer_3_benefit_specific_conditions"]
        
        populated_count = 0
        for extracted_condition in conditions:
            benefit_name = extracted_condition["benefit_name"]
            condition_name = extracted_condition["condition"]
            
            # Find matching condition in taxonomy
            for template_condition in layer_3:
                if (template_condition["benefit_name"] == benefit_name and 
                    template_condition["condition"] == condition_name):
                    
                    # Update the product data
                    if "products" in template_condition:
                        template_condition["products"][product_key] = {
                            "condition_exist": extracted_condition["condition_exist"],
                            "original_text": extracted_condition.get("original_text", ""),
                            "parameters": extracted_condition.get("parameters", {})
                        }
                    
                    if extracted_condition["condition_exist"]:
                        populated_count += 1
                    break
        
        print(f"  ✓ Populated {populated_count} benefit conditions for {product_key}")
    
    def process_all_policies(self, policy_mapping: Dict[str, str]) -> None:
        """
        Process all policy PDFs and populate taxonomy
        
        Args:
            policy_mapping: Dict mapping product_key to PDF path
                           e.g., {"Product A": "/path/to/policy1.pdf", ...}
        """
        print(f"\n{'#'*70}")
        print(f"# TAXONOMY POPULATION - Processing {len(policy_mapping)} Policies")
        print(f"{'#'*70}\n")
        
        start_time = time.time()
        
        for product_key, pdf_path in policy_mapping.items():
            try:
                self.populate_from_policy(pdf_path, product_key)
                # Save after each policy (in case of errors)
                self._save_taxonomy()
                print(f"\n✓ Progress saved for {product_key}\n")
                
            except Exception as e:
                print(f"\n✗ ERROR processing {product_key}: {e}")
                logger.error("policy_processing_failed", product=product_key, error=str(e))
                continue
        
        elapsed = time.time() - start_time
        print(f"\n{'#'*70}")
        print(f"# COMPLETE - All policies processed in {elapsed:.1f} seconds")
        print(f"{'#'*70}\n")


def main():
    """Main execution"""
    # Get project paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Define file paths
    taxonomy_file = project_root / "assets" / "Taxonomy" / "Taxonomy_Hackathon.json"
    policy_dir = project_root / "assets" / "Policy_Wordings"
    
    # Check files exist
    if not taxonomy_file.exists():
        print(f"Error: Taxonomy file not found: {taxonomy_file}")
        sys.exit(1)
    
    if not policy_dir.exists():
        print(f"Error: Policy directory not found: {policy_dir}")
        sys.exit(1)
    
    # Map products to their PDF files
    # You can customize this mapping based on which policy is which product
    policy_mapping = {
        "Product A": str(policy_dir / "Scootsurance.pdf"),
        "Product B": str(policy_dir / "MHInsure_travel.pdf"),
        "Product C": str(policy_dir / "international_travel.pdf"),
    }
    
    print("\n" + "="*70)
    print("TAXONOMY POPULATION CONFIGURATION")
    print("="*70)
    print(f"Taxonomy File: {taxonomy_file}")
    print(f"Policy Directory: {policy_dir}")
    print("\nPolicy Mapping:")
    for product, pdf in policy_mapping.items():
        pdf_name = Path(pdf).name
        exists = "✓" if Path(pdf).exists() else "✗"
        print(f"  {exists} {product}: {pdf_name}")
    print("="*70)
    
    # Check all PDFs exist
    missing_pdfs = [k for k, v in policy_mapping.items() if not Path(v).exists()]
    if missing_pdfs:
        print(f"\nError: Missing PDF files for: {', '.join(missing_pdfs)}")
        sys.exit(1)
    
    # Ask for confirmation
    print("\nThis will populate the taxonomy JSON with data from the policies.")
    print("The process will use AI (Groq API) to extract information.")
    response = input("\nProceed? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    # Create populator and process
    populator = TaxonomyPopulator(str(taxonomy_file))
    populator.process_all_policies(policy_mapping)
    
    print("\n✓ Taxonomy population complete!")
    print(f"✓ Updated file: {taxonomy_file}")


if __name__ == "__main__":
    main()

