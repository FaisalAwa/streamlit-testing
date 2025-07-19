"""
Base class for all question types - provides common XML building functionality.
"""

from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import base64
import re
from typing import Dict, List, Any

class BaseQuestion(ABC):
    def __init__(self, question_data: Dict[str, Any]):
        self.number = question_data["number"]
        self.type = question_data["type"]
        self.text = question_data["text"]
        self.images = question_data.get("images", [])
        self.content_items = question_data.get("content_items", [])
    
    def build_xml(self) -> ET.Element:
        """Main XML building method - calls other methods in order"""
        root = ET.Element("Question")
        
        # Common elements for all questions
        self._add_basic_elements(root)
        
        # MODIFIED: Add content and images in sequential order
        self._add_sequential_content(root)
        
        # Question-specific elements (implemented by subclasses)
        self._add_question_specific_elements(root)
        
        # Common ending elements
        self._add_id_element(root)
        self._add_explanation(root)
        
        return root
    
    def _add_basic_elements(self, root: ET.Element):
        """Add Kind, DisplayKind, QuestionNo - same for all"""
        ET.SubElement(root, "Kind").text = self.get_xml_kind()
        ET.SubElement(root, "DisplayKind").text = self.get_xml_kind()
        ET.SubElement(root, "QuestionNo").text = str(self.number)
    
    # def _add_sequential_content(self, root: ET.Element):
    #     """Add text and images in sequential order based on content_items - WITH DEBUG"""
    #     print(f"\n=== BaseQuestion._add_sequential_content DEBUG for Question {self.number} ===")
        
    #     if not self.content_items:
    #         print("❌ No content_items, using fallback")
    #         self._add_description_contents(root)
    #         self._add_description_images(root)
    #         return
        
    #     print(f"✅ Found {len(self.content_items)} content_items")
    #     image_types = self._get_image_types()
    #     print(f"Image types: {image_types}")
        
    #     description_images_added = 0
        
    #     for i, item in enumerate(self.content_items):
    #         item_text = item.get("content", "").strip()
    #         item_images = item.get("images", [])
            
    #         print(f"\n--- Item {i} ---")
    #         print(f"Text: '{item_text}'")
    #         print(f"Images: {len(item_images)}")
            
    #         # Add text content if present
    #         if item_text:
    #             clean_text = self._clean_item_text(item_text)
    #             print(f"Clean text: '{clean_text}'")
    #             if clean_text:
    #                 contents = ET.SubElement(root, "Contents")
    #                 ET.SubElement(contents, "ContentType").text = "Text"
    #                 ET.SubElement(contents, "Text").text = clean_text
    #                 print(f"✅ Added text content")
            
    #         # Add images that appear after this text
    #         if item_images:
    #             for j, img in enumerate(item_images):
    #                 img_path = img.get("path", "")
    #                 img_type = image_types.get(img_path, "description")
    #                 img_size = len(img.get("data", b""))
                    
    #                 print(f"  Image {j}: path='{img_path}', type='{img_type}', size={img_size}")
                    
    #                 if img_type == "description":
    #                     print(f"  ✅ ADDING DESCRIPTION IMAGE")
    #                     self._add_image_content(root, img, is_answer=False)
    #                     description_images_added += 1
    #                 else:
    #                     print(f"  ⏭️ Skipping (not description)")
        
    #     print(f"\n📊 SUMMARY: Added {description_images_added} description images")
    #     print(f"=== END BaseQuestion._add_sequential_content DEBUG ===\n")


    def _add_sequential_content(self, root: ET.Element):
        """Add text and images in sequential order based on content_items"""
        if not self.content_items:
            # Fallback to original behavior if no content_items
            self._add_description_contents(root)
            self._add_description_images(root)
            return
        
        image_types = self._get_image_types()
        
        for item in self.content_items:
            item_text = item.get("content", "").strip()
            item_images = item.get("images", [])
            
            # Add text content if present
            if item_text:
                clean_text = self._clean_item_text(item_text)
                if clean_text:
                    contents = ET.SubElement(root, "Contents")
                    ET.SubElement(contents, "ContentType").text = "Text"
                    ET.SubElement(contents, "Text").text = clean_text
            
            # Add images that appear after this text
            if item_images:
                for img in item_images:
                    img_type = image_types.get(img.get("path", ""), "description")
                    
                    # Handle different image types
                    if img_type == "description":
                        self._add_image_content(root, img, is_answer=False, is_background=False)
                    elif img_type == "background":  # ← ADD THIS NEW CONDITION
                        self._add_image_content(root, img, is_answer=False, is_background=True)

    
    def _clean_item_text(self, text: str) -> str:
        """Clean and filter text content - UPDATED to handle POSITIONEDDROPDOWN"""
        # Remove markers - UPDATED to include PositionedImage
        text = re.sub(r'(QuestionDescriptionImage:|BackgroundImage:|PositionedImage:|QuestionOptionImage:|AnswerOptionImage:|JustDropDown:|CaseStudyImage:)\s*', '', text)
        
        # Remove question headers
        text = re.sub(r'^\s*QUESTION NO:\s*\d+.*?\n?', '', text, flags=re.IGNORECASE)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Skip answer content
        if self._is_answer_content(text):
            return ""
        
        # Skip question type duplicates
        if self._is_question_type_duplicate(text):
            return ""
        
        # Skip explanation duplicates (content that's meant for explanation section)
        if self._is_explanation_duplicate(text):
            return ""
        
        # Replace underscores with [blank]
        text = self._replace_blanks_with_keyword(text)
        
        return text
    
    def _is_answer_content(self, text: str) -> bool:
        """Check if text contains answer information - UPDATED to filter URLs"""
        text_lower = text.lower().strip()
        
        # Skip answer-related content
        if (text_lower.startswith('answer:') or 
            'choices' in text_lower):
            return True
        
        # Skip option choices (A. B. C. D. format) - they belong in Choices section
        if re.match(r'^[A-Z]\.', text.strip()):
            return True
        
        # Skip explanation content
        if text_lower.startswith('explanation:'):
            return True
        
        # Skip URLs (they should only appear in Explanation section) - UPDATED patterns
        url_patterns = [
            r'https://[^\s\)]+',    # Standard URLs
            r'https:[^\s\)]+',      # Malformed URLs without double slash
            r'www\.[^\s\)]+\.[a-zA-Z]{2,}',  # www URLs
        ]
        
        for pattern in url_patterns:
            if re.search(pattern, text):
                return True
                
        return False
    
    def _is_question_type_duplicate(self, text: str) -> bool:
        """Check if text is just the question type (like 'FillInTheBlank')"""
        text_clean = text.strip()
        question_types = [
            'FillInTheBlank', 
            'MultipleChoice', 
            'TrueFalse', 
            'SingleChoice',
            'MultipleSelect',
            'DropDown',
            'DragDrop', 
            'Hotspot',
            'Simulation',
            'DROPDOWN',
            'DRAGDROP', 
            'HOTSPOT',
            'SIMULATION',
            'POSITIONEDDROPDOWN',  # Add this
            'PositionedDropDown',   # Add this too
            'POSITIONEDDRAGDROP',
            'POSITIONEDDragDrop'
        ]
        return text_clean in question_types
    
    def _replace_blanks_with_keyword(self, text: str) -> str:
        """Replace underscores with [blank] keyword"""
        # Replace multiple underscores (2 or more) with [blank]
        text = re.sub(r'_{2,}', '[blank]', text)
        return text
    
    def _is_explanation_duplicate(self, text: str) -> bool:
        """Check if text is explanation content that should not appear in main Contents"""
        # Get the explanation section to compare
        explanation_text = self._extract_explanation()
        if explanation_text and text.strip() in explanation_text:
            return True
        return False
    
    def _add_description_contents(self, root: ET.Element):
        """Add text paragraphs as Contents - same for all (fallback method)"""
        clean_desc = self._clean_description()
        paragraphs = [p.strip() for p in clean_desc.split('\n') if p.strip()]
        
        for paragraph in paragraphs:
            contents = ET.SubElement(root, "Contents")
            ET.SubElement(contents, "ContentType").text = "Text"
            ET.SubElement(contents, "Text").text = paragraph
    
    def _add_description_images(self, root: ET.Element):
        """Add description images - same for all (fallback method)"""
        desc_images = self._get_description_images()
        for img in desc_images:
            self._add_image_content(root, img, is_answer=False)
    
    # def _add_image_content(self, root: ET.Element, img_data: Dict, is_answer: bool = False):
    #     """Helper method to add image content to XML"""
    #     contents = ET.SubElement(root, "Contents")
    #     ET.SubElement(contents, "ContentType").text = "Image"
        
    #     # Encode image to base64
    #     img_base64 = base64.b64encode(img_data["data"]).decode('utf-8')
    #     ET.SubElement(contents, "Image").text = img_base64
        
    #     # Add IsAnswerImage flag
    #     ET.SubElement(contents, "IsAnswerImage").text = str(is_answer).lower()

    def _add_image_content(self, root: ET.Element, img_data: Dict, is_answer: bool = False, is_background: bool = False):
        """Helper method to add image content to XML"""
        contents = ET.SubElement(root, "Contents")
        
        # Set ContentType based on image type
        if is_background:
            ET.SubElement(contents, "ContentType").text = "BImage"  # ← NEW: Background image type
        else:
            ET.SubElement(contents, "ContentType").text = "Image"   # ← EXISTING: Regular image type
        
        # Encode image to base64
        img_base64 = base64.b64encode(img_data["data"]).decode('utf-8')
        ET.SubElement(contents, "Image").text = img_base64
        
        # Add IsAnswerImage flag
        ET.SubElement(contents, "IsAnswerImage").text = str(is_answer).lower()
    
    def _add_id_element(self, root: ET.Element):
        """Add Id element - same for all"""
        ET.SubElement(root, "Id").text = ""
    
    def _add_explanation(self, root: ET.Element):
        """Add explanation section - WITH DEBUG"""
        # print(f"\n=== _add_explanation DEBUG for Question {self.number} ===")
        
        explanation_text = self._extract_explanation()
        references = self._extract_references()
        
        # print(f"Explanation text: '{explanation_text}'")
        # print(f"References found: {references}")
        
        if explanation_text or references:
            explanation = ET.SubElement(root, "Explanation")
            # print(f"✅ Created Explanation element")
            
            if explanation_text:
                explanation_paragraphs = explanation_text.split('\n')
                explanation_paragraphs = [p.strip() for p in explanation_paragraphs if p.strip()]
                
                # print(f"Explanation paragraphs: {explanation_paragraphs}")
                
                for paragraph in explanation_paragraphs:
                    # Don't add paragraphs that contain URLs (they'll be handled as links)
                    if "References:" not in paragraph.strip() and not re.search(r'https://[^\s\)]+|https:[^\s\)]+|www\.[^\s\)]+\.[a-zA-Z]{2,}', paragraph):
                        contents = ET.SubElement(explanation, "Contents")
                        ET.SubElement(contents, "ContentType").text = "Text"
                        ET.SubElement(contents, "Text").text = paragraph
                        # print(f"✅ Added explanation text: '{paragraph}'")
                    # else:
                        # print(f"⏭️ Skipped paragraph (contains URL): '{paragraph}'")
            
            if references:
                for link in references:
                    contents = ET.SubElement(explanation, "Contents")
                    ET.SubElement(contents, "ContentType").text = "Link"
                    ET.SubElement(contents, "Link").text = link
                    print(f"✅ Added link: '{link}'")
        #     else:
        #         print(f"❌ No references to add")
        # else:
        #     print(f"❌ No explanation or references found")
        
        # print(f"=== END _add_explanation DEBUG ===\n")
    
    # Abstract methods - must be implemented by subclasses
    @abstractmethod
    def get_xml_kind(self) -> str:
        """Return the XML kind/type for this question"""
        pass
    
    @abstractmethod
    def _add_question_specific_elements(self, root: ET.Element):
        """Add question-type specific XML elements"""
        pass
    
    # Common utility methods
    def _clean_description(self) -> str:
        """Clean question description using existing helper"""
        from modules.utils.text_helpers import remove_noise
        return remove_noise(self.text)
    
    def _extract_explanation(self) -> str:
        """Extract explanation text - ENHANCED"""
        # print(f"\n=== _extract_explanation DEBUG ===")
        # print(f"Full text: '{self.text}'")
        
        if "Explanation:" in self.text:
            parts = self.text.split("Explanation:", 1)
            if len(parts) > 1:
                explanation_text = parts[1].strip()
                # print(f"Raw explanation: '{explanation_text}'")
                
                # Don't remove URLs here - let _extract_references handle them
                # Just clean up the explanation text
                lines = explanation_text.split('\n')
                clean_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line and not re.search(r'https?://|https?:|www\.', line):  # Keep non-URL lines
                        clean_lines.append(line)
                
                result = '\n'.join(clean_lines)
                # print(f"Clean explanation: '{result}'")
                # print(f"=== END _extract_explanation DEBUG ===\n")
                return result
        
        # print(f"No explanation found")
        # print(f"=== END _extract_explanation DEBUG ===\n")
        return ""
    
    def _extract_references(self) -> List[str]:
        """Extract reference links - WITH DEBUG"""
        # print(f"\n=== _extract_references DEBUG for Question {self.number} ===")
        
        all_text = self.text
        # print(f"Main text: '{self.text}'")
        
        # Also check in content_items for URLs that might be separate
        for i, item in enumerate(self.content_items):
            content = item.get("content", "")
            if content.strip():
                all_text += " " + content
                # print(f"Content item {i}: '{content}'")
        
        # print(f"Combined text: '{all_text}'")
        
        # UPDATED patterns to handle longer URLs like microsoft docs
        url_patterns = [
            r'https://[^\s\)]+',    # https:// URLs (avoid ending at closing parenthesis)
            r'http://[^\s\)]+',     # http:// URLs
            r'https:[^\s\)]+',      # malformed https: URLs
            r'www\.[^\s\)]+\.[a-zA-Z]{2,}',  # www URLs
        ]
        
        all_urls = []
        
        # Extract URLs using all patterns
        for pattern in url_patterns:
            urls = re.findall(pattern, all_text)
            # print(f"Pattern '{pattern}' found: {urls}")
            all_urls.extend(urls)
        
        # print(f"All URLs found: {all_urls}")
        
        # Remove exact duplicates while preserving order and original format
        unique_urls = []
        for url in all_urls:
            if url not in unique_urls:
                unique_urls.append(url)  # Keep exact original format
        
        # print(f"Unique URLs: {unique_urls}")
        # print(f"=== END _extract_references DEBUG ===\n")
        
        return unique_urls
    
    def _get_image_types(self) -> Dict[str, str]:
        """Get image types mapping - WITH DEBUG"""
        # print(f"\n=== BaseQuestion._get_image_types DEBUG for Question {self.number} ===")
        
        from modules.image_processing.image_processor import identify_image_types
        image_types = identify_image_types(self.content_items)
        
        # print(f"Image types from identify_image_types: {image_types}")
        
        # Also debug the content_items
        # print(f"Content items analysis:")
        for i, item in enumerate(self.content_items):
            content = item.get("content", "").strip()
            images = item.get("images", [])
            # print(f"  Item {i}: content='{content}', images={len(images)}")
            if images:
                for j, img in enumerate(images):
                    print(f"    Image {j}: {img.get('path', 'NO_PATH')}")
        
        print(f"=== END BaseQuestion._get_image_types DEBUG ===\n")
        
        return image_types
    
    def _get_description_images(self) -> List[Dict]:
        """Get images marked as description images"""
        image_types = self._get_image_types()
        return [img for img in self.images 
                if image_types.get(img["path"]) == "description"]
    
    def _get_question_answer_images(self) -> tuple:
        """Get question and answer images separately"""
        image_types = self._get_image_types()
        
        q_images = [img for img in self.images 
                   if image_types.get(img["path"]) == "question"]
        a_images = [img for img in self.images 
                   if image_types.get(img["path"]) == "answer"]
        
        # Fallback logic for unidentified images
        if not q_images and not a_images:
            if len(self.images) >= 2:
                q_images = [self.images[0]]
                a_images = [self.images[1]]
            elif len(self.images) == 1:
                q_images = [self.images[0]]
        
        return q_images, a_images