"""
TravelMate AI - PDF Text Extraction
Extract text from policy PDF documents using pdfplumber
"""

import pdfplumber
from pathlib import Path
from typing import Dict, List
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Extract text from PDF policy documents"""
    
    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        """
        Extract all text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            logger.info("extracting_pdf", file=str(pdf_path))
            
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {page_num} ---\n{text}")
            
            full_text = "\n\n".join(text_content)
            
            logger.info(
                "pdf_extracted",
                file=str(pdf_path),
                pages=len(pdf.pages),
                chars=len(full_text)
            )
            
            return full_text
            
        except Exception as e:
            logger.error("pdf_extraction_failed", file=str(pdf_path), error=str(e))
            raise
    
    @staticmethod
    def extract_tables(pdf_path: Path) -> List[List[List[str]]]:
        """
        Extract tables from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of tables (each table is a list of rows)
        """
        try:
            logger.info("extracting_tables", file=str(pdf_path))
            
            all_tables = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            all_tables.append(table)
            
            logger.info(
                "tables_extracted",
                file=str(pdf_path),
                table_count=len(all_tables)
            )
            
            return all_tables
            
        except Exception as e:
            logger.error("table_extraction_failed", file=str(pdf_path), error=str(e))
            raise
    
    @staticmethod
    def extract_sections(text: str, section_markers: List[str]) -> Dict[str, str]:
        """
        Split text into sections based on markers
        
        Args:
            text: Full PDF text
            section_markers: List of section header patterns
            
        Returns:
            Dictionary mapping section names to text content
        """
        sections = {}
        current_section = "preamble"
        current_content = []
        
        for line in text.split('\n'):
            # Check if line matches any section marker
            matched = False
            for marker in section_markers:
                if marker.lower() in line.lower():
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = marker
                    current_content = [line]
                    matched = True
                    break
            
            if not matched:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections

