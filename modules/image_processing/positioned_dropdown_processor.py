# claude chat : https://claude.ai/chat/4186c51a-8786-4377-88b5-96b1aa7e36a2

"""
Module for processing positioned dropdown images using Claude API.
"""

import base64
import json
import re
import xml.etree.ElementTree as ET
import requests
from typing import Dict, List, Any, Optional

from modules.config import ANTHROPIC_API_KEY

def call_claude_api(image_bytes: bytes) -> str:
    """Call Claude Sonnet 4 API for positioned dropdown detection"""
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
    }
    
    # Convert bytes to base64
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_b64
                    }
                },
                {
                    "type": "text",
                    "text": get_detection_prompt()
                }
            ]
        }]
    }
    
    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        return result['content'][0]['text']
    else:
        raise Exception(f"Claude API Error: {response.status_code} - {response.text}")

def get_detection_prompt():
    """Detection prompt for Claude with selected option detection"""
    return """Please analyze this image and identify all dropdown menus. Look for EXPANDED dropdown menus that show lists of options, not just the trigger buttons.

For each dropdown menu you find, provide the coordinates for the ENTIRE VISIBLE DROPDOWN AREA (including all the options shown) in this EXACT XML format:

<QuestionOptions>
    <OptionSet index="1">
        <id>1</id>
        <x>412</x>
        <y>74</y>
        <width>185</width>
        <height>120</height>
        <ColumnHeaderStatement/>
        <Statement/>
        <ColumnHeaderOptions/>
        <Options>
            <Option>VIEW</Option>
            <Option selected="true">FUNCTION</Option>
            <Option>PROCEDURE</Option>
            <Option>TABLE</Option>
        </Options>
    </OptionSet>
</QuestionOptions>

CRITICAL XML FORMATTING RULES:
- ALL tags must be properly closed
- Root element must be <QuestionOptions>
- Each dropdown should be an <OptionSet> with index attribute
- Include id, x, y, width, height inside each OptionSet
- ColumnHeaderStatement, Statement, and ColumnHeaderOptions should be empty self-closing tags
- Each visible dropdown option should be wrapped in <Option> tags
- Extract the EXACT text visible in each dropdown option
- IMPORTANT: If an option appears SELECTED, HIGHLIGHTED, or in a DIFFERENT COLOR (like blue), add selected="true" attribute to that Option
- Return ONLY the XML structure, no additional text
- Ensure the XML is valid and well-formed

IMPORTANT DETECTION REQUIREMENTS:
- Detect the FULL expanded dropdown areas, not just small trigger buttons
- Include the entire rectangle containing all visible dropdown options
- Provide precise pixel coordinates for the complete dropdown region
- Extract each individual option text exactly as it appears in the dropdown
- CRITICAL: Identify which option is SELECTED/HIGHLIGHTED/BLUE and mark it with selected="true"
- Look for visual indicators like different background color, highlighting, or selection state"""

def remove_duplicate_options(options_list):
    """Remove duplicate options while preserving order"""
    if not options_list:
        return options_list
    
    seen = set()
    unique_options = []
    
    for option in options_list:
        option_lower = option.lower().strip()
        if option_lower not in seen:
            seen.add(option_lower)
            unique_options.append(option.strip())
    
    return unique_options

def clean_and_fix_xml(xml_text):
    """Clean and fix XML formatting"""
    
    xml_text = xml_text.replace('&', '&amp;')
    xml_text = xml_text.replace('<', '&lt;').replace('&lt;', '<', 1)
    xml_text = re.sub(r'&lt;(\w+)', r'<\1', xml_text)
    xml_text = re.sub(r'&lt;/(\w+)', r'</\1', xml_text)
    
    if '<QuestionOptions>' not in xml_text:
        if '<OptionSet>' in xml_text:
            xml_text = '<QuestionOptions>' + xml_text + '</QuestionOptions>'
    
    xml_text = re.sub(r'<QuestionOptions>\s*<QuestionOptions>', '<QuestionOptions>', xml_text)
    xml_text = re.sub(r'</QuestionOptions>\s*</QuestionOptions>', '</QuestionOptions>', xml_text)
    
    tag_patterns = ['id', 'x', 'y', 'width', 'height']
    for tag in tag_patterns:
        xml_text = re.sub(rf'<{tag}>([^<]*?)(?=\s*<(?!/)|\s*$)', rf'<{tag}>\1</{tag}>', xml_text)
    
    xml_text = re.sub(r'<Option>([^<]*?)(?=\s*<(?!/Option)|\s*</Options|\s*</OptionSet|\s*$)', r'<Option>\1</Option>', xml_text)
    
    empty_tags = ['ColumnHeaderStatement', 'Statement', 'ColumnHeaderOptions']
    for tag in empty_tags:
        xml_text = re.sub(rf'<{tag}></{tag}>', f'<{tag}/>', xml_text)
        xml_text = re.sub(rf'<{tag}>(?!\s*</{tag}>)', f'<{tag}/>', xml_text)
    
    xml_text = re.sub(r'>\s+<', '><', xml_text)
    xml_text = re.sub(r'\s+', ' ', xml_text)
    
    if not xml_text.startswith('<QuestionOptions>'):
        xml_text = '<QuestionOptions>' + xml_text
    if not xml_text.endswith('</QuestionOptions>'):
        xml_text = xml_text + '</QuestionOptions>'
    
    return xml_text

def extract_optionset_data(optionset_element):
    """Extract data from OptionSet XML element"""
    try:
        def safe_get_text(element, tag_name, default=None):
            elem = element.find(tag_name)
            if elem is not None and elem.text:
                return elem.text.strip()
            return default
        
        index = optionset_element.get('index', '1')
        
        id_text = safe_get_text(optionset_element, 'id')
        x_text = safe_get_text(optionset_element, 'x')
        y_text = safe_get_text(optionset_element, 'y')
        width_text = safe_get_text(optionset_element, 'width')
        height_text = safe_get_text(optionset_element, 'height')
        
        if not all([id_text, x_text, y_text, width_text, height_text]):
            return None
        
        options = []
        selected_options = []  # Track selected options
        options_container = optionset_element.find('Options')
        if options_container is not None:
            for option in options_container.findall('Option'):
                if option.text:
                    option_text = option.text.strip()
                    options.append(option_text)
                    
                    # Check if this option is selected
                    if option.get('selected') == 'true':
                        selected_options.append(option_text)
        
        options = remove_duplicate_options(options)
        selected_options = remove_duplicate_options(selected_options)
        
        dropdown_data = {
            'id': int(id_text),
            'x': int(x_text),
            'y': int(y_text),
            'width': int(width_text),
            'height': int(height_text),
            'options': options,
            'selected_options': selected_options,
            'option_count': len(options),
            'index': index
        }
        
        return dropdown_data
        
    except (ValueError, AttributeError):
        return None

def manual_extraction_fallback(response_text):
    """Manual extraction for new format"""
    
    try:
        dropdowns = []
        optionset_blocks = re.findall(r'<OptionSet[^>]*>(.*?)</OptionSet>', response_text, re.DOTALL)
        
        for i, block in enumerate(optionset_blocks):
            try:
                index_match = re.search(r'<OptionSet[^>]*index="([^"]*)"', response_text)
                index = index_match.group(1) if index_match else str(i+1)
                
                patterns = {
                    'id': r'<id>(\d+)</id>',
                    'x': r'<x>(\d+)</x>',
                    'y': r'<y>(\d+)</y>',
                    'width': r'<width>(\d+)</width>',
                    'height': r'<height>(\d+)</height>'
                }
                
                extracted = {}
                for field, pattern in patterns.items():
                    match = re.search(pattern, block, re.DOTALL)
                    if match:
                        extracted[field] = match.group(1).strip()
                
                options = []
                selected_options = []
                
                # Extract all options and check for selected ones
                option_matches = re.findall(r'<Option([^>]*)>(.*?)</Option>', block, re.DOTALL)
                for option_attrs, option_text in option_matches:
                    if option_text.strip():
                        option_text = option_text.strip()
                        options.append(option_text)
                        
                        # Check if this option has selected="true"
                        if 'selected="true"' in option_attrs:
                            selected_options.append(option_text)
                
                options = remove_duplicate_options(options)
                selected_options = remove_duplicate_options(selected_options)
                
                required_fields = ['id', 'x', 'y', 'width', 'height']
                if all(field in extracted for field in required_fields):
                    dropdown_data = {
                        'id': int(extracted['id']),
                        'x': int(extracted['x']),
                        'y': int(extracted['y']),
                        'width': int(extracted['width']),
                        'height': int(extracted['height']),
                        'options': options,
                        'selected_options': selected_options,
                        'option_count': len(options),
                        'index': index
                    }
                    dropdowns.append(dropdown_data)
                    
            except (ValueError, AttributeError):
                continue
        
        if dropdowns:
            return {'dropdowns': dropdowns, 'total_found': len(dropdowns)}
        else:
            return None
            
    except Exception:
        return None

def parse_ai_response(response_text):
    """Parse XML response"""
    try:
        response_text = response_text.strip()
        
        xml_start = response_text.find('<')
        xml_end = response_text.rfind('>') + 1
        if xml_start != -1 and xml_end > xml_start:
            response_text = response_text[xml_start:xml_end]
        
        response_text = clean_and_fix_xml(response_text)
        root = ET.fromstring(response_text)
        
        dropdowns = []
        for optionset in root.findall('.//OptionSet'):
            try:
                dropdown_data = extract_optionset_data(optionset)
                if dropdown_data:
                    dropdowns.append(dropdown_data)
            except Exception:
                continue
        
        if dropdowns:
            return {'dropdowns': dropdowns, 'total_found': len(dropdowns)}
        else:
            return manual_extraction_fallback(response_text)
            
    except ET.ParseError:
        return manual_extraction_fallback(response_text)
    except Exception:
        return manual_extraction_fallback(response_text)

def process_positioned_dropdown_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Process positioned dropdown image and return structured data.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        Dictionary containing dropdown data or error information
    """
    try:
        ai_response = call_claude_api(image_bytes)
        coordinates = parse_ai_response(ai_response)
        
        if coordinates and 'dropdowns' in coordinates:
            return coordinates
        else:
            return {"error": "Could not detect any dropdowns in the image"}
            
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}