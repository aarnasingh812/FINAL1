import cv2
import numpy as np
import streamlit as st
import extraction
import LLM
import os
from dotenv import load_dotenv
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check for required API keys
required_keys = ['GROQ_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID']
missing_keys = [key for key in required_keys if not os.getenv(key)]

# Create temp directory if it doesn't exist
os.makedirs("temp", exist_ok=True)

# UI
st.set_page_config(
    page_title="Medicine Information Scanner",
    page_icon="💊",
    layout="wide"
)

st.title("Medicine Information Scanner")
st.write("Take a picture or upload an image of a medicine package to get detailed information.")

# Warning for missing API keys
if missing_keys:
    st.warning(f"Missing required API keys: {', '.join(missing_keys)}. Some features may not work.")

# Function to process images and display results
def process_image(image_path, image_display):
    try:
        # Process the image to extract text
        with st.spinner("Processing image..."):
            processed_image, extracted_text = extraction.extract_text(image_path)
        
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image_display, caption='Uploaded Image')
            
            # Display the extracted text
            st.subheader("Extracted Text:")
            if extracted_text.strip():
                st.code(extracted_text)
            else:
                st.error("No text could be extracted. Please try with a clearer image.")
        
        with col2:
            st.image(processed_image, caption='Processed Image')
            
            # Extract medicine name
            medicine_name = LLM.extract_medicine_name(extracted_text)
            if medicine_name:
                st.success(f"Identified medicine: {medicine_name}")
            else:
                st.warning("Could not identify medicine name from text.")
        
        if extracted_text.strip():
            # Generate medicine information using LLM
            with st.spinner("Searching for medicine information and generating response..."):
                llm_response = LLM.query_llm(extracted_text)
                
            st.subheader("Medicine Information:")
            st.markdown(llm_response)
            
            # Add disclaimer
            st.info("⚠️ DISCLAIMER: This information is for educational purposes only. Always consult a healthcare professional for medical advice and follow your prescription instructions.")
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

# Create tabs for camera and file upload
tab1, tab2 = st.tabs(["📷 Camera", "📁 Upload"])

with tab1:
    st.header("Camera Input")
    st.write("Take a clear picture of a medicine package or label.")
    
    pic = st.camera_input("Capture image")
    
    if pic is not None:
        bytes_data = pic.read()
        np_array = np.frombuffer(bytes_data, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        cv2.imwrite("cap_img.jpg", image)
        
        process_image("cap_img.jpg", pic)

with tab2:
    st.header("File Upload")
    st.write("Upload a clear image of a medicine package or label.")
    
    uploaded_file = st.file_uploader("Upload image:", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        np_array = np.frombuffer(bytes_data, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        temp_image_path = "captured_image.jpg"
        cv2.imwrite(temp_image_path, image)
        
        process_image(temp_image_path, uploaded_file)

# Add instructions at the bottom
st.divider()
with st.expander("Instructions & About"):
    st.markdown("""
    ### How to Use
    1. **Take a picture** of a medicine package using the camera tab, or **upload** an image file.
    2. The system will extract text from the image and identify the medicine name.
    3. Information about the medicine will be searched online and presented in a structured format.
    
    ### Tips for Best Results
    - Ensure good lighting when taking pictures
    - Focus on the part of the package with the medicine name and details
    - Make sure text is clearly visible and not blurry
    - For best results, capture the brand name and active ingredients
    
    ### Privacy Note
    Images are processed locally and not stored permanently. Search data is used only to retrieve medicine information.
    """)