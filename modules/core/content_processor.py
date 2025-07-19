"""
Updated content processor using OOP approach.
"""

from typing import List, Dict, Any, Tuple
from modules.core.content_processor_base import ODTExtractor, SimpleQuestionGrouper
from modules.core.case_study_processor import CaseStudyContentGrouper
from modules.utils.content_statistics import ContentStatistics, ContentUtilities


class ContentProcessor:
    """Main content processor that orchestrates all content processing."""
    
    def __init__(self):
        self.extractor = ODTExtractor()
        self.statistics = ContentStatistics()
        self.utilities = ContentUtilities()
    
    def extract_content_from_odt(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract content from ODT file in sequential order.
        
        Args:
            file_bytes: The ODT file as bytes
            
        Returns:
            List of content items (backward compatible format)
        """
        content_items = self.extractor.extract_content_from_odt(file_bytes)
        # Convert to backward compatible format
        return [item.to_dict() for item in content_items]
    
    def group_content_into_questions(self, content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group content items into questions based on "QUESTION NO:" markers.
        
        Args:
            content_items: List of content item dictionaries
            
        Returns:
            List of question dictionaries
        """
        # Convert dicts back to ContentItem objects
        from modules.core.content_processor_base import ContentItem
        content_objects = [
            ContentItem(
                item.get("type", "text"),
                item.get("content", ""),
                item.get("frame_refs", []),
                item.get("images", [])
            )
            for item in content_items
        ]
        
        grouper = SimpleQuestionGrouper()
        return grouper.process_content_items(content_objects)
    
    def group_content_into_questions_and_case_studies(self, content_items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Group content items into questions and case studies based on markers.
        
        Args:
            content_items: List of content item dictionaries
            
        Returns:
            Tuple of (standalone_questions, case_studies)
        """
        # Convert dicts back to ContentItem objects
        from modules.core.content_processor_base import ContentItem
        content_objects = [
            ContentItem(
                item.get("type", "text"),
                item.get("content", ""),
                item.get("frame_refs", []),
                item.get("images", [])
            )
            for item in content_items
        ]
        
        grouper = CaseStudyContentGrouper()
        return grouper.process_content_items(content_objects)
    
    def get_question_stats(self, questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, Dict[str, int]]:
        """Generate statistics about questions."""
        return self.statistics.get_question_stats(questions)
    
    def check_missing_images(self, standalone_questions: List[Dict[str, Any]], case_studies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Check for missing images in questions and case studies."""
        return self.statistics.check_missing_images(standalone_questions, case_studies)
    
    def process_case_study_headings(self, text: str) -> str:
        """Process case study headings in text."""
        return self.utilities.process_case_study_headings(text)


# Backward compatibility - create global instance and expose functions
_processor = ContentProcessor()

def extract_content_from_odt(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Backward compatible function."""
    return _processor.extract_content_from_odt(file_bytes)

def group_content_into_questions(content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Backward compatible function."""
    return _processor.group_content_into_questions(content_items)

def group_content_into_questions_and_case_studies(content_items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Backward compatible function."""
    return _processor.group_content_into_questions_and_case_studies(content_items)

def get_question_stats(questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, Dict[str, int]]:
    """Backward compatible function."""
    return _processor.get_question_stats(questions)

def check_missing_images(standalone_questions: List[Dict[str, Any]], case_studies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Backward compatible function."""
    return _processor.check_missing_images(standalone_questions, case_studies)

def process_case_study_headings(text: str) -> str:
    """Backward compatible function."""
    return _processor.process_case_study_headings(text)