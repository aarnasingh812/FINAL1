from flask import Flask, request, jsonify, render_template
import os
import cv2
import numpy as np
import extraction
import LLM
import logging
from dotenv import load_dotenv
import tempfile
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required API keys
required_keys = ['GROQ_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID']
missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    logger.warning(f"Missing required API keys: {', '.join(missing_keys)}")

# Create temp directory if it doesn't exist
os.makedirs("temp", exist_ok=True)

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_image():
    """Process uploaded image and return the results."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        # Get the uploaded file
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            temp_path = temp.name
            file.save(temp_path)
            
        # Process the image
        processed_image, extracted_text = extraction.extract_text(temp_path)
        
        # Convert images to base64 for sending to frontend
        _, img_encoded = cv2.imencode('.jpg', processed_image)
        processed_image_b64 = base64.b64encode(img_encoded).decode('utf-8')
        
        # Extract medicine name
        medicine_name = LLM.extract_medicine_name(extracted_text)
        
        response_data = {
            'success': True,
            'extracted_text': extracted_text,
            'processed_image': processed_image_b64,
            'medicine_name': medicine_name
        }
        
        # Only process with LLM if text was extracted
        if extracted_text.strip():
            # Generate medicine information using LLM
            llm_response = LLM.query_llm(extracted_text)
            response_data['llm_response'] = llm_response
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/process_camera', methods=['POST'])
def process_camera_image():
    """Process image from camera and return the results."""
    try:
        # Get base64 image from request
        data = request.json
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
            
        # Decode base64 image
        image_data = data['image'].split(',')[1]  # Remove data URL prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # Save to temporary file
        temp_path = "temp_camera.jpg"
        cv2.imwrite(temp_path, img)
        
        # Process the image
        processed_image, extracted_text = extraction.extract_text(temp_path)
        
        # Convert processed image to base64
        _, img_encoded = cv2.imencode('.jpg', processed_image)
        processed_image_b64 = base64.b64encode(img_encoded).decode('utf-8')
        
        # Extract medicine name
        medicine_name = LLM.extract_medicine_name(extracted_text)
        
        response_data = {
            'success': True,
            'extracted_text': extracted_text,
            'processed_image': processed_image_b64,
            'medicine_name': medicine_name
        }
        
        # Only process with LLM if text was extracted
        if extracted_text.strip():
            # Generate medicine information using LLM
            llm_response = LLM.query_llm(extracted_text)
            response_data['llm_response'] = llm_response
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing camera image: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

    