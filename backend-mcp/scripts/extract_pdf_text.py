"""
PDF Text Extractor for Travel Insurance Policies
Extracts text from PDF policy documents using pypdf
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    from pypdf import PdfReader


class PDFTextExtractor:
    """Extract text from PDF policy documents"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF extractor
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    def extract_text(self, max_pages: Optional[int] = None) -> str:
        """
        Extract text from PDF
        
        Args:
            max_pages: Maximum number of pages to extract (None for all)
            
        Returns:
            Extracted text as string
        """
        try:
            reader = PdfReader(str(self.pdf_path))
            total_pages = len(reader.pages)
            pages_to_extract = min(max_pages, total_pages) if max_pages else total_pages
            
            text_parts = []
            
            for page_num in range(pages_to_extract):
                page = reader.pages[page_num]
                text = page.extract_text()
                text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            
            print(f"✓ Extracted {len(full_text)} characters from {pages_to_extract} pages")
            print(f"  File: {self.pdf_path.name}")
            
            return full_text
            
        except Exception as e:
            print(f"✗ Failed to extract from {self.pdf_path.name}: {e}")
            raise
    
    def extract_to_file(self, output_path: str, max_pages: Optional[int] = None) -> None:
        """
        Extract text and save to file
        
        Args:
            output_path: Where to save extracted text
            max_pages: Maximum number of pages to extract
        """
        text = self.extract_text(max_pages=max_pages)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"✓ Saved to: {output_path}")


def extract_all_policies(policy_dir: str, output_dir: str) -> dict[str, str]:
    """
    Extract text from all policy PDFs in a directory
    
    Args:
        policy_dir: Directory containing policy PDFs
        output_dir: Directory to save extracted text files
        
    Returns:
        Dictionary mapping policy name to extracted text
    """
    policy_path = Path(policy_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    policies = {}
    pdf_files = list(policy_path.glob("*.pdf"))
    
    print(f"\n{'='*60}")
    print(f"Extracting text from {len(pdf_files)} PDF files")
    print(f"{'='*60}\n")
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        
        try:
            extractor = PDFTextExtractor(str(pdf_file))
            text = extractor.extract_text()
            
            # Save to output file
            output_file = output_path / f"{pdf_file.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            policies[pdf_file.stem] = text
            print(f"✓ Saved to: {output_file}\n")
            
        except Exception as e:
            print(f"✗ Error processing {pdf_file.name}: {e}\n")
            continue
    
    print(f"{'='*60}")
    print(f"Extraction complete: {len(policies)}/{len(pdf_files)} successful")
    print(f"{'='*60}\n")
    
    return policies


if __name__ == "__main__":
    # Example usage
    import os
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Define paths
    policy_dir = project_root / "assets" / "Policy_Wordings"
    output_dir = project_root / "backend-mcp" / "extracted_policies"
    
    print(f"Policy directory: {policy_dir}")
    print(f"Output directory: {output_dir}")
    
    if not policy_dir.exists():
        print(f"Error: Policy directory not found: {policy_dir}")
        sys.exit(1)
    
    # Extract all policies
    policies = extract_all_policies(str(policy_dir), str(output_dir))
    
    print(f"\nExtracted policies:")
    for name, text in policies.items():
        print(f"  - {name}: {len(text):,} characters")

