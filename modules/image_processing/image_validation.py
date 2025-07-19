"""
Module for validating question content before processing.
"""

from typing import List, Dict, Any, Tuple

def validate_question_images(questions: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate that all questions have the required images according to their type.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of error messages
    """
    all_valid = True
    error_messages = []
    
    for question in questions:
        q_number = question.get("number", "Unknown")
        q_type = question.get("type", "Unknown")
        content_items = question.get("content_items", [])
        text = question.get("text", "")
        images = question.get("images", [])
        
        # Extract image markers from content_items and text
        image_markers = {}
        
        # First check content_items
        for item in content_items:
            content = item.get("content", "")
            
            if "QuestionOptionImage:" in content:
                image_markers["QuestionOptionImage"] = True
            
            if "AnswerOptionImage:" in content:
                image_markers["AnswerOptionImage"] = True
            
            if "QuestionDescriptionImage:" in content:
                image_markers["QuestionDescriptionImage"] = True
            
            if "PositionedImage:" in content:  # ← Add this marker check
                image_markers["PositionedImage"] = True

            if "BackgroundImage:" in content:  # ← Add this marker check
                image_markers["BackgroundImage"] = True     

            # if "JustCoordinates:" in content:  # ← Add this marker check
            #     image_markers["JustCoordinates"] = True          
        
        # Also check text content
        if "QuestionOptionImage:" in text:
            image_markers["QuestionOptionImage"] = True
        
        if "AnswerOptionImage:" in text:
            image_markers["AnswerOptionImage"] = True
        
        if "QuestionDescriptionImage:" in text:
            image_markers["QuestionDescriptionImage"] = True

        if "PositionedImage:" in text:  # ← Add this marker check
            image_markers["PositionedImage"] = True

        if "BackgroundImage:" in text:  # ← Add this marker check
            image_markers["BackgroundImage"] = True

        # if "JustCoordinates:" in text:  # ← Add this marker check
        #     image_markers["JustCoordinates"] = True
        
        # Validate based on question type
        if q_type == "HOTSPOT":
            # HOTSPOT questions require QuestionOptionImage and AnswerOptionImage
            if "QuestionOptionImage" not in image_markers:
                error_messages.append(f"Question {q_number} (HOTSPOT) - Missing QuestionOptionImage")
                all_valid = False
            
            if "AnswerOptionImage" not in image_markers:
                error_messages.append(f"Question {q_number} (HOTSPOT) - Missing AnswerOptionImage")
                all_valid = False
        
        elif q_type == "DRAGDROP":
            # DRAGDROP questions require QuestionOptionImage and AnswerOptionImage
            if "QuestionOptionImage" not in image_markers:
                error_messages.append(f"Question {q_number} (DRAGDROP) - Missing QuestionOptionImage")
                all_valid = False
            
            if "AnswerOptionImage" not in image_markers:
                error_messages.append(f"Question {q_number} (DRAGDROP) - Missing AnswerOptionImage")
                all_valid = False
        
        elif q_type == "DROPDOWN":

            if "QuestionOptionImage" not in image_markers:
                error_messages.append(f"Question {q_number} (DROPDOWN Type 1) - Missing QuestionOptionImage")
                all_valid = False
                
            if "AnswerOptionImage" not in image_markers:
                error_messages.append(f"Question {q_number} (DROPDOWN Type 1) - Missing AnswerOptionImage")
                all_valid = False
        
        elif q_type == "POSITIONEDDROPDOWN":  # ← Add validation for new question type

            if "BackgroundImage" not in image_markers:
                error_messages.append(f"Question {q_number} (POSITIONEDDROPDOWN) - Missing PositionedImage")
                all_valid = False
            
            if "PositionedImage" not in image_markers:
                error_messages.append(f"Question {q_number} (POSITIONEDDROPDOWN) - Missing PositionedImage")
                all_valid = False
            

        elif q_type == "POSITIONEDDRAGDROP":  # ← Add validation for new question type

            if "BackgroundImage" not in image_markers:
                error_messages.append(f"Question {q_number} (POSITIONEDDRAGDROP) - Missing BackgroundImage")
                all_valid = False

            # if "JustCoordinates" not in image_markers:
            #     error_messages.append(f"Question {q_number} (POSITIONEDDRAGDROP) - Missing JustCoordinates")
            #     all_valid = False

            
            if "PositionedImage" not in image_markers:
                error_messages.append(f"Question {q_number} (POSITIONEDDRAGDROP) - Missing PositionedImage")
                all_valid = False  
    
    return all_valid, error_messages

def validate_case_study_questions(case_studies: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate that all questions in case studies have the required images.
    
    Args:
        case_studies: List of case study dictionaries
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of error messages
    """
    all_valid = True
    error_messages = []
    
    for case_study in case_studies:
        cs_number = f"{case_study.get('topic_number', 'Unknown')}-{case_study.get('number', 'Unknown')}"
        
        # Validate each question in the case study
        valid, errors = validate_question_images(case_study.get("questions", []))
        
        if not valid:
            all_valid = False
            error_messages.append(f"Case Study {cs_number} contains invalid questions:")
            error_messages.extend([f"  {error}" for error in errors])
            error_messages.append("")  # Add blank line for readability
    
    return all_valid, error_messages