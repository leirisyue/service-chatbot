from PIL import Image
import pytesseract
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        pass
    
    def extract_text_from_image(self, image_bytes: bytes) -> Optional[str]:
        """
        Extract text from image using OCR
        
        Args:
            image_bytes: Image bytes
            
        Returns:
            Extracted text or None if failed
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            logger.info(f"OCR extracted {len(text)} characters")
            return text.strip() if text.strip() else None
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return None
    
    def process_image_query(self, image_bytes: bytes, 
                           existing_text: Optional[str] = None) -> str:
        """
        Process image and combine with existing text query
        
        Args:
            image_bytes: Image bytes
            existing_text: Optional existing text query
            
        Returns:
            Combined query text
        """
        extracted_text = self.extract_text_from_image(image_bytes)
        
        if extracted_text and existing_text:
            return f"{existing_text}\n\nText from image:\n{extracted_text}"
        elif extracted_text:
            return extracted_text
        elif existing_text:
            return existing_text
        else:
            return ""

# Singleton instance
ocr_processor = OCRProcessor()