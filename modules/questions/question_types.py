"""
Specific question type classes that inherit from BaseQuestion.
"""

from .question_base import BaseQuestion
import xml.etree.ElementTree as ET
import streamlit as st
import difflib
import json
from typing import List, Dict, Any
import re
from typing import List












class HotspotQuestion(BaseQuestion):
    def get_xml_kind(self) -> str:
        return "Hotspot"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add HOTSPOT-specific XML elements"""
        q_images, a_images = self._get_question_answer_images()
        
        # Check for missing images
        if not q_images:
            st.warning(f"No question option image found for HOTSPOT Question {self.number}")
        if not a_images:
            st.warning(f"No answer option image found for HOTSPOT Question {self.number}")
        
        # Extract and add options
        if q_images:
            options = self._extract_options_from_image(q_images[0]["data"])
            self._add_options_to_xml(root, options)
        
        # Extract and add answers
        if a_images:
            answers = self._extract_answers_from_image(a_images[0]["data"])
            options = self._extract_options_from_image(q_images[0]["data"]) if q_images else []
            self._add_answers_to_xml(root, answers, options)
    
    def _extract_options_from_image(self, image_data: bytes) -> List[tuple]:
        """Extract options from question image"""
        from modules.image_processing.image_processor import extract_text_from_image, parse_question_options
        q_text = extract_text_from_image(image_data)
        return parse_question_options(q_text)
    
    def _extract_answers_from_image(self, image_data: bytes) -> List[Dict]:
        """Extract answers from answer image"""
        from modules.image_processing.image_processor import extract_answers_from_image
        return extract_answers_from_image(image_data)
    
    def _add_options_to_xml(self, root: ET.Element, options: List[tuple]):
        """Add options to XML"""
        options_elem = ET.SubElement(root, "QuestionOptions")
        for idx, (stmt, opts) in enumerate(options, start=1):
            option_set = ET.SubElement(options_elem, "OptionSet")
            option_set.set("index", str(idx))
            ET.SubElement(option_set, "Statement").text = stmt
            opts_parent = ET.SubElement(option_set, "Options")
            for opt in opts:
                ET.SubElement(opts_parent, "Option").text = opt
    
    def _add_answers_to_xml(self, root: ET.Element, answers_data: List[Dict], options: List[tuple]):
        """Add answers to XML with statement matching"""
        answers_elem = ET.SubElement(root, "Answers")
        
        if options and answers_data:
            for item in answers_data:
                ans_stmt = item.get("statement", "").strip()
                ans_value = item.get("answer", "").strip()
                
                # Try to find matching statement in options
                best_match = None
                best_match_score = 0
                
                for opt_stmt, _ in options:
                    seq_score = difflib.SequenceMatcher(None, opt_stmt.lower(), ans_stmt.lower()).ratio()
                    
                    if seq_score > best_match_score and seq_score > 0.6:
                        best_match = opt_stmt
                        best_match_score = seq_score
                
                final_statement = best_match if best_match else ans_stmt
                
                ans_elem = ET.SubElement(answers_elem, "Answer")
                ans_elem.set("statement", final_statement)
                ans_elem.text = ans_value
















class DragDropQuestion(BaseQuestion):
    def get_xml_kind(self) -> str:
        return "DragDrop"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add DRAGDROP-specific XML elements"""
        q_images, a_images = self._get_question_answer_images()
        
        # Check for missing images
        if not q_images:
            st.warning(f"No question option image found for DRAGDROP Question {self.number}")
        if not a_images:
            st.warning(f"No answer option image found for DRAGDROP Question {self.number}")
        
        # Extract columns data from question image
        if q_images:
            columns_data = self._extract_columns_from_image(q_images[0]["data"])
            self._add_columns_to_xml(root, columns_data)
        
        # Extract answer pairs if we have an answer image
        if a_images:
            answer_pairs = self._extract_pairs_from_image(a_images[0]["data"])
            self._add_answer_pairs_to_xml(root, answer_pairs)
    
    def _extract_columns_from_image(self, image_data: bytes) -> Dict:
        """Extract columns from question image"""
        from modules.image_processing.image_processor import extract_columns_dynamic
        return extract_columns_dynamic(image_data)
    
    def _extract_pairs_from_image(self, image_data: bytes) -> List[Dict]:
        """Extract answer pairs from answer image"""
        from modules.image_processing.image_processor import extract_pairs_dynamic
        return extract_pairs_dynamic(image_data)
    
    def _add_columns_to_xml(self, root: ET.Element, columns_data: Dict):
        """Add columns to XML"""
        dynamic_cols = ET.SubElement(root, "DynamicColumns")
        for col in columns_data.get("columns", []):
            heading = (col.get("heading") or "").strip()
            items = col.get("items", [])
            col_elem = ET.SubElement(dynamic_cols, "Column")
            col_elem.set("heading", heading)
            for item in items:
                ET.SubElement(col_elem, "Item").text = item.strip()
    
    def _add_answer_pairs_to_xml(self, root: ET.Element, answer_pairs: List[Dict]):
        """Add answer pairs to XML"""
        ans_pairs = ET.SubElement(root, "AnswerPairs")
        for pair in answer_pairs:
            pair_elem = ET.SubElement(ans_pairs, "Pair")
            for h_key, m_val in pair.items():
                col_elem = ET.SubElement(pair_elem, "Column")
                col_elem.set("name", h_key.strip())
                col_elem.text = m_val.strip()























class DropdownQuestion(BaseQuestion):
    def get_xml_kind(self) -> str:
        return "DropDown"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add DROPDOWN-specific XML elements"""
        q_images, a_images = self._get_categorized_images()
        
        # Extract dropdown question data from question image
        question_data = []
        if q_images:
            question_data = self._extract_dropdown_questions_from_image(q_images[0]["data"])
        
        # Extract dropdown answer data from answer image
        answers_data = []
        if a_images:
            answers_data = self._extract_dropdown_answers_from_image(a_images[0]["data"])
        
        # Add options and answers to XML
        self._add_dropdown_options_to_xml(root, question_data)
        self._add_dropdown_answers_to_xml(root, answers_data, a_images)
    
    def _get_categorized_images(self) -> tuple:
        """Get categorized images for dropdown questions"""
        image_types = self._get_image_types()
        
        q_images = []
        a_images = []
        
        for img in self.images:
            img_path = img["path"]
            img_types = image_types.get(img_path, [])
            
            if "question" in str(img_types):
                q_images.append(img)
            elif "answer" in str(img_types):
                a_images.append(img)
        
        # Fallback logic
        if not q_images and not a_images and self.images:
            if len(self.images) >= 2:
                q_images = [self.images[0]]
                a_images = [self.images[1]]
            else:
                q_images = [self.images[0]]
        
        return q_images, a_images
    
    def _extract_dropdown_questions_from_image(self, image_data: bytes) -> List[Dict]:
        """Extract dropdown questions from image"""
        from modules.image_processing.image_processor import extract_dropdown_questions
        raw_data = extract_dropdown_questions(image_data, is_just_dropdown=False)
        
        if isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, dict):
            return [raw_data]
        else:
            try:
                parsed = json.loads(str(raw_data)) if isinstance(raw_data, str) else []
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    return [{"options": [str(parsed)]}]
            except:
                return [{"options": [str(raw_data)]}]
    
    def _extract_dropdown_answers_from_image(self, image_data: bytes) -> List[Dict]:
        """Extract dropdown answers from image"""
        from modules.image_processing.image_processor import extract_dropdown_answers
        raw_answers = extract_dropdown_answers(image_data)
        return raw_answers if isinstance(raw_answers, list) else [raw_answers] if raw_answers else []
    
    def _add_dropdown_options_to_xml(self, root: ET.Element, question_data: List[Dict]):
        """Add dropdown options to XML"""
        options_elem = ET.SubElement(root, "QuestionOptions")
        
        for idx, qd in enumerate(question_data, start=1):
            if not isinstance(qd, dict):
                continue
            
            stmt_text = str(qd.get("statement", "")).strip()
            statement_header = str(qd.get("statement_header", "")).strip()
            options_header = str(qd.get("options_header", "")).strip()
            
            opts_list = qd.get("options", [])
            opts = [str(opt) for opt in opts_list] if isinstance(opts_list, list) else [str(opts_list)]
            
            option_set = ET.SubElement(options_elem, "OptionSet")
            option_set.set("index", str(idx))
            
            ET.SubElement(option_set, "ColumnHeaderStatement").text = statement_header
            ET.SubElement(option_set, "Statement").text = stmt_text
            ET.SubElement(option_set, "ColumnHeaderOptions").text = options_header
            
            opts_parent = ET.SubElement(option_set, "Options")
            for opt in opts:
                ET.SubElement(opts_parent, "Option").text = str(opt)
    
    def _add_dropdown_answers_to_xml(self, root: ET.Element, answers_data: List[Dict], a_images: List[Dict]):
        """Add dropdown answers to XML"""
        answers_elem = ET.SubElement(root, "Answers")
        
        if not answers_data and a_images:
            # Fallback: try to extract text directly
            from modules.image_processing.image_processor import extract_text_from_image
            answer_text = extract_text_from_image(a_images[0]["data"])
            
            lines = answer_text.strip().split('\n')
            for line in lines:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    header = parts[0].strip()
                    value = parts[1].strip()
                    
                    if header and value:
                        ans_elem = ET.SubElement(answers_elem, "Answer")
                        ans_elem.set("statement_header", str(header))
                        ans_elem.set("answer_header", "")
                        ans_elem.set("statement", str(f'"{header}" :'))
                        ans_elem.text = str(value)
        else:
            for ans_item in answers_data:
                if not isinstance(ans_item, dict):
                    continue
                
                statement = str(ans_item.get("statement", "")).strip()
                answer = str(ans_item.get("answer", "")).strip()
                statement_header = str(ans_item.get("statement_header", "")).strip()
                answer_header = str(ans_item.get("answer_header", "")).strip()
                
                ans_elem = ET.SubElement(answers_elem, "Answer")
                ans_elem.set("statement_header", statement_header)
                ans_elem.set("answer_header", answer_header)
                ans_elem.set("statement", statement)
                ans_elem.text = answer
































class TextBasedQuestion(BaseQuestion):
    def get_xml_kind(self) -> str:
        return self.type  # SingleChoice, MultipleChoice, etc.
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add text-based question specific XML elements"""
        options, correct_answers = self._extract_text_options()
        self._add_text_choices_to_xml(root, options, correct_answers)
    
    def _extract_text_options(self) -> tuple:
        """Extract options and answers from text and content_items"""
        options = []
        correct_answers = []
        
        # First try to extract from self.text (original logic)
        try:
            from modules.utils.text_helpers import extract_options_from_text
            text_options, text_answers, _ = extract_options_from_text(self.text, self.type)
            if text_options:
                options.extend(text_options)
                correct_answers.extend(text_answers)
        except:
            pass
        
        # If no options found in text, extract from content_items
        if not options and self.content_items:
            options = self._extract_options_from_content_items()
            correct_answers = self._extract_answers_from_text()
        
        # return options, correct_answers

            # Remove duplicates from correct_answers while preserving order
        seen = set()
        unique_answers = []
        for ans in correct_answers:
            if ans not in seen:
                seen.add(ans)
                unique_answers.append(ans)
        
        return options, unique_answers
    
    def _extract_options_from_content_items(self) -> List[tuple]:
        """Extract A., B., C., D. options from content_items"""
        options = []
        
        for item in self.content_items:
            item_text = item.get("content", "").strip()
            
            # Look for A., B., C., D. pattern options
            if re.match(r'^[A-Z]\.', item_text):
                # Extract letter (A, B, C, D)
                letter = item_text[0]
                # Extract option text (remove "A. " part)
                option_text = re.sub(r'^[A-Z]\.\s*', '', item_text).strip()
                options.append((letter, option_text))
        
        return options
    
    def _extract_answers_from_text(self) -> List[str]:
        """Extract correct answers from text"""
        correct_answers = []
        
        # Look for answer patterns in text
        if "Answer:" in self.text:
            answer_part = self.text.split("Answer:", 1)[1]
            # Extract letters from answer (A, B, C, etc.)
            answer_letters = re.findall(r'\b[A-Z]\b', answer_part)
            correct_answers.extend(answer_letters)
        
        # Also check content_items for answer
        if self.content_items:
            for item in self.content_items:
                item_text = item.get("content", "").strip()
                if item_text.lower().startswith('answer:'):
                    answer_letters = re.findall(r'\b[A-Z]\b', item_text)
                    correct_answers.extend(answer_letters)
        
        return correct_answers
    
    def _add_text_choices_to_xml(self, root: ET.Element, options: List[tuple], correct_answers: List[str]):
        """Add text-based choices to XML"""
        # Add choices
        for letter, opt_text in options:
            choice = ET.SubElement(root, "Choices")
            ET.SubElement(choice, "Number").text = letter
            contents = ET.SubElement(choice, "Contents")
            ET.SubElement(contents, "ContentType").text = "Text"
            ET.SubElement(contents, "Text").text = opt_text
        
        # Add answers
        if correct_answers:
            answer = ET.SubElement(root, "Answer")
            for ans in correct_answers:
                ET.SubElement(answer, "Choices").text = ans





































class FillInTheBlankQuestion(BaseQuestion):
    """Handles FILLINTHEBLANK question type with multiple blanks and answers"""
    
    def get_xml_kind(self) -> str:
        return "FillInTheBlank"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add FILLINTHEBLANK-specific XML elements with multiple blank support"""
        # Extract multiple answers
        answers = self._extract_multiple_answers()
        
        # Add multiple answer choices
        if answers:
            answer_elem = ET.SubElement(root, "Answer")
            for answer in answers:
                if answer.strip():  # Only add non-empty answers
                    choices_elem = ET.SubElement(answer_elem, "Choices")
                    choices_elem.text = answer.strip()
    
    def _extract_multiple_answers(self) -> List[str]:
        """Extract multiple answers separated by commas"""
        
        # Look for "Answer:" followed by comma-separated values
        patterns = [
            r'Answer:\s*(.+?)(?:\n\s*(?:QUESTION|Explanation|References)|$)',
            r'Answer:\s*(.+?)(?:\n\n|$)',
            r'Answer:\s*(.+?)(?:\n|$)',
            r'Answer:\s*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                answer_text = match.group(1).strip()
                
                # Clean up the answer text
                answer_text = re.sub(r'\s+', ' ', answer_text)  # Replace multiple spaces with single
                answer_text = answer_text.strip()
                
                if answer_text:
                    # Split by comma and clean each answer
                    answers = [ans.strip() for ans in answer_text.split(',') if ans.strip()]
                    return answers
        
        return []
    
    def _clean_description(self) -> str:
        """Override to replace blanks with [blank] in description"""
        from modules.utils.text_helpers import remove_noise
        clean_desc = remove_noise(self.text)
        
        # Replace all blank patterns with [blank]
        blank_patterns = [
            r'_{3,}',           # Multiple underscores (3 or more)
            r'_+',              # Any underscores
            r'\[_+\]',          # Underscores in brackets
        ]
        
        for pattern in blank_patterns:
            clean_desc = re.sub(pattern, '[blank]', clean_desc)
        
        return clean_desc






























class SimulationQuestion(BaseQuestion):
    """Handles SIMULATION question type"""
    
    def get_xml_kind(self) -> str:
        return "Simulation"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add SIMULATION-specific XML elements"""
        # Extract answer text (not as choices since there are no A,B,C options)
        answer_text = self._extract_answer_text()
        
        # Add simple answer element with direct text
        if answer_text:
            answer_elem = ET.SubElement(root, "Answer")
            answer_elem.text = answer_text
    
    def _extract_answer_text(self) -> str:
        """Extract answer text from SIMULATION question"""
        
        # Look for "Answer:" followed by the answer text
        patterns = [
            # Pattern 1: Answer: text until Explanation or next section
            r'Answer:\s*(.+?)(?:\n\s*(?:Explanation|QUESTION|References)|$)',
            # Pattern 2: Answer: text until double newline
            r'Answer:\s*(.+?)(?:\n\n|$)',
            # Pattern 3: Answer: text until single newline  
            r'Answer:\s*(.+?)(?:\n|$)',
            # Pattern 4: Answer: everything after it
            r'Answer:\s*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                
                # Clean up the answer
                answer = re.sub(r'\s+', ' ', answer)  # Replace multiple spaces with single space
                answer = answer.strip()
                
                if answer and len(answer) > 0:
                    return answer
        
        return ""




























class PositionedDropdownQuestion(BaseQuestion):
    """Handles POSITIONEDDROPDOWN question type with positioned dropdown detection"""
    
    def get_xml_kind(self) -> str:
        return "PositionedDropDown"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add POSITIONEDDROPDOWN-specific XML elements"""
        # Get positioned images only - let BaseQuestion handle description images
        positioned_images = self._get_positioned_images()
        
        # Check for missing positioned images
        if not positioned_images:
            st.warning(f"No PositionedImage found for POSITIONEDDROPDOWN Question {self.number}")
            return
        
        # Process positioned dropdown image
        positioned_data = self._process_positioned_image(positioned_images[0]["data"])
        
        if positioned_data and 'dropdowns' in positioned_data:
            self._add_positioned_dropdown_to_xml(root, positioned_data)
        else:
            st.error(f"Failed to process PositionedImage for Question {self.number}")
    
    def _get_positioned_images(self) -> List[Dict]:
        """Get positioned images only - same pattern as other question types"""
        image_types = self._get_image_types()
        return [img for img in self.images 
                if image_types.get(img["path"]) == "positioned"]
    
    def _process_positioned_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Process positioned dropdown image using Claude API"""
        from modules.image_processing.positioned_dropdown_processor import process_positioned_dropdown_image
        return process_positioned_dropdown_image(image_bytes)
    
    def _add_positioned_dropdown_to_xml(self, root: ET.Element, positioned_data: Dict[str, Any]):
        """Add positioned dropdown data to XML"""
        # Add QuestionOptions section
        options_elem = ET.SubElement(root, "QuestionOptions")
        
        for dropdown in positioned_data['dropdowns']:
            option_set = ET.SubElement(options_elem, "OptionSet")
            option_set.set("index", str(dropdown.get("index", dropdown["id"])))
            
            # Add positioning data
            ET.SubElement(option_set, "id").text = str(dropdown["id"])
            ET.SubElement(option_set, "x").text = str(dropdown["x"])
            ET.SubElement(option_set, "y").text = str(dropdown["y"])
            ET.SubElement(option_set, "width").text = str(dropdown["width"])
            ET.SubElement(option_set, "height").text = str(dropdown["height"])
            
            # Add empty header elements
            ET.SubElement(option_set, "ColumnHeaderStatement")
            ET.SubElement(option_set, "Statement")
            ET.SubElement(option_set, "ColumnHeaderOptions")
            
            # Add options
            opts_parent = ET.SubElement(option_set, "Options")
            for option_text in dropdown.get('options', []):
                option_elem = ET.SubElement(opts_parent, "Option")
                option_elem.text = option_text
                
                # Mark selected options
                if option_text in dropdown.get('selected_options', []):
                    option_elem.set("selected", "true")
        
        # Add Answers section (only selected options)
        answers_elem = ET.SubElement(root, "Answers")
        
        for dropdown in positioned_data['dropdowns']:
            # Get coordinates and index for this dropdown
            x = dropdown["x"]
            y = dropdown["y"]
            width = dropdown["width"]
            height = dropdown["height"]
            index = dropdown.get("index", dropdown["id"])
            
            # Create an Answer element ONLY for SELECTED options in this dropdown
            for selected_option in dropdown.get('selected_options', []):
                ans_elem = ET.SubElement(answers_elem, "Answer")
                ans_elem.set("statement_header", "")
                ans_elem.set("answer_header", "")
                ans_elem.set("statement", "")
                ans_elem.set("index", str(index))
                ans_elem.set("x", str(x))
                ans_elem.set("y", str(y))
                ans_elem.set("width", str(width))
                ans_elem.set("height", str(height))
                ans_elem.text = selected_option
































# class PositionedDragDropQuestion(BaseQuestion):
#     """Handles POSITIONEDDRAGDROP question type with positioned drag-drop detection"""
    
#     def get_xml_kind(self) -> str:
#         return "PositionedDragDrop"
    
#     def _add_question_specific_elements(self, root: ET.Element):
#         """Add POSITIONEDDRAGDROP-specific XML elements"""
#         # Get positioned images only - let BaseQuestion handle description images
#         positioned_images = self._get_positioned_images()
        
#         # Check for missing positioned images
#         if not positioned_images:
#             st.warning(f"No PositionedImage found for POSITIONEDDRAGDROP Question {self.number}")
#             return
        
#         # Process positioned drag-drop image
#         positioned_data = self._process_positioned_image(positioned_images[0]["data"])
        
#         if positioned_data and not positioned_data.get('error'):
#             self._add_positioned_dragdrop_to_xml(root, positioned_data)
#         else:
#             error_msg = positioned_data.get('error', 'Unknown error')
#             st.error(f"Failed to process PositionedImage for Question {self.number}: {error_msg}")
    
#     def _get_positioned_images(self) -> List[Dict]:
#         """Get positioned images only - same pattern as other question types"""
#         image_types = self._get_image_types()
#         return [img for img in self.images 
#                 if image_types.get(img["path"]) == "positioned"]
    
#     def _process_positioned_image(self, image_bytes: bytes) -> Dict[str, Any]:
#         """Process positioned drag-drop image using Claude API"""
#         from modules.image_processing.positioned_dragdrop_processor import process_positioned_dragdrop_image
#         return process_positioned_dragdrop_image(image_bytes)
    
#     def _add_positioned_dragdrop_to_xml(self, root: ET.Element, positioned_data: Dict[str, Any]):
#         """Add positioned drag-drop data to XML"""
#         # Add DynamicColumns section (sidebar options)
#         dynamic_cols = ET.SubElement(root, "DynamicColumns")
#         for column in positioned_data.get('columns', []):
#             col_elem = ET.SubElement(dynamic_cols, "Column")
#             col_elem.set("heading", column.get('heading', ''))
#             for item in column.get('items', []):
#                 ET.SubElement(col_elem, "Item").text = item
        
#         # Add Box coordinates
#         for box in positioned_data.get('boxes', []):
#             box_elem = ET.SubElement(dynamic_cols, "Box")
#             box_elem.set("index", str(box.get('index', '')))
            
#             ET.SubElement(box_elem, "id").text = str(box.get('id', ''))
#             ET.SubElement(box_elem, "x").text = str(box.get('x', ''))
#             ET.SubElement(box_elem, "y").text = str(box.get('y', ''))
#             ET.SubElement(box_elem, "width").text = str(box.get('width', ''))
#             ET.SubElement(box_elem, "height").text = str(box.get('height', ''))
        
#         # Add AnswerPairs section
#         if positioned_data.get('answer_pairs'):
#             answer_pairs = ET.SubElement(dynamic_cols, "AnswerPairs")
            
#             # Group answer pairs by their index/name for proper pairing
#             current_pair = None
#             current_pair_elem = None
            
#             for pair_data in positioned_data.get('answer_pairs', []):
#                 # Create new pair if needed
#                 if current_pair != pair_data.get('name'):
#                     current_pair = pair_data.get('name')
#                     current_pair_elem = ET.SubElement(answer_pairs, "Pair")
                
#                 # Add column to current pair
#                 if current_pair_elem is not None:
#                     col_elem = ET.SubElement(current_pair_elem, "Column")
#                     col_elem.set("name", pair_data.get('name', ''))
#                     col_elem.set("index", str(pair_data.get('index', '')))
#                     col_elem.set("id", str(pair_data.get('id', '')))
#                     col_elem.set("x", str(pair_data.get('x', '')))
#                     col_elem.set("y", str(pair_data.get('y', '')))
#                     col_elem.set("width", str(pair_data.get('width', '')))
#                     col_elem.set("height", str(pair_data.get('height', '')))
#                     col_elem.text = pair_data.get('text', '')














import xml.etree.ElementTree as ET
import streamlit as st
from typing import Dict, List, Any

from modules.questions.question_base import BaseQuestion

class PositionedDragDropQuestion(BaseQuestion):
    """Handles POSITIONEDDRAGDROP question type with positioned drag-drop detection"""
    
    def get_xml_kind(self) -> str:
        return "PositionedDragDrop"
    
    def _add_question_specific_elements(self, root: ET.Element):
        """Add POSITIONEDDRAGDROP-specific XML elements"""
        # Get different types of images
        image_types = self._get_image_types()
        
        # Get background image (used for coordinates)
        background_images = [img for img in self.images 
                           if image_types.get(img["path"]) == "background"]
        
        # Get positioned image (used for text content)
        positioned_images = [img for img in self.images 
                           if image_types.get(img["path"]) == "positioned"]
        
        if not background_images:
            st.warning(f"No BackgroundImage found for Question {self.number}")
            return
            
        if not positioned_images:
            st.warning(f"No PositionedImage found for Question {self.number}")
            return
        
        # Get coordinates from BackgroundImage
        coordinates_data = self._get_coordinates_from_image(background_images[0]["data"])
        
        # Get positioned data from PositionedImage
        positioned_data = self._get_positioned_data_from_image(positioned_images[0]["data"])
        
        # Combine the data and add to XML
        if coordinates_data and positioned_data:
            combined_data = self._combine_coordinate_and_positioned_data(coordinates_data, positioned_data)
            self._add_positioned_dragdrop_to_xml(root, combined_data)
        else:
            st.error(f"Failed to process images for Question {self.number}")
    
    def _get_coordinates_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract coordinates from BackgroundImage"""
        # Process background image for coordinates only
        from modules.image_processing.positioned_dragdrop_processor import process_coordinates_only
        coordinates_data = process_coordinates_only(image_bytes)
        
        if coordinates_data.get('error'):
            st.error(f"Failed to process BackgroundImage for coordinates: {coordinates_data.get('error')}")
            return {}
        
        return coordinates_data
    
    def _get_positioned_data_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract positioned data from PositionedImage"""
        # Process positioned image for columns and answers only
        from modules.image_processing.positioned_dragdrop_processor import process_positioned_data_only
        positioned_data = process_positioned_data_only(image_bytes)
        
        if positioned_data.get('error'):
            st.error(f"Failed to process PositionedImage: {positioned_data.get('error')}")
            return {}
        
        return positioned_data
    
    def _combine_coordinate_and_positioned_data(self, coordinates_data: Dict, positioned_data: Dict) -> Dict[str, Any]:
        """Combine coordinates and positioned data"""
        combined_data = {
            'columns': positioned_data.get('columns', []),
            'boxes': coordinates_data.get('boxes', []),
            'answer_pairs': []
        }
        
        # Combine answer pairs with coordinates
        boxes = coordinates_data.get('boxes', [])
        answer_pairs = positioned_data.get('answer_pairs', [])
        
        # Match answer pairs with their corresponding box coordinates
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
    
    def _add_positioned_dragdrop_to_xml(self, root: ET.Element, positioned_data: Dict[str, Any]):
        """Add positioned drag-drop data to XML"""
        # Add DynamicColumns section (sidebar options)
        dynamic_cols = ET.SubElement(root, "DynamicColumns")
        for column in positioned_data.get('columns', []):
            col_elem = ET.SubElement(dynamic_cols, "Column")
            col_elem.set("heading", column.get('heading', ''))
            for item in column.get('items', []):
                ET.SubElement(col_elem, "Item").text = item
        
        # Add Box coordinates
        for box in positioned_data.get('boxes', []):
            box_elem = ET.SubElement(dynamic_cols, "Box")
            box_elem.set("index", str(box.get('index', '')))
            
            ET.SubElement(box_elem, "id").text = str(box.get('id', ''))
            ET.SubElement(box_elem, "x").text = str(box.get('x', ''))
            ET.SubElement(box_elem, "y").text = str(box.get('y', ''))
            ET.SubElement(box_elem, "width").text = str(box.get('width', ''))
            ET.SubElement(box_elem, "height").text = str(box.get('height', ''))
        
        # Add AnswerPairs section
        if positioned_data.get('answer_pairs'):
            answer_pairs = ET.SubElement(dynamic_cols, "AnswerPairs")
            
            # Group answer pairs by their index/name for proper pairing
            current_pair = None
            current_pair_elem = None
            
            for pair_data in positioned_data.get('answer_pairs', []):
                # Create new pair if needed
                if current_pair != pair_data.get('name'):
                    current_pair = pair_data.get('name')
                    current_pair_elem = ET.SubElement(answer_pairs, "Pair")
                
                # Add column to current pair
                if current_pair_elem is not None:
                    col_elem = ET.SubElement(current_pair_elem, "Column")
                    col_elem.set("name", pair_data.get('name', ''))
                    col_elem.set("index", str(pair_data.get('index', '')))
                    col_elem.set("id", str(pair_data.get('id', '')))
                    col_elem.set("x", str(pair_data.get('x', '')))
                    col_elem.set("y", str(pair_data.get('y', '')))
                    col_elem.set("width", str(pair_data.get('width', '')))
                    col_elem.set("height", str(pair_data.get('height', '')))
                    col_elem.text = pair_data.get('text', '')