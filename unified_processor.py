"""
Unified Document Processor
Bridges PDF extraction, OCR, and FHIR conversion
"""

from pathlib import Path
import json
from typing import Dict, Optional
import logging

# Import existing modules
from docling_ocr import DoclingOCR
from test_extraction import extract_pdf_text as extract_text_from_pdf
from run_with_mcp import process_clinical_text_to_fhir
from mcp_validator import validate_fhir_bundle

logger = logging.getLogger(__name__)


class UnifiedProcessor:
    """
    Unified processor for both PDF and Image inputs
    """
    
    def __init__(self):
        self.ocr = DoclingOCR()
    
    def process_pdf_to_fhir(self, pdf_path: str, patient_id: Optional[str] = None) -> Dict:
        """
        Complete PDF → FHIR pipeline
        
        Args:
            pdf_path: Path to PDF file
            patient_id: Optional patient identifier
            
        Returns:
            Dictionary with FHIR resources and metadata
        """
        try:
            pdf_path = Path(pdf_path)
            
            if patient_id is None:
                patient_id = f"PDF-{pdf_path.stem}"
            
            # Step 1: Extract text from PDF
            logger.info(f"Extracting text from: {pdf_path.name}")
            extracted_text = extract_text_from_pdf(str(pdf_path))
            
            if not extracted_text or len(extracted_text) < 10:
                return {
                    'success': False,
                    'stage': 'text_extraction',
                    'error': 'No text extracted from PDF'
                }
            
            # Step 2: Convert to FHIR
            logger.info("Converting to FHIR format")
            fhir_resources = process_clinical_text_to_fhir(
                clinical_text=extracted_text,
                patient_id=patient_id
            )
            
            # Step 3: Validate FHIR
            logger.info("Validating FHIR bundle")
            is_valid = validate_fhir_bundle(fhir_resources)
            
            return {
                'success': True,
                'type': 'pdf_to_fhir',
                'extracted_text': extracted_text,
                'fhir_resources': fhir_resources,
                'is_valid': is_valid,
                'text_length': len(extracted_text),
                'resource_count': len(fhir_resources.get('entry', [])),
                'patient_id': patient_id
            }
        
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                'success': False,
                'stage': 'processing',
                'error': str(e)
            }
    
    def process_image_to_text(
        self, 
        image_path: str, 
        enhance: bool = True
    ) -> Dict:
        """
        Complete Image → Text pipeline (OCR only)
        
        Args:
            image_path: Path to image file
            enhance: Whether to enhance image before OCR
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            image_path = Path(image_path)
            
            # OCR extraction
            logger.info(f"Processing image: {image_path.name}")
            result = self.ocr.process_image(str(image_path), enhance=enhance)
            
            if not result['success']:
                return result
            
            return {
                'success': True,
                'type': 'image_to_text',
                'extracted_text': result['extracted_text'],
                'confidence': result['metadata']['confidence_score'],
                'quality': result['metadata']['quality'],
                'word_count': result['metadata']['word_count'],
                'image_size': result['metadata']['image_size'],
                'warnings': result.get('warnings', [])
            }
        
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                'success': False,
                'stage': 'ocr',
                'error': str(e)
            }
    
    def process_image_to_fhir(
        self,
        image_path: str,
        enhance: bool = True,
        patient_id: Optional[str] = None
    ) -> Dict:
        """
        Complete Image → OCR → FHIR pipeline
        
        Args:
            image_path: Path to image file
            enhance: Whether to enhance image
            patient_id: Optional patient identifier
            
        Returns:
            Dictionary with FHIR resources and metadata
        """
        try:
            image_path = Path(image_path)
            
            if patient_id is None:
                patient_id = f"IMG-{image_path.stem}"
            
            # Step 1: OCR
            ocr_result = self.process_image_to_text(str(image_path), enhance)
            
            if not ocr_result['success']:
                return ocr_result
            
            extracted_text = ocr_result['extracted_text']
            confidence = ocr_result['confidence']
            
            # Check if confidence is sufficient for FHIR conversion
            if confidence < 0.50:
                return {
                    'success': False,
                    'stage': 'ocr_quality',
                    'error': f'OCR confidence too low: {confidence:.1%}',
                    'extracted_text': extracted_text,
                    'confidence': confidence,
                    'recommendation': 'Manual review required before FHIR conversion'
                }
            
            # Step 2: Convert to FHIR
            logger.info("Converting OCR text to FHIR")
            fhir_resources = process_clinical_text_to_fhir(
                clinical_text=extracted_text,
                patient_id=patient_id
            )
            
            # Step 3: Validate
            is_valid = validate_fhir_bundle(fhir_resources)
            
            return {
                'success': True,
                'type': 'image_to_fhir',
                'extracted_text': extracted_text,
                'ocr_confidence': confidence,
                'ocr_quality': ocr_result['quality'],
                'fhir_resources': fhir_resources,
                'is_valid': is_valid,
                'word_count': ocr_result['word_count'],
                'resource_count': len(fhir_resources.get('entry', [])),
                'patient_id': patient_id
            }
        
        except Exception as e:
            logger.error(f"Image to FHIR failed: {e}")
            return {
                'success': False,
                'stage': 'processing',
                'error': str(e)
            }
    
    def auto_process(
        self,
        file_path: str,
        mode: str = 'auto',
        enhance: bool = True,
        patient_id: Optional[str] = None
    ) -> Dict:
        """
        Automatically detect file type and process accordingly
        
        Args:
            file_path: Path to file
            mode: 'auto', 'pdf_to_fhir', 'image_to_text', 'image_to_fhir'
            enhance: Whether to enhance images
            patient_id: Optional patient identifier
            
        Returns:
            Processing result dictionary
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        # Auto-detect if mode is auto
        if mode == 'auto':
            if file_path.suffix.lower() == '.pdf':
                mode = 'pdf_to_fhir'
            else:
                mode = 'image_to_text'
        
        # Route to appropriate processor
        if mode == 'pdf_to_fhir':
            return self.process_pdf_to_fhir(str(file_path), patient_id)
        
        elif mode == 'image_to_text':
            return self.process_image_to_text(str(file_path), enhance)
        
        elif mode == 'image_to_fhir':
            return self.process_image_to_fhir(str(file_path), enhance, patient_id)
        
        else:
            return {
                'success': False,
                'error': f'Unknown mode: {mode}'
            }


# Convenience function
def process_document(file_path: str, **kwargs) -> Dict:
    """Quick processing function"""
    processor = UnifiedProcessor()
    return processor.auto_process(file_path, **kwargs)
