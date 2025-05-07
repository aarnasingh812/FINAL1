import pytesseract
import cv2
import numpy as np
import platform
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Tesseract path based on operating system
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# For macOS (Homebrew installation)
elif platform.system() == 'Darwin':
    if os.path.exists("/usr/local/bin/tesseract"):
        pytesseract.pytesseract.tesseract_cmd = r"/usr/local/bin/tesseract"
    elif os.path.exists("/opt/homebrew/bin/tesseract"):
        pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"
# For Linux
elif platform.system() == 'Linux':
    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# Create temp directory if it doesn't exist
os.makedirs("temp", exist_ok=True)

# Configuration for OCR - optimized for medicine labels
# PSM 6: Assume a single uniform block of text
# PSM 3: Fully automatic page segmentation, but no OSD (use this if PSM 6 fails)
# OEM 3: Default, based on LSTM neural network
myconfig = r"--psm 6 --oem 3"

def preprocess_image(image_path):
    """
    Preprocess the image for optimal OCR text extraction from medicine labels.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (original image, preprocessed image)
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
            
        # Keep a copy of original image
        original = img.copy()
        
        # Resize for better OCR accuracy - medicine labels often have small text
        scale_percent = 200  # Increase size by 200%
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Try multiple preprocessing techniques and store them
        # 1. Basic denoising
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # 2. Adaptive thresholding
        thresh_adaptive = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 3. Otsu's thresholding
        _, thresh_otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. Edge enhancement
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        _, thresh_sharp = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Save intermediate images for debugging
        cv2.imwrite("temp/gray.png", gray)
        cv2.imwrite("temp/denoised.png", denoised)
        cv2.imwrite("temp/thresh_adaptive.png", thresh_adaptive)
        cv2.imwrite("temp/thresh_otsu.png", thresh_otsu)
        cv2.imwrite("temp/thresh_sharp.png", thresh_sharp)
        
        # Return original and the sharpened threshold image which often works best for text
        return original, thresh_sharp
        
    except Exception as e:
        logger.error(f"Error in preprocessing image: {str(e)}")
        # Return original image if available, or raise the exception
        if 'original' in locals():
            return original, original
        raise

def extract_text(image_path):
    """
    Extract text from an image of a medicine label.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (processed image with text boxes, extracted text)
    """
    try:
        # Preprocess the image
        img, preprocessed_img = preprocess_image(image_path)
        
        # Create a copy for drawing
        result_img = img.copy()
        
        # Run OCR with both preprocessing methods and combine results
        text = pytesseract.image_to_string(preprocessed_img, config=myconfig)
        
        # If text is minimal, try with different PSM mode
        if len(text.strip()) < 10:
            logger.info("Initial OCR yielded minimal text, trying with different PSM mode")
            text = pytesseract.image_to_string(
                preprocessed_img, 
                config=r"--psm 3 --oem 3"  # Try with auto page segmentation
            )
        
        # Draw bounding boxes around detected text for visualization
        boxes = pytesseract.image_to_data(preprocessed_img, config=myconfig, output_type=pytesseract.Output.DICT)
        
        # Resize result_img to match the size of preprocessed_img if needed
        if result_img.shape[:2] != preprocessed_img.shape[:2]:
            result_img = cv2.resize(
                result_img, 
                (preprocessed_img.shape[1], preprocessed_img.shape[0]), 
                interpolation=cv2.INTER_CUBIC
            )
        
        # Draw boxes around text
        for i in range(len(boxes['text'])):
            if int(boxes['conf'][i]) > 60:  # Only consider text with confidence > 60%
                (x, y, w, h) = (
                    boxes['left'][i], boxes['top'][i], 
                    boxes['width'][i], boxes['height'][i]
                )
                # Draw green rectangle around text
                cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Save the result image
        cv2.imwrite("temp/text_boxes.png", result_img)
        
        logger.info(f"Extracted text length: {len(text)}")
        return result_img, text
        
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        if 'img' in locals():
            return img, f"Error extracting text: {str(e)}"
        raise

    