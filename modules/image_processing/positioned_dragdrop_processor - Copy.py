# """
# Module for processing positioned drag-drop images using Claude API.
# """

# import base64
# import json
# import re
# import xml.etree.ElementTree as ET
# import requests
# from typing import Dict, List, Any, Optional

# from modules.config import ANTHROPIC_API_KEY

# def call_claude_api(image_bytes: bytes) -> str:
#     """Call Claude Sonnet 4 API for positioned drag-drop detection"""
#     headers = {
#         'Content-Type': 'application/json',
#         'x-api-key': ANTHROPIC_API_KEY,
#         'anthropic-version': '2023-06-01'
#     }
    
#     # Convert bytes to base64
#     image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
#     payload = {
#         "model": "claude-sonnet-4-20250514",
#         "max_tokens": 2000,
#         "messages": [{
#             "role": "user",
#             "content": [
#                 {
#                     "type": "image",
#                     "source": {
#                         "type": "base64",
#                         "media_type": "image/png",
#                         "data": image_b64
#                     }
#                 },
#                 {
#                     "type": "text",
#                     "text": get_detection_prompt()
#                 }
#             ]
#         }]
#     }
    
#     response = requests.post(
#         'https://api.anthropic.com/v1/messages',
#         headers=headers,
#         json=payload
#     )
    
#     if response.status_code == 200:
#         result = response.json()
#         return result['content'][0]['text']
#     else:
#         raise Exception(f"Claude API Error: {response.status_code} - {response.text}")

# def get_detection_prompt():
#     """Detection prompt for Claude with positioned drag-drop detection"""
#     return """Please analyze this image and identify:

# 1. **RECTANGULAR BOXES/AREAS**: Look for any rectangular selection boxes, highlighted areas, or distinct rectangular regions in the main content area.

# 2. **SIDEBAR OPTIONS**: Look for any menu options, buttons, or selectable items on the left side of the interface.

# 3. **TEXT CONTENT IN BOXES**: For each rectangular box, identify what text content is displayed within that box.

# For each rectangular area you find, and for the sidebar options, provide the information in this EXACT XML format:

# <DynamicColumns>
# <Column heading="Values">
# <Item>DEFINE</Item>
# <Item>EVALUATE</Item>
# <Item>FILTER</Item>
# <Item>SUMMARIZE</Item>
# <Item>TABLE</Item>
# </Column>
# <Box index="1">
# <id>1</id>
# <x>514</x>
# <y>42</y>
# <width>100</width>
# <height>25</height>
# </Box>
# <Box index="2">
# <id>2</id>
# <x>514</x>
# <y>130</y>
# <width>100</width>
# <height>25</height>
# </Box>
# <AnswerPairs>
# <Pair>
# <Column name="Box 1" index="1" id="1" x="514" y="42" width="100" height="25">DEFINE</Column>
# </Pair>
# <Pair>
# <Column name="Box 2" index="2" id="2" x="514" y="130" width="100" height="25">EVALUATE</Column>
# </Pair>
# </AnswerPairs>
# </DynamicColumns>

# IMPORTANT: In the AnswerPairs section, the text content between the Column tags should be the actual text you can read inside each rectangular box in the image. Look carefully at what text appears within each detected rectangular area.

# Return ONLY the XML structure, no additional text."""

# def clean_xml_response(response_text):
#     """Clean and extract XML from Claude response"""
#     # Extract XML portion
#     xml_start = response_text.find('<DynamicColumns')
#     xml_end = response_text.rfind('</DynamicColumns>') + len('</DynamicColumns>')
    
#     if xml_start != -1 and xml_end > xml_start:
#         xml_content = response_text[xml_start:xml_end]
#     else:
#         xml_content = response_text
    
#     # Basic XML cleaning
#     xml_content = xml_content.replace('&', '&amp;')
#     xml_content = xml_content.replace('&amp;lt;', '&lt;')
#     xml_content = xml_content.replace('&amp;gt;', '&gt;')
    
#     return xml_content

# def parse_positioned_dragdrop_response(response_text):
#     """Parse the positioned drag-drop response into structured data"""
#     try:
#         # Clean the XML response
#         clean_xml = clean_xml_response(response_text)
        
#         # Parse XML
#         root = ET.fromstring(clean_xml)
        
#         # Extract data
#         result = {
#             'columns': [],
#             'boxes': [],
#             'answer_pairs': []
#         }
        
#         # Extract columns (sidebar options)
#         for column in root.findall('Column'):
#             heading = column.get('heading', '')
#             items = [item.text for item in column.findall('Item') if item.text]
#             result['columns'].append({
#                 'heading': heading,
#                 'items': items
#             })
        
#         # Extract boxes (rectangular areas)
#         for box in root.findall('Box'):
#             box_data = {
#                 'index': box.get('index', ''),
#                 'id': box.find('id').text if box.find('id') is not None else '',
#                 'x': int(box.find('x').text) if box.find('x') is not None else 0,
#                 'y': int(box.find('y').text) if box.find('y') is not None else 0,
#                 'width': int(box.find('width').text) if box.find('width') is not None else 0,
#                 'height': int(box.find('height').text) if box.find('height') is not None else 0
#             }
#             result['boxes'].append(box_data)
        
#         # Extract answer pairs
#         answer_pairs_elem = root.find('AnswerPairs')
#         if answer_pairs_elem is not None:
#             for pair in answer_pairs_elem.findall('Pair'):
#                 for column in pair.findall('Column'):
#                     pair_data = {
#                         'name': column.get('name', ''),
#                         'index': column.get('index', ''),
#                         'id': column.get('id', ''),
#                         'x': int(column.get('x', 0)),
#                         'y': int(column.get('y', 0)),
#                         'width': int(column.get('width', 0)),
#                         'height': int(column.get('height', 0)),
#                         'text': column.text or ''
#                     }
#                     result['answer_pairs'].append(pair_data)
        
#         return result
        
#     except Exception as e:
#         return {"error": f"Failed to parse response: {str(e)}"}

# def process_positioned_dragdrop_image(image_bytes: bytes) -> Dict[str, Any]:
#     """
#     Process positioned drag-drop image and return structured data.
    
#     Args:
#         image_bytes: Image data as bytes
        
#     Returns:
#         Dictionary containing positioned drag-drop data or error information
#     """
#     try:
#         ai_response = call_claude_api(image_bytes)
#         result = parse_positioned_dragdrop_response(ai_response)
        
#         if "error" not in result:
#             return result
#         else:
#             return result
            
#     except Exception as e:
#         return {"error": f"Error processing image: {str(e)}"}

































# for 3 images  Background, just coordinates and positioned image

# """
# Module for processing positioned drag-drop images using Claude API.
# """

# import base64
# import json
# import re
# import xml.etree.ElementTree as ET
# import requests
# from typing import Dict, List, Any, Optional

# from modules.config import ANTHROPIC_API_KEY

# def call_claude_api(image_bytes: bytes, prompt: str) -> str:
#     """Call Claude Sonnet 4 API with custom prompt"""
#     headers = {
#         'Content-Type': 'application/json',
#         'x-api-key': ANTHROPIC_API_KEY,
#         'anthropic-version': '2023-06-01'
#     }
    
#     # Convert bytes to base64
#     image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
#     payload = {
#         "model": "claude-sonnet-4-20250514",
#         "max_tokens": 2000,
#         "messages": [{
#             "role": "user",
#             "content": [
#                 {
#                     "type": "image",
#                     "source": {
#                         "type": "base64",
#                         "media_type": "image/png",
#                         "data": image_b64
#                     }
#                 },
#                 {
#                     "type": "text",
#                     "text": prompt
#                 }
#             ]
#         }]
#     }
    
#     response = requests.post(
#         'https://api.anthropic.com/v1/messages',
#         headers=headers,
#         json=payload
#     )
    
#     if response.status_code == 200:
#         result = response.json()
#         return result['content'][0]['text']
#     else:
#         raise Exception(f"Claude API Error: {response.status_code} - {response.text}")

# def get_coordinates_detection_prompt():
#     """Prompt for extracting only coordinates from JustCoordinates image"""
#     return """Please analyze this image and identify ONLY the RECTANGULAR BOXES/AREAS.

# Look for any rectangular selection boxes, highlighted areas, or distinct rectangular regions in the main content area.

# For each rectangular area you find, provide the information in this EXACT XML format:

# <CoordinatesData>
# <Box index="1">
# <id>1</id>
# <x>514</x>
# <y>42</y>
# <width>100</width>
# <height>25</height>
# </Box>
# <Box index="2">
# <id>2</id>
# <x>514</x>
# <y>130</y>
# <width>100</width>
# <height>25</height>
# </Box>
# </CoordinatesData>

# IMPORTANT: Only provide the coordinates and dimensions of the rectangular boxes. Do not extract any text content.

# Return ONLY the XML structure, no additional text."""

# def get_positioned_data_detection_prompt():
#     """Prompt for extracting only columns and answer text from PositionedImage"""
#     return """Please analyze this image and identify:

# 1. **SIDEBAR OPTIONS**: Look for any menu options, buttons, or selectable items on the left side of the interface.

# 2. **TEXT CONTENT IN BOXES**: For each rectangular box, identify what text content is displayed within that box.

# For the sidebar options and text content, provide the information in this EXACT XML format:

# <PositionedData>
# <Column heading="Values">
# <Item>DEFINE</Item>
# <Item>EVALUATE</Item>
# <Item>FILTER</Item>
# <Item>SUMMARIZE</Item>
# <Item>TABLE</Item>
# </Column>
# <AnswerPairs>
# <Pair>
# <Column name="Box 1" index="1" id="1">DEFINE</Column>
# </Pair>
# <Pair>
# <Column name="Box 2" index="2" id="2">EVALUATE</Column>
# </Pair>
# </AnswerPairs>
# </PositionedData>

# IMPORTANT: 
# - Do NOT include coordinates (x, y, width, height) in this response
# - Only extract the sidebar options and the text content visible in the boxes
# - The text content between the Column tags should be the actual text you can read inside each rectangular box

# Return ONLY the XML structure, no additional text."""

# def clean_xml_response(response_text):
#     """Clean and extract XML from Claude response"""
#     # Extract XML portion - handle both CoordinatesData and PositionedData
#     xml_start = -1
#     xml_end = -1
    
#     # Try to find CoordinatesData
#     coord_start = response_text.find('<CoordinatesData')
#     coord_end = response_text.rfind('</CoordinatesData>') + len('</CoordinatesData>')
    
#     # Try to find PositionedData
#     pos_start = response_text.find('<PositionedData')
#     pos_end = response_text.rfind('</PositionedData>') + len('</PositionedData>')
    
#     if coord_start != -1 and coord_end > coord_start:
#         xml_start = coord_start
#         xml_end = coord_end
#     elif pos_start != -1 and pos_end > pos_start:
#         xml_start = pos_start
#         xml_end = pos_end
#     else:
#         # Fallback to DynamicColumns if present
#         xml_start = response_text.find('<DynamicColumns')
#         xml_end = response_text.rfind('</DynamicColumns>') + len('</DynamicColumns>')
    
#     if xml_start != -1 and xml_end > xml_start:
#         xml_content = response_text[xml_start:xml_end]
#     else:
#         xml_content = response_text
    
#     # Basic XML cleaning
#     xml_content = xml_content.replace('&', '&amp;')
#     xml_content = xml_content.replace('&amp;lt;', '&lt;')
#     xml_content = xml_content.replace('&amp;gt;', '&gt;')
    
#     return xml_content

# def parse_coordinates_response(response_text):
#     """Parse coordinates-only response"""
#     try:
#         clean_xml = clean_xml_response(response_text)
#         root = ET.fromstring(clean_xml)
        
#         result = {
#             'boxes': []
#         }
        
#         # Extract boxes (rectangular areas)
#         for box in root.findall('Box'):
#             box_data = {
#                 'index': box.get('index', ''),
#                 'id': box.find('id').text if box.find('id') is not None else '',
#                 'x': int(box.find('x').text) if box.find('x') is not None else 0,
#                 'y': int(box.find('y').text) if box.find('y') is not None else 0,
#                 'width': int(box.find('width').text) if box.find('width') is not None else 0,
#                 'height': int(box.find('height').text) if box.find('height') is not None else 0
#             }
#             result['boxes'].append(box_data)
        
#         return result
        
#     except Exception as e:
#         return {"error": f"Failed to parse coordinates response: {str(e)}"}

# def parse_positioned_data_response(response_text):
#     """Parse positioned data response (columns and answer pairs only)"""
#     try:
#         clean_xml = clean_xml_response(response_text)
#         root = ET.fromstring(clean_xml)
        
#         result = {
#             'columns': [],
#             'answer_pairs': []
#         }
        
#         # Extract columns (sidebar options)
#         for column in root.findall('Column'):
#             heading = column.get('heading', '')
#             items = [item.text for item in column.findall('Item') if item.text]
#             result['columns'].append({
#                 'heading': heading,
#                 'items': items
#             })
        
#         # Extract answer pairs (without coordinates)
#         answer_pairs_elem = root.find('AnswerPairs')
#         if answer_pairs_elem is not None:
#             for pair in answer_pairs_elem.findall('Pair'):
#                 for column in pair.findall('Column'):
#                     pair_data = {
#                         'name': column.get('name', ''),
#                         'index': column.get('index', ''),
#                         'id': column.get('id', ''),
#                         'text': column.text or ''
#                     }
#                     result['answer_pairs'].append(pair_data)
        
#         return result
        
#     except Exception as e:
#         return {"error": f"Failed to parse positioned data response: {str(e)}"}

# def process_coordinates_only(image_bytes: bytes) -> Dict[str, Any]:
#     """
#     Process JustCoordinates image to extract only box coordinates.
    
#     Args:
#         image_bytes: Image data as bytes
        
#     Returns:
#         Dictionary containing only box coordinates or error information
#     """
#     try:
#         prompt = get_coordinates_detection_prompt()
#         ai_response = call_claude_api(image_bytes, prompt)
#         result = parse_coordinates_response(ai_response)
        
#         return result
            
#     except Exception as e:
#         return {"error": f"Error processing coordinates image: {str(e)}"}

# def process_positioned_data_only(image_bytes: bytes) -> Dict[str, Any]:
#     """
#     Process PositionedImage to extract only columns and answer text.
    
#     Args:
#         image_bytes: Image data as bytes
        
#     Returns:
#         Dictionary containing columns and answer pairs (without coordinates) or error information
#     """
#     try:
#         prompt = get_positioned_data_detection_prompt()
#         ai_response = call_claude_api(image_bytes, prompt)
#         result = parse_positioned_data_response(ai_response)
        
#         return result
            
#     except Exception as e:
#         return {"error": f"Error processing positioned data image: {str(e)}"}

# # Keep the original function for backward compatibility
# def process_positioned_dragdrop_image(image_bytes: bytes) -> Dict[str, Any]:
#     """
#     DEPRECATED: Original function for backward compatibility.
#     Use process_coordinates_only and process_positioned_data_only instead.
#     """
#     return {"error": "This function is deprecated. Use process_coordinates_only and process_positioned_data_only instead."}
































"""
Module for processing positioned drag-drop images using Claude API.
"""

import base64
import json
import re
import xml.etree.ElementTree as ET
import requests
from typing import Dict, List, Any, Optional

from modules.config import ANTHROPIC_API_KEY

def call_claude_api(image_bytes: bytes, prompt: str) -> str:
    """Call Claude Sonnet 4 API with custom prompt"""
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
                    "text": prompt
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

# def get_coordinates_detection_prompt():
#     """Prompt for extracting only coordinates from BackgroundImage"""
#     return """Please analyze this image and identify ONLY the RECTANGULAR BOXES/AREAS.

# Look for any rectangular selection boxes, highlighted areas, or distinct rectangular regions in the main content area.

# For each rectangular area you find, provide the information in this EXACT XML format:

# <CoordinatesData>
# <Box index="1">
# <id>1</id>
# <x>514</x>
# <y>42</y>
# <width>100</width>
# <height>25</height>
# </Box>
# <Box index="2">
# <id>2</id>
# <x>514</x>
# <y>130</y>
# <width>100</width>
# <height>25</height>
# </Box>
# </CoordinatesData>

# IMPORTANT: Only provide the coordinates and dimensions of the rectangular boxes. Do not extract any text content.

# Return ONLY the XML structure, no additional text."""


def get_coordinates_detection_prompt():
    """Prompt for extracting only coordinates from BackgroundImage"""
    return """Please analyze this image and identify the RECTANGULAR BOXES/AREAS where answers should be placed.

Look specifically for:
1. The empty rectangle/box areas in the code snippet
2. Areas that look like input fields or blank spaces for answers
3. Rectangular regions that are visually distinct from the surrounding content

For each rectangular area you find, provide the information in this EXACT XML format:

<CoordinatesData>
<Box index="1">
<id>1</id>
<x>514</x>
<y>42</y>
<width>100</width>
<height>25</height>
</Box>
<Box index="2">
<id>2</id>
<x>514</x>
<y>130</y>
<width>100</width>
<height>25</height>
</Box>
</CoordinatesData>

IMPORTANT: 
- Focus on finding the exact pixel coordinates of areas where answers should be filled in
- Pay special attention to empty brackets [] or blank areas in the code that appear to be placeholders
- The x,y coordinates should represent the top-left corner of each box
- Provide precise width and height measurements in pixels

Return ONLY the XML structure, no additional text."""

def get_positioned_data_detection_prompt():
    """Prompt for extracting only columns and answer text from PositionedImage"""
    return """Please analyze this image and identify:

1. **SIDEBAR OPTIONS**: Look for any menu options, buttons, or selectable items on the left side of the interface.

2. **TEXT CONTENT IN BOXES**: For each rectangular box, identify what text content is displayed within that box.

For the sidebar options and text content, provide the information in this EXACT XML format:

<PositionedData>
<Column heading="Values">
<Item>DEFINE</Item>
<Item>EVALUATE</Item>
<Item>FILTER</Item>
<Item>SUMMARIZE</Item>
<Item>TABLE</Item>
</Column>
<AnswerPairs>
<Pair>
<Column name="Box 1" index="1" id="1">DEFINE</Column>
</Pair>
<Pair>
<Column name="Box 2" index="2" id="2">EVALUATE</Column>
</Pair>
</AnswerPairs>
</PositionedData>

IMPORTANT: 
- Do NOT include coordinates (x, y, width, height) in this response
- Only extract the sidebar options and the text content visible in the boxes
- The text content between the Column tags should be the actual text you can read inside each rectangular box

Return ONLY the XML structure, no additional text."""

def clean_xml_response(response_text):
    """Clean and extract XML from Claude response"""
    # Extract XML portion - handle both CoordinatesData and PositionedData
    xml_start = -1
    xml_end = -1
    
    # Try to find CoordinatesData
    coord_start = response_text.find('<CoordinatesData')
    coord_end = response_text.rfind('</CoordinatesData>') + len('</CoordinatesData>')
    
    # Try to find PositionedData
    pos_start = response_text.find('<PositionedData')
    pos_end = response_text.rfind('</PositionedData>') + len('</PositionedData>')
    
    if coord_start != -1 and coord_end > coord_start:
        xml_start = coord_start
        xml_end = coord_end
    elif pos_start != -1 and pos_end > pos_start:
        xml_start = pos_start
        xml_end = pos_end
    else:
        # Fallback to DynamicColumns if present
        xml_start = response_text.find('<DynamicColumns')
        xml_end = response_text.rfind('</DynamicColumns>') + len('</DynamicColumns>')
    
    if xml_start != -1 and xml_end > xml_start:
        xml_content = response_text[xml_start:xml_end]
    else:
        xml_content = response_text
    
    # Basic XML cleaning
    xml_content = xml_content.replace('&', '&amp;')
    xml_content = xml_content.replace('&amp;lt;', '&lt;')
    xml_content = xml_content.replace('&amp;gt;', '&gt;')
    
    return xml_content

def parse_coordinates_response(response_text):
    """Parse coordinates-only response"""
    try:
        clean_xml = clean_xml_response(response_text)
        root = ET.fromstring(clean_xml)
        
        result = {
            'boxes': []
        }
        
        # Extract boxes (rectangular areas)
        for box in root.findall('Box'):
            box_data = {
                'index': box.get('index', ''),
                'id': box.find('id').text if box.find('id') is not None else '',
                'x': int(box.find('x').text) if box.find('x') is not None else 0,
                'y': int(box.find('y').text) if box.find('y') is not None else 0,
                'width': int(box.find('width').text) if box.find('width') is not None else 0,
                'height': int(box.find('height').text) if box.find('height') is not None else 0
            }
            result['boxes'].append(box_data)
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to parse coordinates response: {str(e)}"}

def parse_positioned_data_response(response_text):
    """Parse positioned data response (columns and answer pairs only)"""
    try:
        clean_xml = clean_xml_response(response_text)
        root = ET.fromstring(clean_xml)
        
        result = {
            'columns': [],
            'answer_pairs': []
        }
        
        # Extract columns (sidebar options)
        for column in root.findall('Column'):
            heading = column.get('heading', '')
            items = [item.text for item in column.findall('Item') if item.text]
            result['columns'].append({
                'heading': heading,
                'items': items
            })
        
        # Extract answer pairs (without coordinates)
        answer_pairs_elem = root.find('AnswerPairs')
        if answer_pairs_elem is not None:
            for pair in answer_pairs_elem.findall('Pair'):
                for column in pair.findall('Column'):
                    pair_data = {
                        'name': column.get('name', ''),
                        'index': column.get('index', ''),
                        'id': column.get('id', ''),
                        'text': column.text or ''
                    }
                    result['answer_pairs'].append(pair_data)
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to parse positioned data response: {str(e)}"}

def process_coordinates_only(image_bytes: bytes) -> Dict[str, Any]:
    """
    Process BackgroundImage to extract only box coordinates.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        Dictionary containing only box coordinates or error information
    """
    try:
        prompt = get_coordinates_detection_prompt()
        ai_response = call_claude_api(image_bytes, prompt)
        result = parse_coordinates_response(ai_response)
        
        return result
            
    except Exception as e:
        return {"error": f"Error processing coordinates image: {str(e)}"}

def process_positioned_data_only(image_bytes: bytes) -> Dict[str, Any]:
    """
    Process PositionedImage to extract only columns and answer text.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        Dictionary containing columns and answer pairs (without coordinates) or error information
    """
    try:
        prompt = get_positioned_data_detection_prompt()
        ai_response = call_claude_api(image_bytes, prompt)
        result = parse_positioned_data_response(ai_response)
        
        return result
            
    except Exception as e:
        return {"error": f"Error processing positioned data image: {str(e)}"}

def process_positioned_dragdrop_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Process positioned drag-drop image and return structured data.
    This function processes the same image to extract both coordinates and positioned data.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        Dictionary containing complete positioned drag-drop data
    """
    try:
        # First extract coordinates
        coordinates_data = process_coordinates_only(image_bytes)
        
        if coordinates_data.get('error'):
            return coordinates_data
        
        # Then extract positioned data
        positioned_data = process_positioned_data_only(image_bytes)
        
        if positioned_data.get('error'):
            return positioned_data
        
        # Combine the results
        combined_data = {
            'columns': positioned_data.get('columns', []),
            'boxes': coordinates_data.get('boxes', []),
            'answer_pairs': []
        }
        
        # Match answer pairs with coordinates
        boxes = coordinates_data.get('boxes', [])
        answer_pairs = positioned_data.get('answer_pairs', [])
        
        for pair in answer_pairs:
            # Find matching box by index or id
            matching_box = None
            for box in boxes:
                if (box.get('index') == pair.get('index') or 
                    box.get('id') == pair.get('id')):
                    matching_box = box
                    break
            
            if matching_box:
                # Update pair with coordinates from matching box
                pair.update({
                    'x': matching_box.get('x'),
                    'y': matching_box.get('y'),
                    'width': matching_box.get('width'),
                    'height': matching_box.get('height')
                })
            
            combined_data['answer_pairs'].append(pair)
        
        return combined_data
            
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}