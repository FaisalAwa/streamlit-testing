"""
Statistics and utility classes for content processing.
"""

from typing import List, Dict, Any, Tuple


class ContentStatistics:
    """Handles statistics generation for processed content."""
    
    @staticmethod
    def get_question_stats(questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, Dict[str, int]]:
        """
        Generate statistics about questions and their images.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Tuple containing:
                - List of question stats
                - Total image count
                - Dictionary of question type counts
        """
        stats = []
        total_images = 0
        question_types = {
            "HOTSPOT": 0,
            "DRAGDROP": 0,
            "DROPDOWN": 0,
            "RADIOBUTTON": 0,
            "MULTIPLECHOICE": 0
        }
        
        for q in questions:
            q_num = q["number"]
            q_type = q["type"]
            img_count = len(q["images"])
            
            # Update type count
            if q_type in question_types:
                question_types[q_type] += 1
            
            # Update total image count
            total_images += img_count
            
            # Add to stats
            stats.append({
                "Question": q_num,
                "Type": q_type,
                "Images": img_count
            })
        
        # Sort by question number
        stats.sort(key=lambda x: int(x["Question"]) if str(x["Question"]).isdigit() else x["Question"])
        
        return stats, total_images, question_types
    
    @staticmethod
    def check_missing_images(standalone_questions: List[Dict[str, Any]], case_studies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check for missing images in questions and case studies.
        
        Args:
            standalone_questions: List of standalone question dictionaries
            case_studies: List of case study dictionaries
            
        Returns:
            Dictionary with missing image information
        """
        missing_images = {
            "standalone_questions": [],
            "case_studies": []
        }
        
        # Check standalone questions
        ContentStatistics._check_questions_for_missing_images(
            standalone_questions, 
            missing_images["standalone_questions"]
        )
        
        # Check case study questions
        ContentStatistics._check_case_studies_for_missing_images(
            case_studies, 
            missing_images["case_studies"]
        )
        
        return missing_images
    
    @staticmethod
    def _check_questions_for_missing_images(questions: List[Dict[str, Any]], missing_list: List[Dict[str, Any]]):
        """Check individual questions for missing images."""
        for question in questions:
            q_number = question.get("number", "Unknown")
            q_type = question.get("type", "Unknown")
            content_items = question.get("content_items", [])
            
            # Debug print
            # print(f"Question {q_number} - Type: {q_type}")
            # print(f"Content Items Count: {len(content_items)}")
            
            # Check for required image markers
            ContentStatistics._check_image_markers(question, content_items)
            
            # Check question images
            images = question.get("images", [])
            if not images:
                missing_list.append({
                    "number": q_number,
                    "type": q_type,
                    "message": f"Question {q_number} ({q_type}) has no images at all."
                })
            # else:
            #     print(f"  Question has {len(images)} images")
    
    @staticmethod
    def _check_case_studies_for_missing_images(case_studies: List[Dict[str, Any]], missing_list: List[Dict[str, Any]]):
        """Check case study questions for missing images."""
        for case_study in case_studies:
            cs_number = f"{case_study.get('topic_number', 'Unknown')}-{case_study.get('number', 'Unknown')}"
            questions = case_study.get("questions", [])
            
            # print(f"Case Study {cs_number}")
            # print(f"Questions Count: {len(questions)}")
            
            for question in questions:
                q_number = question.get("number", "Unknown")
                q_type = question.get("type", "Unknown")
                content_items = question.get("content_items", [])
                
                # print(f"  Case Study Question {q_number} - Type: {q_type}")
                # print(f"  Content Items Count: {len(content_items)}")
                
                # Check for required image markers
                ContentStatistics._check_image_markers(question, content_items)
                
                # Check question images
                images = question.get("images", [])
                if not images:
                    missing_list.append({
                        "case_study": cs_number,
                        "question": q_number,
                        "type": q_type,
                        "message": f"Case Study {cs_number}, Question {q_number} ({q_type}) has no images at all."
                    })
                # else:
                #     print(f"  Question has {len(images)} images")
    
    @staticmethod
    def _check_image_markers(question: Dict[str, Any], content_items: List[Dict[str, Any]]):
        """Check for specific image markers in question content."""
        has_question_option = any("QuestionOptionImage:" in item.get("content", "") for item in content_items)
        has_answer_option = any("AnswerOptionImage:" in item.get("content", "") for item in content_items)
        has_just_dropdown = any("JustDropDown:" in item.get("content", "") for item in content_items)
        
        # print(f"  Has QuestionOptionImage marker: {has_question_option}")
        # print(f"  Has AnswerOptionImage marker: {has_answer_option}")
        # print(f"  Has JustDropDown marker: {has_just_dropdown}")


class ContentUtilities:
    """Utility functions for content processing."""
    
    @staticmethod
    def process_case_study_headings(text: str) -> str:
        """
        Process CaseStudyHeading markers in text and convert them to XML-style tags.
        
        Args:
            text: Raw text with CaseStudyHeading: markers
            
        Returns:
            Text with <CaseStudyHeading> tags
        """
        # Split the text by CaseStudyHeading: markers
        parts = text.split("CaseStudyHeading:")
        
        if len(parts) <= 1:  # No headings found
            return text
        
        # First part is text before any heading
        result = parts[0]
        
        # Process each heading and its content
        for i in range(1, len(parts)):
            part = parts[i].strip()
            if not part:
                continue
                
            # Split the heading title from its content
            lines = part.split("\n", 1)
            heading_title = lines[0].strip()
            
            result += f"<CaseStudyHeading>{heading_title}</CaseStudyHeading>\n"
            
            # Add the content if any
            if len(lines) > 1:
                result += lines[1] + "\n"
        
        return result