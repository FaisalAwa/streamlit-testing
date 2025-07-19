"""
Case Study processing classes for handling complex content grouping.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from .content_processor_base import BaseContentGrouper, ContentItem


class CaseStudyState:
    """Manages the state of case study processing."""
    
    def __init__(self):
        self.topic_number = ""
        self.case_study_number = ""
        self.topic_name = ""
        self.current_case_study = None
        self.current_segment_name = ""
        self.current_segment_contents = []
        self.in_case_study = False
        self.in_case_study_details = False
        self.next_image_is_case_study = False
    
    def reset(self):
        """Reset all state variables."""
        self.topic_number = ""
        self.case_study_number = ""
        self.topic_name = ""
        self.current_case_study = None
        self.current_segment_name = ""
        self.current_segment_contents = []
        self.in_case_study = False
        self.in_case_study_details = False
        self.next_image_is_case_study = False
    
    def start_case_study(self):
        """Start a new case study."""
        self.in_case_study = True
        self.current_case_study = {
            "topic_number": self.topic_number,
            "number": self.case_study_number,
            "topic_name": self.topic_name,
            "segments": [],
            "questions": [],
            "images": []
        }
    
    def finalize_current_segment(self):
        """Finalize current segment and add to case study."""
        if self.current_segment_name and self.current_segment_contents and self.current_case_study:
            self.current_case_study["segments"].append({
                "name": self.current_segment_name,
                "contents": self.current_segment_contents
            })
            self.current_segment_contents = []


class CaseStudyContentGrouper(BaseContentGrouper):
    """Groups content into questions and case studies."""
    
    def __init__(self):
        super().__init__()
        self.case_studies = []
        self.standalone_questions = []
        self.state = CaseStudyState()
    
    def process_content_items(self, content_items: List[ContentItem]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Group content items into questions and case studies.
        
        Returns:
            Tuple of (standalone_questions, case_studies)
        """
        for item in content_items:
            self._process_single_item(item)
        
        # Finalize any remaining content
        self._finalize_processing()
        
        return self.standalone_questions, self.case_studies
    
    def _process_single_item(self, item: ContentItem):
        """Process a single content item."""
        text = item.content
        
        # Check for various markers and handle accordingly
        if self._handle_case_study_markers(item, text):
            return
        
        if self._handle_question_markers(item, text):
            return
        
        if self._handle_case_study_content(item, text):
            return
        
        # Default: add to current question if exists
        if self.current_question:
            self._add_item_to_current_question(item)
    
    def _handle_case_study_markers(self, item: ContentItem, text: str) -> bool:
        """Handle case study-related markers. Returns True if handled."""
        
        # Topic and case study number
        topic_match = re.search(r'Topic\s+(\d+),\s+Case\s+Study\s+(\d+)', text)
        if topic_match:
            self.state.topic_number = topic_match.group(1)
            self.state.case_study_number = topic_match.group(2)
            return True
        
        # Topic name
        if "TopicName:" in text:
            self.state.topic_name = self._extract_topic_name(text)
            return True
        
        # Case study start
        if "CaseStudyStart:" in text:
            self.state.start_case_study()
            return True
        
        # Case study end
        if "CaseStudyEnd:" in text:
            self._finalize_case_study()
            return True
        
        # Case study details markers
        if "CaseStudyDetailsStart:" in text:
            self.state.in_case_study_details = True
            return True
        
        if "CaseStudyDetailsEnd:" in text:
            self.state.in_case_study_details = False
            self.state.next_image_is_case_study = False
            return True
        
        # Case study heading

        if self.state.in_case_study_details and "Segment:" in text and self.state.current_case_study:
            self._handle_case_study_heading(text)
            return True
        
        # Case study heading title
        if self.state.in_case_study_details and "Title:" in text and self.state.current_case_study and self.state.current_segment_name:
            self._handle_case_study_heading_title(text)
            return True
        
        # Case study image marker
        if "CaseStudyImage:" in text:
            self.state.next_image_is_case_study = True
            return True
        
        return False
    
    def _handle_question_markers(self, item: ContentItem, text: str) -> bool:
        """Handle question-related markers. Returns True if handled."""
        
        if item.has_question_start():
            # Finish the previous question
            self._finalize_current_question()
            
            # Create new question
            self.current_question = self._create_question_from_item(item)
            
            return True
        
        return False
    
    def _handle_case_study_content(self, item: ContentItem, text: str) -> bool:
        """Handle case study content. Returns True if handled."""
        
        # Handle case study images
        if self.state.next_image_is_case_study and item.images and self.state.current_case_study:
            self.state.current_case_study["images"].extend(item.images)
            
            if self.state.in_case_study_details and self.state.current_segment_name:
                for img in item.images:
                    self.state.current_segment_contents.append({
                        "type": "Image",
                        "image": img,
                        "is_answer_image": False
                    })
            
            self.state.next_image_is_case_study = False
            return True
        
        # Handle case study details content
        if self.state.in_case_study_details and self.state.current_case_study:
            if self.state.current_segment_name:
                if text.strip():
                    self.state.current_segment_contents.append({
                        "type": "Text",
                        "content": text.strip()
                    })
                return True
            elif text.strip():
                # Content before any heading - create default segment
                self.state.current_segment_name = "Introduction"
                self.state.current_segment_contents.append({
                    "type": "Text",
                    "content": text.strip()
                })
                return True
        
        return False
    
    def _extract_topic_name(self, text: str) -> str:
        """Extract topic name from text."""
        parts = text.split("TopicName:", 1)
        if len(parts) > 1:
            topic_content = parts[1].strip()
            if topic_content.startswith('"') and topic_content.endswith('"'):
                topic_content = topic_content[1:-1]
            return topic_content.strip()
        return ""
    
    def _handle_case_study_heading(self, text: str):
        """Handle case study heading marker."""
        # Finalize previous segment
        self.state.finalize_current_segment()
        
        # Extract new heading name
        heading_parts = text.split("Segment:", 1)
        if len(heading_parts) > 1:
            self.state.current_segment_name = heading_parts[1].strip()
    
    def _handle_case_study_heading_title(self, text: str):
        """Handle case study heading title marker."""
        title_parts = text.split("Title:", 1)
        if len(title_parts) > 1:
            title_content = title_parts[1].strip()
            self.state.current_segment_contents.append({
                "type": "Title",
                "content": title_content
            })
    
    def _finalize_case_study(self):
        """Finalize current case study."""
        # Add current question to case study if exists
        if self.current_question and self.state.in_case_study and self.state.current_case_study:
            question_numbers = [q["number"] for q in self.state.current_case_study["questions"]]
            if self.current_question["number"] not in question_numbers:
                self.state.current_case_study["questions"].append(self.current_question)
            self.current_question = None
        
        if self.state.current_case_study:
            # Finalize any remaining segment
            self.state.finalize_current_segment()
            
            # Add to case studies list
            self.case_studies.append(self.state.current_case_study)
            
            # Debug print
            cs = self.state.current_case_study
            # print(f"Case Study: Topic {cs['topic_number']}, Case {cs['number']}, TopicName: {cs.get('topic_name', 'MISSING')}")
            # print(f"  Segments: {len(cs['segments'])}")
            # print(f"  Questions: {len(cs['questions'])}")
        
        self.state.reset()
    
    def _finalize_processing(self):
        """Finalize any remaining content."""
        # Add final question
        if self.current_question:
            if self.state.in_case_study and self.state.current_case_study:
                self.state.current_case_study["questions"].append(self.current_question)
            else:
                self.standalone_questions.append(self.current_question)
        
        # Add final case study
        if self.state.current_case_study:
            self.state.finalize_current_segment()
            self.case_studies.append(self.state.current_case_study)
    
    def _finalize_current_question(self):
        """Override to handle case study vs standalone questions."""
        if self.current_question:
            if self.state.in_case_study and self.state.current_case_study:
                self.state.current_case_study["questions"].append(self.current_question)
            else:
                self.standalone_questions.append(self.current_question)
            self.current_question = None


