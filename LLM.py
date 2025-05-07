import os
from groq import Groq
from dotenv import load_dotenv
import re
from search import search_medicine_info

def extract_medicine_name(text):
    """
    Extract the likely medicine name from the OCR text.
    
    Args:
        text (str): The OCR extracted text
        
    Returns:
        str: The extracted medicine name or empty string if none found
    """
    # Look for common medicine name patterns
    # This is a simple implementation - consider using NLP or more robust methods
    
    # Try to find the medicine name - usually one of the prominent words
    # Often, medicine names are in ALL CAPS or appear at the beginning of the text
    lines = text.strip().split('\n')
    
    # Check for all caps words which are often brand names
    for line in lines:
        words = line.split()
        for word in words:
            # Look for words that might be medicine names (all caps, no numbers, longer than 3 chars)
            if word.isupper() and len(word) > 3 and word.isalpha():
                return word
    
    # If no all-caps words found, try the first line which often contains the product name
    if lines and len(lines[0].strip()) > 0:
        # Return first line, limited to first 30 chars to avoid getting entire paragraphs
        return lines[0].strip()[:30]
    
    # Fallback - return nothing
    return ""

def query_llm(input_text):
    """
    Process extracted text, search for medicine info, and generate a structured response.
    
    Args:
        input_text (str): The text extracted from the medicine image
        
    Returns:
        str: Structured information about the medicine
    """
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get the API key from environment variables
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not groq_api_key:
            return "Unable to generate response. API key missing."
        
        # Extract medicine name from the OCR text
        medicine_name = extract_medicine_name(input_text)
        
        if not medicine_name:
            return "Could not identify a medicine name in the image. Please try again with a clearer image."
            
        # Search for medicine information online
        search_results = search_medicine_info(medicine_name)
        
        # Initialize the Groq client with API key
        client = Groq(api_key=groq_api_key)
        
        # Create a chat completion using the Groq API with a medicine-focused prompt
        chat_completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a helpful medical information assistant. 
                    Your task is to provide clear, factual information about medications based on reliable sources.
                    Structure your response in these sections:
                    1. Medicine Name: The identified medication
                    2. Primary Uses: What conditions this medicine typically treats
                    3. Dosage Information: General dosing guidelines (noting that specific dosage should be prescribed by a doctor)
                    4. Common Side Effects: The most frequently reported side effects
                    5. Precautions: Important warnings or contraindications
                    6. Important Note: Always remind users to consult healthcare professionals and follow their prescribed dosage.
                    
                    Be factual and avoid speculating. If information is unclear or missing, acknowledge this rather than guessing.
                    IMPORTANT: Never provide medical advice - only factual information about the medicine."""
                },
                {
                    "role": "user", 
                    "content": f"""I need information about a medication. 
                    Here is text extracted from a medicine package/label: 
                    
                    {input_text}
                    
                    I identified this as potentially being: {medicine_name}
                    
                    Here is additional information from search results:
                    
                    {search_results}
                    
                    Please provide structured information about this medication."""
                }
            ],
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1500
        )
        
        # Return the LLM's response
        return chat_completion.choices[0].message.content
    
    except Exception as e:
        # Return a user-friendly error message without exposing API details
        return f"Unable to generate response: {str(e)}"