"""
Text processing utility functions for cleaning and extracting information from text.
"""

import re
from typing import List, Tuple, Optional

def clean_text(text: str) -> str:
    """
    Remove special characters and normalize whitespace.
    
    Args:
        text: The input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
        
    # Replace non-breaking spaces and other special characters
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    text = re.sub(r'\r', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_question_number(text: str) -> Optional[str]:
    """
    Extract question number from text.
    
    Args:
        text: The text to extract from
        
    Returns:
        Question number as string or None if not found
    """
    match = re.search(r'QUESTION NO:\s*(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def get_question_type(text: str) -> str:
    """
    Determine question type from text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Question type as string
    """

        # ABSOLUTE PRIORITY 1: Check for POSITIONEDDRAGDROP patterns FIRST
    positioneddragdrop_patterns = [
        r'POSITIONEDDRAGDROP',
        r'PositionedDragDrop',
        r'positioneddragdrop',
        r'Positioned DragDrop',
        r'QUESTION NO:\s*\d+\s+POSITIONEDDRAGDROP',
        r'QUESTION NO:\s*\d+\s+PositionedDragDrop',
    ]
    
    for pattern in positioneddragdrop_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "POSITIONEDDRAGDROP"


        # ABSOLUTE PRIORITY 1: Check for POSITIONEDDROPDOWN patterns FIRST
    positioneddropdown_patterns = [
        r'POSITIONEDDROPDOWN',
        r'PositionedDropdown',
        r'positioneddropdown',
        r'Positioned Dropdown',
        r'QUESTION NO:\s*\d+\s+POSITIONEDDROPDOWN',
        r'QUESTION NO:\s*\d+\s+PositionedDropdown',
    ]
    
    for pattern in positioneddropdown_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "POSITIONEDDROPDOWN"
    
    # ABSOLUTE PRIORITY: Check for FillInTheBlank patterns FIRST
    fillintheblank_patterns = [
        r'FillInTheBlank',
        r'FILLINTHEBLANK', 
        r'fillInTheBlank',
        r'Fill In The Blank',
        r'QUESTION NO:\s*\d+\s+FillInTheBlank',
        r'_{3,}',  # Multiple underscores indicating blanks
    ]
    
    for pattern in fillintheblank_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "FILLINTHEBLANK"
        

        # PRIORITY 2: Check for SIMULATION patterns
    simulation_patterns = [
        r'SIMULATION',
        r'Simulation',  
        r'simulation',
        r'QUESTION NO:\s*\d+\s+SIMULATION',
        r'QUESTION NO:\s*\d+\s+Simulation',
    ]
    
    for pattern in simulation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "SIMULATION"
        
        # First check for explicit type declaration
    type_match = re.search(r'QUESTION NO:\s*\d+\s*(\w+)', text, re.IGNORECASE)
    if type_match:
        declared_type = type_match.group(1).upper()
        # if declared_type in ["HOTSPOT", "DRAGDROP", "DROPDOWN", "RADIOBUTTON", "MULTIPLECHOICE","FillInTheBlank","SIMULATION","POSITIONEDDROPDOWN"]:

        if declared_type in ["HOTSPOT", "DRAGDROP", "DROPDOWN", "RADIOBUTTON", "MULTIPLECHOICE","FillInTheBlank","SIMULATION","POSITIONEDDROPDOWN"]:
            return declared_type
    
    # Check for patterns indicating HOTSPOT
    if re.search(r'\bhot\s*spot\b|\bselect\b.*\byes\b.*\bif\b|\bselect\b.*\bstatement\b.*\btrue\b', text, re.IGNORECASE):
        return "HOTSPOT"
    
    # Check for patterns indicating DRAGDROP
    if re.search(r'\bdrag\b.*\bdrop\b|\bmatch\b.*\bitem\b|\bdrag\b.*\bappropriate\b|\bcorrect\b\s+\bmatch\b', text, re.IGNORECASE):
        return "DRAGDROP"
    
    # Check for patterns indicating DROPDOWN
    if re.search(r'\bdrop\s*down\b|\bselect\b.*\bfrom\b.*\bmenu\b|\bcorrectly completes the sentence\b|\bselect the appropriate options? in the answer area\b', text, re.IGNORECASE):
        return "DROPDOWN"
    
    # Check for multiple choice options
    options = re.findall(r'^[A-Z]\.\s+', text, re.MULTILINE)
    answer_line = re.search(r'Answer:\s*([A-Z](?:,\s*[A-Z])*)', text)
    
    if options and answer_line:
        answers = [a.strip() for a in answer_line.group(1).split(',') if a.strip()]
        return "MultipleChoice" if len(answers) > 1 else "SingleChoice"
    
    # Default to RADIOBUTTON if no other type is detected
    return "SingleChoice"

def remove_noise(text: str) -> str:
    """
    Removes trailing noise from question descriptions,
    but preserves actual question content completely.
    SIMPLE APPROACH: Just remove the first line if it contains QUESTION NO:
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Split into lines
    lines = text.split('\n')
    
    # If first line contains "QUESTION NO:", remove it
    if lines and 'QUESTION NO:' in lines[0].upper():
        lines = lines[1:]  # Remove first line
    
    # Rejoin
    text = '\n'.join(lines)
    
    # Remove any "QuestionDescriptionImage:" markers
    text = re.sub(r'QuestionDescriptionImage:\s*', '', text, flags=re.DOTALL)
    
    # Remove any <map> tag and following content
    text = re.sub(r'<map>.*$', '', text, flags=re.DOTALL)
    
    # Remove choice options (A, B, C, etc.) from the description
    text = re.sub(r'(?:\n|\r|^)[A-F]\.\s+.*?(?=(?:\n|\r)[A-F]\.|(?:\n|\r)Answer:|$)', '', text, flags=re.DOTALL | re.MULTILINE)
    
    # Remove the References section from the description
    text = re.sub(r'(?:\n|\r|^)References:[\s\S]*?(?=QUESTION NO:|$)', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove trailing Answer: and Explanation: sections
    text = re.sub(r'\s*(Answer:[\s\S]*?|Explanation:[\s\S]*?)(?=References:|$)', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove any "PositionedImage:" markers
    text = re.sub(r'PositionedImage:\s*$', '', text, flags=re.DOTALL)

    # Remove ". JustDropDown:" and everything after it
    # text = re.sub(r'\s*BackgroundImage:\s*$', '', text)
    text = re.sub(r'BackgroundImage:\s*', '', text, flags=re.DOTALL)

    # Remove ". JustDropDown:" and everything after it
    text = re.sub(r'\s*JustDropDown:\s*$', '', text)

    # Remove ". QuestionOptionImage:" and everything after it
    text = re.sub(r'\s*QuestionOptionImage:\s*$', '', text)

    # Remove ". AnswerOptionImage:" and everything after it
    text = re.sub(r'\s*AnswerOptionImage:\s*$', '', text)

    # Remove " QuestionDescriptionImage: QuestionDescriptionImage:" and everything after it
    text = re.sub(r'\s*QuestionDescriptionImage:\s*QuestionDescriptionImage:\s*$', '', text)
    

    # Final cleanup: remove extra whitespace but preserve paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with single space
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
    text = text.strip()
    
    return text


def extract_options_from_text(text: str, q_type: str) -> Tuple[List[Tuple[str, str]], List[str], str]:
    """
    Extract options for RadioButton/MultipleChoice questions from text.
    
    Args:
        text: Question text
        q_type: Current question type
        
    Returns:
        Tuple containing:
            - List of (letter, option_text) tuples
            - List of correct answer letters
            - Updated question type (might be changed based on answer count)
    """
    options = []
    correct_answers = []
    
    if q_type in ["SingleChoice", "MultipleChoice"]:
        # Find option lines (A., B., etc.)
        option_matches = re.finditer(r'^([A-Z])\.\s+(.*?)$', text, re.MULTILINE)
        
        for match in option_matches:
            letter = match.group(1)
            opt_text = match.group(2).strip()
            options.append((letter, opt_text))
        
        # Find answer line
        answer_match = re.search(r'Answer:\s*([A-Z](?:,\s*[A-Z])*)', text)
        if answer_match:
            answer_text = answer_match.group(1)
            correct_answers = [a.strip() for a in answer_text.split(',') if a.strip()]
            
            # If there are multiple answers, update the question type to MULTIPLECHOICE
            if len(correct_answers) > 1:
                q_type = "MultipleChoice"
    
    return options, correct_answers, q_type