import os
import json
import requests
from dotenv import load_dotenv

def search_medicine_info(medicine_name):
    """
    Search for information about a medicine using Google Custom Search API.
    
    Args:
        medicine_name (str): The name of the medicine to search for
        
    Returns:
        str: Compiled search results information
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key and Search Engine ID from environment variables
        api_key = os.getenv('GOOGLE_API_KEY')
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not api_key or not search_engine_id:
            return "Google Search API configuration is missing."
        
        # Construct search query
        query = f"{medicine_name} medicine usage information dosage"
        
        # Make request to Google Custom Search API
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': query,
            'num': 3  # Number of results to return
        }
        
        response = requests.get(url, params=params)
        results = response.json()
        
        # Process and format the search results
        if 'items' not in results:
            return f"No information found for {medicine_name}."
        
        # Compile relevant information from search results
        compiled_info = f"Search Results for {medicine_name}:\n\n"
        
        for item in results['items']:
            compiled_info += f"Title: {item.get('title', 'N/A')}\n"
            compiled_info += f"Source: {item.get('displayLink', 'N/A')}\n"
            compiled_info += f"Snippet: {item.get('snippet', 'N/A')}\n\n"
        
        return compiled_info
    
    except Exception as e:
        return f"Error searching for medicine information: {str(e)}"