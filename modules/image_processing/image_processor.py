"""
Module for handling image processing tasks.
"""

from io import BytesIO
from PIL import Image as PILImage
from typing import Dict, List, Any, Tuple
import json
import streamlit as st
import re

from modules.image_processing.api_client import (
    call_gemini_with_retry,
    extract_text_from_image
)

def is_valid_image(image_data: bytes) -> bool:
    """
    Check if image data is valid.
    
    Args:
        image_data: Image bytes
        
    Returns:
        Boolean indicating if image is valid
    """
    try:
        PILImage.open(BytesIO(image_data)).verify()
        return True
    except Exception:
        return False

def parse_question_options(extracted_text: str) -> List[Tuple[str, List[str]]]:
    """
    Parses the extracted text from a hotspot question image into a list of tuples.
    
    Args:
        extracted_text: Text extracted from hotspot question image
        
    Returns:
        List of (statement, available_options) tuples
    """
    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    
    # If the text begins with a header like "statement", "yes", "no", skip it.
    if len(lines) >= 3 and lines[0].lower() == "statement" and lines[1].lower() == "yes" and lines[2].lower() == "no":
        lines = lines[3:]
        
    combined_lines = []
    buffer = ""
    
    for line in lines:
        if not buffer:
            buffer = line
        else:
            if line and line[0].islower():
                buffer += " " + line
            else:
                combined_lines.append(buffer)
                buffer = line
                
    if buffer:
        combined_lines.append(buffer)
        
    # Only include statements with more than 20 characters
    statements = [l for l in combined_lines if len(l) > 20]
    return [(stmt, ["Yes", "No"]) for stmt in statements]

def extract_answers_from_image(image_bytes: bytes) -> List[Dict[str, str]]:
    """
    For HOTSPOT questions: extract answers from the answer image.
    
    Args:
        image_bytes: Image data
        
    Returns:
        List of answer dictionaries with statement and answer keys
    """
    prompt = """
    You are an expert in analyzing images of multiple-choice questions.
    In the provided image, a grey-colored rectangle indicates the selected (correct) answer.
    Extract the complete text of each statement along with its selected answer.
    Output a JSON array of objects with exactly two keys:
      "statement": the full text of the statement,
      "answer": either "Yes" or "No".
    Output ONLY valid JSON with no extra commentary.
    """
    
    raw_text = call_gemini_with_retry(prompt, image_bytes)
        # Clean up the response
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = re.sub(r'^json\s*', '', raw_text, flags=re.IGNORECASE).strip()
    
    try:
        return json.loads(raw_text)
    except Exception as e:
        return []

def extract_columns_dynamic(image_bytes: bytes) -> Dict[str, List[Dict[str, Any]]]:
    """
    For DRAGDROP questions: extract dynamic columns from the question image.
    
    Args:
        image_bytes: Image data
        
    Returns:
        Dictionary with columns key containing column information
    """
    prompt = """
    You are an expert in analyzing images of a drag-and-drop question.
    This question image has multiple columns (possibly 3 or more), each with a heading (like "Applications", "Feature", "Service", etc.).
    IMPORTANT: Extract ALL columns and their items completely, even if they appear in separate sections or different parts of the image.
    Pay special attention to ensuring you capture ALL columns shown in the image.
    
    Return the data in JSON with this structure:
    {
      "columns": [
        {"heading": "<column heading>", "items": ["item1", "item2", "..."]},
        ...
      ]
    }
    Output ONLY valid JSON, no extra commentary.
    """
    
    raw_text = call_gemini_with_retry(prompt, image_bytes)

    # Clean up the response
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = re.sub(r'^json\s*', '', raw_text, flags=re.IGNORECASE).strip()
    
    try:
        data = json.loads(raw_text)
        if not isinstance(data, dict) or "columns" not in data:
            return {"columns": []}
        return data
    except Exception as e:
        return {"columns": []}

def extract_pairs_dynamic(image_bytes: bytes) -> List[Dict[str, str]]:
    """
    For DRAGDROP questions: extract matched pairs from the answer image.
    
    Args:
        image_bytes: Image data
        
    Returns:
        List of dictionaries representing matched pairs
    """
    prompt = """
    You are an expert in analyzing images of a drag-and-drop question.
    This image shows the final matched pairs (or triplets) of the columns that appeared in the question image.
    Each row includes all relevant columns, matched to the correct items.
    Output a JSON array where each object has keys corresponding to the column headings.
    Output ONLY valid JSON, no extra commentary.
    """
    
    raw_text = call_gemini_with_retry(prompt, image_bytes)

    # Clean up the response
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = re.sub(r'^json\s*', '', raw_text, flags=re.IGNORECASE).strip()
    
    start_idx = raw_text.find('[')
    end_idx = raw_text.rfind(']')
    if start_idx != -1 and end_idx != -1:
        raw_text = raw_text[start_idx:end_idx+1]
    
    try:
        data = json.loads(raw_text)
        return data  # This should now be a parsed list of dictionaries
    except Exception as e:
        return []

def extract_just_dropdown_options(image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Extracts structured dropdown options from images marked with JustDropDown.
    
    Args:
        image_bytes: Image data
        
    Returns:
        List of dictionaries with labels and their associated options
    """
    prompt = """
    You are an expert in analyzing images containing dropdown menus.
    This image is marked with "JustDropDown:" which means it contains dropdown options.
    Extract ALL dropdown options WITH their category/parameter labels.

    Return ONLY a JSON array using this format:
    [
      {
        "label": "parameter_name", 
        "options": ["option1", "option2", "option3"]
      },
      {
        "label": "another_parameter",
        "options": ["choice1", "choice2"]
      }
    ]

    Make sure to:
    1. Include ALL dropdown menus visible in the image
    2. Return ONLY valid JSON with no extra text or commentary
    3. Use exact text for options and labels
    """
    
    raw_text = call_gemini_with_retry(prompt, image_bytes)

            # Clean up the response
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = re.sub(r'^json\s*', '', raw_text, flags=re.IGNORECASE).strip()
        
    start_idx = raw_text.find('[')
    end_idx = raw_text.rfind(']')
    if start_idx != -1 and end_idx != -1:
            raw_text = raw_text[start_idx:end_idx+1]
        
    try:
        data = json.loads(raw_text)
        return data
    except Exception as e:
        return []

def extract_dropdown_questions(image_bytes: bytes, is_just_dropdown: bool = False) -> List[Dict[str, Any]]:
    """
    Uses Gemini to parse the question image for DROPDOWN questions.
    
    Args:
        image_bytes: Image data
        is_just_dropdown: Flag to indicate if this is a JustDropDown question
        
    Returns:
        List of dropdown question dictionaries
    """
    if is_just_dropdown:
        return extract_just_dropdown_options(image_bytes)
    
    # Original behavior for normal dropdown questions
    prompt = """
    You are an expert in analyzing an image that shows two columns with headers.
    One column (the left) contains the statement header and statement text,
    and the other column (the right) contains the options header and the dropdown options.
    For each row in the image, extract:
      - "statement_header": the header for the statement column,
      - "statement": the statement text,
      - "options_header": the header for the options column,
      - "options": an array of the dropdown options.
    Return a JSON array of objects with these four keys.
    Output ONLY valid JSON, with no extra commentary.
    """
    
    raw_text = call_gemini_with_retry(prompt, image_bytes)

    # Clean up the response
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = re.sub(r'^json\s*', '', raw_text, flags=re.IGNORECASE).strip()
        
    start_idx = raw_text.find('[')
    end_idx = raw_text.rfind(']')
    if start_idx != -1 and end_idx != -1:
        raw_text = raw_text[start_idx:end_idx+1]
        
    try:
        data = json.loads(raw_text)
        return data
    except Exception as e:
        return []

def extract_dropdown_answers(image_bytes: bytes) -> List[Dict[str, str]]:
    """
    Uses Gemini to parse the answer image for DROPDOWN questions.
    
    Args:
        image_bytes: Image data
        
    Returns:
        List of dropdown answer dictionaries
    """
    prompt = """
    You are an expert in analyzing an image that shows two columns with headers.
    One column contains the statement header and statement text,
    and the other column contains the answer header and the highlighted answer.
    For each row, extract:
      - "statement_header": the header for the statement column,
      - "statement": the full text of the statement,
      - "answer_header": the header for the answer column,
      - "answer": the highlighted option text.
    Return a JSON array of objects with these four keys.
    Output ONLY valid JSON, with no extra commentary.
    """
    
    raw_text = call_gemini_with_retry(prompt, image_bytes)
    # Clean up the response
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = re.sub(r'^json\s*', '', raw_text, flags=re.IGNORECASE).strip()
    
    start_idx = raw_text.find('[')
    end_idx = raw_text.rfind(']')
    if start_idx != -1 and end_idx != -1:
        raw_text = raw_text[start_idx:end_idx+1]
    
    try:
        data = json.loads(raw_text)
        return data
    except Exception as e:
        
        answer_text = extract_text_from_image(image_bytes)
        
        # Try to manually parse the text into answer items
        answers = []
        lines = answer_text.strip().split('\n')
        
        for line in lines:
            # Look for patterns like "parameter_name" : value OR parameter_name: value
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    header = parts[0].strip().strip('"\'')
                    value = parts[1].strip()
                    
                    if header and value:
                        answers.append({
                            "statement_header": header,
                            "statement": f'"{header}" :',
                            "answer_header": "",
                            "answer": value
                        })
        
        if answers:
            st.info(f"Manually extracted {len(answers)} answers")
            return answers
        
        return []


def identify_image_types(content_items):
    """
    Identify the types of images based on preceding text in content items.
    
    Args:
        content_items: List of content item dictionaries
        
    Returns:
        Dictionary mapping image paths to their identified types
    """
    image_types = {}
    current_type = None
    
    for item in content_items:
        content = item.get("content", "").strip()
        
        # Check for image type markers
        if "QuestionOptionImage:" in content:
            current_type = "question"
        elif "AnswerOptionImage:" in content:
            current_type = "answer"
        elif "QuestionDescriptionImage:" in content:
            current_type = "description"
        elif "JustDropDown:" in content:
            current_type = "justdropdown"
        elif "PositionedImage:" in content:  # ← Add this new marker
            current_type = "positioned"
        elif "BackgroundImage:" in content:  # ← ADD THIS NEW MARKER
            current_type = "background"
        elif "JustCoordinates:" in content:
            current_type = "just_coordinates"
        # Other potential markers can be added here
        
        # If this item has images, assign the current type to them
        if "images" in item and item["images"] and current_type:
            for img in item["images"]:
                if "path" in img:
                    image_types[img["path"]] = current_type
    
    return image_types




















