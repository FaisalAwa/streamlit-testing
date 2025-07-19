"""
Updated module for processing different question types using OOP approach.
"""

import xml.etree.ElementTree as ET
import streamlit as st
from typing import List, Dict, Any
import re

from modules.questions.question_factory import QuestionFactory

def process_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process all questions and generate XML using OOP approach.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        List of processed question dictionaries with XML elements
    """
    results = []
    
    for question_data in questions:
        q_number = question_data["number"]
        q_type = question_data["type"]
        
        try:
            # Handle type updates for text-based questions
            if q_type in ["SingleChoice", "MultipleChoice"]:
                from modules.utils.text_helpers import extract_options_from_text
                options, correct_answers, updated_q_type = extract_options_from_text(question_data["text"], q_type)
                
                if updated_q_type != q_type:
                    q_type = updated_q_type
                    question_data["type"] = q_type
            
            # Create appropriate question object using factory
            question_obj = QuestionFactory.create_question(question_data)
            
            # Generate XML using the object's method
            xml_element = question_obj.build_xml()
            
            results.append({
                "number": q_number,
                "type": q_type,
                "element": xml_element
            })
            
        except Exception as e:
            st.error(f"Error processing question {q_number}: {str(e)}")
            # Create a basic fallback XML structure
            fallback_elem = ET.Element("Question")
            ET.SubElement(fallback_elem, "QuestionNo").text = str(q_number)
            ET.SubElement(fallback_elem, "Kind").text = str(q_type)
            ET.SubElement(fallback_elem, "Error").text = str(e)
            
            results.append({
                "number": q_number,
                "type": q_type,
                "element": fallback_elem
            })
    
    return results

def process_case_study_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process questions in a case study and generate XML elements.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        List of processed question dictionaries with XML elements
    """
    # Reuse the process_questions function since the logic is the same
    return process_questions(questions)

def fix_case_study_details_tags(xml_string):
    """
    Fix the CaseStudyDetails section to ensure embedded CaseStudyHeading tags are preserved.
    
    Args:
        xml_string: XML string with escaped tags
        
    Returns:
        XML string with proper embedded tags
    """
    # Replace escaped angle brackets in the CaseStudyDetails section
    # The pattern looks for content between <CaseStudyDetails> and </CaseStudyDetails>
    pattern = r'(<CaseStudyDetails>)(.*?)(</CaseStudyDetails>)'
    
    def replace_escaped_tags(match):
        opening_tag = match.group(1)
        content = match.group(2)
        closing_tag = match.group(3)
        
        # Unescape the XML tags within the content
        content = content.replace("&lt;", "<").replace("&gt;", ">")
        
        return opening_tag + content + closing_tag
    
    # Use re.DOTALL to make . match newlines as well
    xml_string = re.sub(pattern, replace_escaped_tags, xml_string, flags=re.DOTALL)
    
    return xml_string

def build_xml_for_case_study(case_study: Dict[str, Any]) -> ET.Element:
    """
    Build XML element for a case study without including questions.
    
    Args:
        case_study: Case study dictionary
        
    Returns:
        XML Element for the case study (without questions)
    """
    root = ET.Element("CaseStudy")
    
    # Add Number (was TopicNumber)
    ET.SubElement(root, "Number").text = case_study.get("topic_number", "")
    
    # Add Name (was TopicName) - without quotes
    topic_name = case_study.get("topic_name", "")
    name_elem = ET.SubElement(root, "Name")
    name_elem.text = topic_name
    
    # Process each segment
    for segment in case_study.get("segments", []):
        segment_elem = ET.SubElement(root, "Segments")
        
        # Add segment name
        name_elem = ET.SubElement(segment_elem, "Name")
        name_elem.text = segment["name"]
        
        # Add each content item in the segment
        for content_item in segment.get("contents", []):
            content_elem = ET.SubElement(segment_elem, "Contents")
            
            # Add content type (Text or Image or Title)
            content_type_elem = ET.SubElement(content_elem, "ContentType")
            content_type_elem.text = content_item["type"]
            
            if content_item["type"] == "Text":
                # Add text content
                text_elem = ET.SubElement(content_elem, "Text")
                text_elem.text = content_item["content"]
            elif content_item["type"] == "Title":
                # Add title content as text
                text_elem = ET.SubElement(content_elem, "Text")
                text_elem.text = content_item["content"]
            elif content_item["type"] == "Image":
                # Add image content
                img = content_item["image"]
                img_data = img["data"]
                
                # Encode image to base64
                import base64
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                
                # Add to XML
                img_elem = ET.SubElement(content_elem, "Image")
                img_elem.text = img_base64
                
                # Add IsAnswerImage flag
                is_answer_elem = ET.SubElement(content_elem, "IsAnswerImage")
                is_answer_elem.text = "false"
    
    return root

def build_testlets_xml(standalone_questions, case_studies):
    """
    Build the complete Testlets XML.
    
    Args:
        standalone_questions: List of standalone questions
        case_studies: List of case studies
        
    Returns:
        XML string for Testlets
    """
    root = ET.Element("Testlets")
    
    # Process each case study
    for case_study in case_studies:
        # Get the case study element (without questions)
        case_study_elem = build_xml_for_case_study(case_study)
        
        # Add case study element as a direct child of Testlets
        root.append(case_study_elem)
        
        # Process questions from this case study
        if case_study["questions"]:
            results = process_case_study_questions(case_study["questions"])
            
            # Sort results by question number for consistent output
            results.sort(key=lambda x: int(x["number"]) if x["number"].isdigit() else x["number"])
            
            # Add all question elements as direct children of Testlets
            for result in results:
                root.append(result["element"])
    
    # Process standalone questions (if any)
    if standalone_questions:
        results = process_questions(standalone_questions)
        
        # Sort results by question number for consistent output
        results.sort(key=lambda x: int(x["number"]) if x["number"].isdigit() else x["number"])
        
        # Add each standalone question
        for result in results:
            root.append(result["element"])
    
    # Convert to string
    return ET.tostring(root, encoding='utf-8').decode('utf-8')