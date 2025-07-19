"""
Module for handling API calls to Gemini.
"""

import json
import time
import re
import streamlit as st
import google.generativeai as genai
from typing import Optional, Dict, List, Any, Union

from modules.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_API_RETRIES, RETRY_DELAY_BASE

# Configure API
genai.configure(api_key=GEMINI_API_KEY)

def call_gemini_with_retry(prompt: str, image_data: Optional[bytes] = None) -> str:
    """
    Call Gemini API with automatic retry on failure.
    
    Args:
        prompt: The text prompt to send to Gemini
        image_data: Optional image data bytes
        
    Returns:
        Response text from Gemini
    """
    retries = 0
    last_exception = None
    
    while retries < MAX_API_RETRIES:
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            if image_data:
                image_parts = [{"mime_type": "image/png", "data": image_data}]
                response = model.generate_content([prompt, image_parts[0]])
            else:
                response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            last_exception = e
            retries += 1
            time.sleep(RETRY_DELAY_BASE * retries)  # Exponential backoff
    
    st.error(f"Error after {MAX_API_RETRIES} retries: {str(last_exception)}")
    return "[]" if "JSON" in prompt else ""

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Use Gemini to extract text from image.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        Extracted text
    """
    prompt = """
    You are an expert in analyzing images.
    Extract and return all the text from the provided image.
    Output only the extracted text with no additional commentary.
    """
    
    return call_gemini_with_retry(prompt, image_bytes)
    
