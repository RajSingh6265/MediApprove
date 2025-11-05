"""
Production-Grade Docling OCR Module
Extracts text from scanned images and handwritten notes
Supports: JPG, PNG, TIFF, BMP, PDF (scanned)
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Image processing
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  Warning: pytesseract not installed")

# PDF to image
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠️  Warning: pdf2image not installed")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DoclingOCR:
    """
    Production-grade OCR processor using Docling approach
    Handles all image formats with robust error handling
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.pdf'}
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR processor
        
        Args:
            tesseract_cmd: Path to tesseract executable (auto-detect if None)
        """
        self.tesseract_cmd = tesseract_cmd
        self._setup_tesseract()
        
        logger.info("✅ DoclingOCR initialized successfully")
    
    def _setup_tesseract(self):
        """Setup Tesseract OCR engine"""
        if not TESSERACT_AVAILABLE:
            raise RuntimeError(
                "❌ pytesseract not installed. Install with: pip install pytesseract"
            )
        
        # Auto-detect Tesseract installation
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        else:
            # Common Windows paths
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"✅ Found Tesseract at: {path}")
                    break
        
        # Verify Tesseract is working
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract version: {version}")
        except Exception as e:
            raise RuntimeError(
                f"❌ Tesseract not found. Please install from: "
                f"https://github.com/UB-Mannheim/tesseract/wiki\n"
                f"Error: {e}"
            )
    def preprocess_image(self, image: Image.Image) -> Image.Image:
   
        logger.info("   📊 Pre-processing image...")
        
        # ═══════════════════════════════════════════════════════
        # FIX 1: CRITICAL - Upscale small images (304x351 → 1200px+)
        # ═══════════════════════════════════════════════════════
        width, height = image.size
        min_dimension = min(width, height)
        
        if min_dimension < 1200:
            scale_factor = 1200 / min_dimension
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            image = image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS  # Highest quality
            )
            logger.info(f"   📐 Upscaled {width}x{height} → {new_width}x{new_height}")
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to OpenCV
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # ═══════════════════════════════════════════════════════
        # FIX 2: Auto-brightness adjustment (fixes dark images)
        # ═══════════════════════════════════════════════════════
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        mean_brightness = np.mean(gray)
        logger.info(f"   💡 Image brightness: {mean_brightness:.0f}/255")
        
        if mean_brightness < 100:
            # Very dark image - aggressive brightening
            gray = cv2.convertScaleAbs(gray, alpha=1.8, beta=50)
            logger.info(f"   💡 Applied brightness correction (dark image)")
        elif mean_brightness < 130:
            # Somewhat dark - moderate brightening
            gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=20)
            logger.info(f"   💡 Applied brightness correction (moderate)")
        
        # ═══════════════════════════════════════════════════════
        # FIX 3: Gentle noise removal (preserves text details)
        # ═══════════════════════════════════════════════════════
        denoised = cv2.fastNlMeansDenoising(gray, None, 5, 7, 21)
        
        # ═══════════════════════════════════════════════════════
        # FIX 4: CRITICAL - Adaptive thresholding (best for prescriptions)
        # ═══════════════════════════════════════════════════════
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,  # Block size (larger = more context)
            8    # Constant subtracted (tune based on your images)
        )
        
        # ═══════════════════════════════════════════════════════
        # FIX 5: Deskew (auto-rotate)
        # ═══════════════════════════════════════════════════════
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            if abs(angle) > 0.5:
                (h, w) = binary.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                binary = cv2.warpAffine(
                    binary, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                logger.info(f"   🔄 Deskewed by {angle:.1f}°")
        
        # ═══════════════════════════════════════════════════════
        # FIX 6: Morphological operations (clean up noise)
        # ═══════════════════════════════════════════════════════
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Convert back to PIL
        enhanced = Image.fromarray(binary)
        
        # ═══════════════════════════════════════════════════════
        # FIX 7: Final sharpening (gentle)
        # ═══════════════════════════════════════════════════════
        enhanced = enhanced.filter(ImageFilter.SHARPEN)
        
        logger.info("   ✅ Pre-processing complete")
        return enhanced
    
    def extract_text_with_confidence(
        self, 
        image: Image.Image
    ) -> Tuple[str, float, List[Dict]]:
        """
        Extract text with confidence scores
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (full_text, average_confidence, text_blocks)
        """
        logger.info("   🔍 Extracting text with OCR...")
        
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config='--psm 1 --oem 3'  # Auto page segmentation with LSTM
        )
        
        # Process results
        text_blocks = []
        full_text_parts = []
        confidences = []
        
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i])
            
            if text and conf > 0:
                # Add to blocks
                text_blocks.append({
                    'text': text,
                    'confidence': conf / 100.0,
                    'level': ocr_data['level'][i],
                    'line_num': ocr_data['line_num'][i],
                    'word_num': ocr_data['word_num'][i]
                })
                
                full_text_parts.append(text)
                confidences.append(conf)
        
        # Combine text
        full_text = ' '.join(full_text_parts)
        
        # Calculate average confidence
        avg_confidence = (
            sum(confidences) / len(confidences) / 100.0 
            if confidences else 0.0
        )
        
        logger.info(f"   ✅ Extracted {len(full_text_parts)} words (avg confidence: {avg_confidence:.2%})")
        
        return full_text, avg_confidence, text_blocks
    
    def process_image(
        self, 
        image_path: str,
        enhance: bool = True
    ) -> Dict:
        """
        Process a single image file
        
        Args:
            image_path: Path to image file
            enhance: Whether to pre-process image
            
        Returns:
            Dictionary with extracted text and metadata
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"❌ Image not found: {image_path}")
        
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"❌ Unsupported format: {image_path.suffix}\n"
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"📄 Processing: {image_path.name}")
        
        try:
            # Handle PDF separately
            if image_path.suffix.lower() == '.pdf':
                return self._process_pdf(image_path, enhance)
            
            # Load image
            image = Image.open(image_path)
            logger.info(f"   ℹ️  Image size: {image.size}")
            
            # Pre-process if enabled
            if enhance:
                image = self.preprocess_image(image)
            
            # Extract text
            full_text, confidence, text_blocks = self.extract_text_with_confidence(image)
            
            # Determine quality
            if confidence >= 0.85:
                quality = "high"
            elif confidence >= 0.65:
                quality = "medium"
            else:
                quality = "low"
            
            # Build result
            result = {
                'success': True,
                'file_name': image_path.name,
                'file_path': str(image_path.absolute()),
                'file_type': image_path.suffix.lower(),
                'extracted_text': full_text,
                'full_text': full_text,  # Alias for compatibility
                'text_blocks': text_blocks,
                'metadata': {
                    'extraction_method': 'tesseract_ocr',
                    'confidence_score': round(confidence, 3),
                    'quality': quality,
                    'image_size': image.size,
                    'word_count': len(full_text.split()),
                    'block_count': len(text_blocks),
                    'enhanced': enhance,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Add warnings if needed
            if confidence < 0.65:
                result['warnings'] = [
                    f"Low OCR confidence ({confidence:.1%}). Results may be inaccurate.",
                    "Consider using higher quality image or manual review."
                ]
            
            logger.info(f"✅ Successfully processed: {image_path.name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing {image_path.name}: {e}")
            return {
                'success': False,
                'file_name': image_path.name,
                'file_path': str(image_path.absolute()),
                'error': str(e),
                'error_type': type(e).__name__,
                'metadata': {
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def _process_pdf(self, pdf_path: Path, enhance: bool) -> Dict:
        """Process scanned PDF"""
        if not PDF2IMAGE_AVAILABLE:
            return {
                'success': False,
                'file_name': pdf_path.name,
                'error': 'pdf2image not installed. Install with: pip install pdf2image',
                'error_type': 'DependencyError'
            }
        
        logger.info(f"   📄 Converting PDF to images...")
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"   ℹ️  PDF has {len(images)} page(s)")
            
            # Process each page
            all_text_blocks = []
            all_text = []
            all_confidences = []
            
            for idx, image in enumerate(images, 1):
                logger.info(f"   📄 Processing page {idx}/{len(images)}...")
                
                if enhance:
                    image = self.preprocess_image(image)
                
                text, conf, blocks = self.extract_text_with_confidence(image)
                
                # Add page info to blocks
                for block in blocks:
                    block['page'] = idx
                
                all_text_blocks.extend(blocks)
                all_text.append(f"--- Page {idx} ---\n{text}")
                all_confidences.append(conf)
            
            # Combine results
            full_text = '\n\n'.join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            if avg_confidence >= 0.85:
                quality = "high"
            elif avg_confidence >= 0.65:
                quality = "medium"
            else:
                quality = "low"
            
            return {
                'success': True,
                'file_name': pdf_path.name,
                'file_path': str(pdf_path.absolute()),
                'file_type': '.pdf',
                'extracted_text': full_text,
                'full_text': full_text,
                'text_blocks': all_text_blocks,
                'metadata': {
                    'extraction_method': 'tesseract_ocr_pdf',
                    'confidence_score': round(avg_confidence, 3),
                    'quality': quality,
                    'page_count': len(images),
                    'word_count': len(full_text.split()),
                    'block_count': len(all_text_blocks),
                    'enhanced': enhance,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing PDF: {e}")
            return {
                'success': False,
                'file_name': pdf_path.name,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def process_folder(
        self, 
        folder_path: str,
        output_dir: str = 'output',
        enhance: bool = True
    ) -> Dict:
        """
        Process all images in a folder
        
        Args:
            folder_path: Path to folder containing images
            output_dir: Directory to save results
            enhance: Whether to pre-process images
            
        Returns:
            Summary dictionary
        """
        folder_path = Path(folder_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"❌ Folder not found: {folder_path}")
        
        # Find all supported files
        image_files = []
        for ext in self.SUPPORTED_FORMATS:
            image_files.extend(folder_path.glob(f'*{ext}'))
            image_files.extend(folder_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            logger.warning(f"⚠️  No supported images found in: {folder_path}")
            return {
                'success': False,
                'error': 'No supported image files found',
                'folder': str(folder_path)
            }
        
        logger.info(f"📁 Found {len(image_files)} image(s) in folder")
        
        # Process all images
        results = []
        successful = 0
        failed = 0
        
        for image_file in image_files:
            result = self.process_image(image_file, enhance=enhance)
            results.append(result)
            
            if result['success']:
                successful += 1
                
                # Save individual result
                output_file = output_dir / f"{image_file.stem}_ocr.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"   💾 Saved: {output_file.name}")
            else:
                failed += 1
        
        # Create summary
        summary = {
            'success': True,
            'folder': str(folder_path),
            'total_files': len(image_files),
            'successful': successful,
            'failed': failed,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save summary
        summary_file = output_dir / 'batch_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Batch processing complete: {successful}/{len(image_files)} successful")
        logger.info(f"💾 Summary saved to: {summary_file}")
        
        # ═══════════════════════════════════════════════════════════════
# NEW: Generate quality analysis report (doesn't break old code)
# ═══════════════════════════════════════════════════════════════
        try:
            from ocr_analyzer import OCRAnalyzer
            
            logger.info("\n📊 Generating quality analysis report...")
            analyzer = OCRAnalyzer(output_dir=str(output_dir))
            report = analyzer.generate_batch_report(summary)
            analyzer.save_report(report)
            
        except ImportError:
            logger.warning("⚠️  ocr_analyzer not found. Skipping quality analysis.")
        except Exception as e:
            logger.warning(f"⚠️  Quality analysis failed: {e}")

        return summary


def create_ocr_processor(tesseract_cmd: Optional[str] = None) -> DoclingOCR:
    """Factory function to create OCR processor"""
    return DoclingOCR(tesseract_cmd=tesseract_cmd)
