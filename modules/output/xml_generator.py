"""
Module for generating XML output from processed questions and case studies.
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from typing import List, Dict, Any

from modules.questions.question_processors import (
    process_questions,
    process_case_study_questions,
    build_xml_for_case_study,
    fix_case_study_details_tags
)

def generate_xml_output(standalone_questions: List[Dict[str, Any]], case_studies: List[Dict[str, Any]]) -> str:
    """
    Generate XML output with separate testlets for each case study and a final testlet for standalone questions.
    
    Args:
        standalone_questions: List of standalone question dictionaries
        case_studies: List of case study dictionaries
        
    Returns:
        Pretty-formatted XML string
    """
    # Create root element for the collection
    root = ET.Element("root")
    
    # Add metadata elements
    ET.SubElement(root, "Id").text = ""
    ET.SubElement(root, "Code").text = ""
    ET.SubElement(root, "Name").text = ""
    ET.SubElement(root, "VendorName").text = ""
    
    # Count total questions for QuestionsPerExam
    questions_count = len(standalone_questions)
    if case_studies:
        for cs in case_studies:
            questions_count += len(cs.get("questions", []))
    
    ET.SubElement(root, "QuestionsPerExam").text = str(questions_count)
    ET.SubElement(root, "Version").text = ""
    ET.SubElement(root, "AllowedTime").text = ""
    ET.SubElement(root, "MaxScore").text = ""
    ET.SubElement(root, "RequiredScore").text = ""
    ET.SubElement(root, "SchemaVersion").text = ""
    ET.SubElement(root, "Sections").text = ""
    
    # Sort case studies by topic and number
    if case_studies:
        case_studies.sort(key=lambda x: (
            int(x.get("topic_number", "0")) if x.get("topic_number", "").isdigit() else x.get("topic_number", ""), 
            int(x.get("number", "0")) if x.get("number", "").isdigit() else x.get("number", "")
        ))
    
    # Create separate testlet for each case study
    for case_study in case_studies:
        # Create a new Testlets element for this case study
        testlet = ET.SubElement(root, "Testlets")
        
        # Add the case study element to this testlet
        case_study_elem = build_xml_for_case_study(case_study)
        testlet.append(case_study_elem)
        
        # Process questions from this case study
        if case_study["questions"]:
            results = process_case_study_questions(case_study["questions"])
            
            # Sort results by question number for consistent output
            results.sort(key=lambda x: int(x["number"]) if x["number"].isdigit() else x["number"])
            
            # Add each question to the same testlet (but not inside the case study element)
            for result in results:
                testlet.append(result["element"])
    
    # Create a separate testlet for standalone questions
    if standalone_questions:
        standalone_testlet = ET.SubElement(root, "Testlets")
        
        # Process questions to get XML elements
        results = process_questions(standalone_questions)
        
        # Sort results by question number for consistent output
        results.sort(key=lambda x: int(x["number"]) if x["number"].isdigit() else x["number"])
        
        # Add each question directly to the standalone testlet
        for result in results:
            standalone_testlet.append(result["element"])
    
    # Convert to string with pretty formatting
    xml_string = ET.tostring(root, encoding='utf-8')
    
    # Create a pretty-formatted XML with minidom
    xml_pretty = minidom.parseString(xml_string).toprettyxml(indent="  ")
    
    # Post-processing to ensure embedded tags are preserved
    xml_pretty = fix_case_study_details_tags(xml_pretty)
    
    return xml_pretty

