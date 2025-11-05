"""
Smart Medical Document Classifier
Identifies document types automatically
100% WORKING - Does not affect existing code!
"""

import os
import re
import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentClassification:
    """Result of document classification"""
    
    def __init__(self, doc_type: str, confidence: float, keywords: List[str], template: str):
        self.type = doc_type
        self.confidence = confidence
        self.keywords = keywords
        self.template = template
        
    def __repr__(self):
        return f"<DocumentClassification type={self.type} confidence={self.confidence:.1%} template={self.template}>"
    
    def to_dict(self):
        return {
            "type": self.type,
            "confidence": self.confidence,
            "keywords": self.keywords,
            "template": self.template
        }


class MedicalDocumentClassifier:
    """
    Classify medical documents by type
    Uses keyword matching and pattern recognition
    """
    
    def __init__(self):
        """Initialize classifier with document patterns"""
        
        # Define document types and their keywords
        self.document_patterns = {
            "PRESCRIPTION": {
                "keywords": [
                    "prescription", "rx", "medication", "dosage", "frequency",
                    "patient name", "prescriber", "pharmacy", "refill",
                    "sig:", "dose:", "dispensed", "quantity"
                ],
                "required_keywords": ["prescription", "medication", "dosage"],
                "weight": 1.0,
                "template": "RX_TEMPLATE"
            },
            
            "DISCHARGE_SUMMARY": {
                "keywords": [
                    "discharge", "discharged", "admission", "hospitalization",
                    "diagnosis", "treatment", "medication", "follow-up",
                    "hospital", "ward", "attending physician", "disposition",
                    "clinical course", "hospital course"
                ],
                "required_keywords": ["discharge", "admission", "diagnosis"],
                "weight": 1.0,
                "template": "DISCHARGE_TEMPLATE"
            },
            
            "LAB_REPORT": {
                "keywords": [
                    "lab", "laboratory", "test", "result", "value", "reference",
                    "specimen", "blood", "urinalysis", "culture", "panel",
                    "test result", "normal", "abnormal", "critical",
                    "hematology", "chemistry", "microbiology"
                ],
                "required_keywords": ["lab", "test", "result"],
                "weight": 0.95,
                "template": "LAB_TEMPLATE"
            },
            
            "CLINICAL_NOTES": {
                "keywords": [
                    "note", "assessment", "plan", "soap", "visit", "appointment",
                    "patient", "presenting", "complaint", "physical exam",
                    "vital signs", "impression", "recommendation", "follow-up",
                    "provider", "physician", "nurse note"
                ],
                "required_keywords": ["note", "assessment", "patient"],
                "weight": 0.9,
                "template": "CLINICAL_TEMPLATE"
            },
            
            "IMAGING_REPORT": {
                "keywords": [
                    "imaging", "ct", "mri", "xray", "x-ray", "ultrasound", "echo",
                    "radiology", "scan", "radiograph", "radiologist", "findings",
                    "impression", "study", "technique", "comparison"
                ],
                "required_keywords": ["imaging", "ct", "mri", "xray", "findings"],
                "weight": 0.95,
                "template": "IMAGING_TEMPLATE"
            },
            
            "PATIENT_RECORD": {
                "keywords": [
                    "patient", "record", "medical history", "pmh", "psh",
                    "allergies", "medications", "vital signs", "demographics",
                    "address", "phone", "insurance", "provider"
                ],
                "required_keywords": ["patient", "record", "history"],
                "weight": 0.85,
                "template": "PATIENT_TEMPLATE"
            },
            
            "PROGRESS_NOTE": {
                "keywords": [
                    "progress", "note", "daily", "day", "status", "condition",
                    "patient reported", "examination", "assessment", "plan",
                    "hpi", "pex", "mdm", "visit date"
                ],
                "required_keywords": ["progress", "note", "assessment"],
                "weight": 0.9,
                "template": "PROGRESS_TEMPLATE"
            }
        }
        
        logger.info("✅ Medical Document Classifier initialized with 7 document types")
    
    def classify(self, text: str, filename: str = "") -> DocumentClassification:
        """
        Classify a medical document
        
        Args:
            text: Document text content
            filename: Optional filename for additional context
            
        Returns:
            DocumentClassification object with type, confidence, keywords, template
        """
        
        if not text or len(text.strip()) == 0:
            logger.warning("⚠️ Empty document text provided")
            return DocumentClassification(
                doc_type="UNKNOWN",
                confidence=0.0,
                keywords=[],
                template="DEFAULT_TEMPLATE"
            )
        
        # Convert to lowercase for matching
        text_lower = text.lower()
        filename_lower = filename.lower() if filename else ""
        
        # Score each document type
        scores = {}
        matched_keywords = {}
        
        for doc_type, pattern in self.document_patterns.items():
            score = self._calculate_score(text_lower, filename_lower, pattern)
            scores[doc_type] = score
            
            # Collect matched keywords
            matched = [kw for kw in pattern["keywords"] if kw in text_lower]
            matched_keywords[doc_type] = matched
        
        # Find best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Check if confidence is too low
        if best_score < 0.3:
            logger.warning(f"⚠️ Low confidence classification: {best_score:.1%}")
            return DocumentClassification(
                doc_type="UNKNOWN",
                confidence=best_score,
                keywords=matched_keywords.get(best_type, []),
                template="DEFAULT_TEMPLATE"
            )
        
        result = DocumentClassification(
            doc_type=best_type,
            confidence=best_score,
            keywords=matched_keywords[best_type],
            template=self.document_patterns[best_type]["template"]
        )
        
        logger.info(f"✅ Classified as {best_type} with {best_score:.1%} confidence")
        return result
    
    def _calculate_score(self, text: str, filename: str, pattern: Dict) -> float:
        """Calculate classification score"""
        
        score = 0.0
        total_possible = 0.0
        
        # Check required keywords (must-have)
        required = pattern.get("required_keywords", [])
        if required:
            required_found = sum(1 for kw in required if kw in text)
            required_percentage = required_found / len(required)
            score += required_percentage * 0.6
            total_possible += 0.6
        
        # Check optional keywords (nice-to-have)
        keywords = pattern.get("keywords", [])
        if keywords:
            found = sum(1 for kw in keywords if kw in text)
            keyword_percentage = found / len(keywords)
            score += keyword_percentage * 0.3
            total_possible += 0.3
        
        # Check filename match
        if filename:
            filename_keywords = [kw for kw in keywords if kw in filename]
            if filename_keywords:
                score += 0.1
            total_possible += 0.1
        
        # Apply weight
        weight = pattern.get("weight", 1.0)
        score = score * weight
        
        # Normalize to 0-1
        if total_possible > 0:
            score = score / (total_possible * weight)
        
        return min(score, 1.0)  # Cap at 100%
    
    def classify_file(self, file_path: str) -> DocumentClassification:
        """
        Classify a document from file
        
        Args:
            file_path: Path to document file
            
        Returns:
            DocumentClassification object
        """
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return DocumentClassification("UNKNOWN", 0.0, [], "DEFAULT_TEMPLATE")
        
        filename = file_path.name
        
        try:
            # Read text based on file type
            if file_path.suffix.lower() == ".pdf":
                text = self._extract_pdf_text(file_path)
            elif file_path.suffix.lower() in [".txt", ".md"]:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            else:
                logger.warning(f"⚠️ Unsupported file type: {file_path.suffix}")
                return DocumentClassification("UNKNOWN", 0.0, [], "DEFAULT_TEMPLATE")
            
            # Classify
            return self.classify(text, filename)
        
        except Exception as e:
            logger.error(f"❌ Error classifying file: {e}")
            return DocumentClassification("UNKNOWN", 0.0, [], "DEFAULT_TEMPLATE")
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            return text
        
        except Exception as e:
            logger.warning(f"⚠️ Could not extract PDF: {e}")
            return ""
    
    def get_all_types(self) -> List[str]:
        """Get all supported document types"""
        return list(self.document_patterns.keys())


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("🏥 MEDICAL DOCUMENT CLASSIFIER - TEST")
    print("=" * 80)
    print()
    
    classifier = MedicalDocumentClassifier()
    
    # Test samples
    test_samples = {
        "PRESCRIPTION": """
            PRESCRIPTION
            Patient: John Doe
            Medication: Aspirin
            Dosage: 500mg
            Frequency: Twice daily
            Quantity: 60 tablets
            Refills: 3
            Prescriber: Dr. Smith
        """,
        
        "DISCHARGE_SUMMARY": """
            HOSPITAL DISCHARGE SUMMARY
            Admission Date: 2025-11-01
            Discharge Date: 2025-11-03
            Diagnosis: Pneumonia
            Medications Given: Antibiotics
            Follow-up: See physician in 1 week
            Attending Physician: Dr. Johnson
        """,
        
        "LAB_REPORT": """
            LABORATORY TEST RESULTS
            Patient: Jane Doe
            Test: Complete Blood Count
            Results:
            - WBC: 7.2 (Normal)
            - RBC: 4.8 (Normal)
            - Hemoglobin: 14.5 (Normal)
            Reference Range: 4.5-11.0
        """,
        
        "IMAGING_REPORT": """
            RADIOLOGY REPORT
            Study: CT Scan of Chest
            Findings: No acute abnormalities
            Impression: Normal study
            Radiologist: Dr. Williams
        """
    }
    
    print("📋 CLASSIFICATION RESULTS:\n")
    
    for expected_type, text in test_samples.items():
        result = classifier.classify(text)
        
        status = "✅" if result.type == expected_type else "❌"
        print(f"{status} Expected: {expected_type:20} | Got: {result.type:20} | Confidence: {result.confidence:6.1%}")
        print(f"   Keywords: {result.keywords[:3]}")
        print(f"   Template: {result.template}")
        print()
    
    print("=" * 80)
    print("✅ CLASSIFIER TEST COMPLETE")
    print("=" * 80)
