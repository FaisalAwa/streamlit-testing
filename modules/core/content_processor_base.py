"""
Base classes for content processing from ODT files.
"""

import os
import re
import uuid
import zipfile
import tempfile
from io import BytesIO
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod

from odf.opendocument import load
from odf.text import P
from odf.draw import Frame, Image

from modules.utils.text_helpers import get_question_number, get_question_type
from modules.image_processing.image_processor import is_valid_image


class ContentItem:
    """Represents a single content item from ODT."""
    
    def __init__(self, content_type: str, content: str, frame_refs: List[str] = None, images: List[Dict] = None):
        self.type = content_type
        self.content = content
        self.frame_refs = frame_refs or []
        self.images = images or []
    
    def has_marker(self, marker: str) -> bool:
        """Check if content contains a specific marker."""
        return marker in self.content.upper()
    
    def has_question_start(self) -> bool:
        """Check if this item starts a new question."""
        return "QUESTION NO:" in self.content.upper()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for backward compatibility."""
        return {
            "type": self.type,
            "content": self.content,
            "frame_refs": self.frame_refs,
            "images": self.images
        }


class ODTExtractor:
    """Handles extraction of raw content from ODT files."""
    
    def __init__(self):
        self.image_frames = {}
    
    def extract_content_from_odt(self, file_bytes: bytes) -> List[ContentItem]:
        """
        Extract content from ODT file in sequential order.
        
        Args:
            file_bytes: The ODT file as bytes
            
        Returns:
            List of ContentItem objects
        """
        with tempfile.NamedTemporaryFile(suffix='.odt', delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        
        try:
            content_items = self._extract_text_and_frames(temp_file_path)
            self._add_images_to_content(content_items, file_bytes)
            return content_items
        finally:
            self._cleanup_temp_file(temp_file_path)
    
    def _extract_text_and_frames(self, file_path: str) -> List[ContentItem]:
        """Extract text content and frame references."""
        doc = load(file_path)
        content_items = []
        
        for para in doc.getElementsByType(P):
            # Get text content
            text = ""
            for node in para.childNodes:
                if hasattr(node, "data"):
                    text += node.data
            
            # Check for frames (which contain images)
            frames = para.getElementsByType(Frame)
            frame_refs = []
            
            for frame in frames:
                frame_id = str(uuid.uuid4())
                self.image_frames[frame_id] = frame
                frame_refs.append(frame_id)
            
            # Create content item
            content_items.append(ContentItem("text", text, frame_refs))
        
        return content_items
    
    def _add_images_to_content(self, content_items: List[ContentItem], file_bytes: bytes):
        """Add image data to content items."""
        with zipfile.ZipFile(BytesIO(file_bytes)) as zip_file:
            image_data = self._extract_image_data(zip_file)
            
            for item in content_items:
                if item.frame_refs:
                    item.images = self._get_images_for_frames(item.frame_refs, image_data)
    
    def _extract_image_data(self, zip_file: zipfile.ZipFile) -> Dict[str, bytes]:
        """Extract all valid images from ZIP file."""
        image_files = [f for f in zip_file.namelist() 
                      if f.startswith('Pictures/') or 
                      any(f.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif'))]
        
        image_data = {}
        for img_path in image_files:
            try:
                data = zip_file.read(img_path)
                if is_valid_image(data):
                    image_data[img_path] = data
            except Exception:
                continue
        
        return image_data
    
    def _get_images_for_frames(self, frame_refs: List[str], image_data: Dict[str, bytes]) -> List[Dict]:
        """Get image data for specific frames."""
        images = []
        
        for frame_id in frame_refs:
            frame = self.image_frames.get(frame_id)
            if frame:
                image_elements = frame.getElementsByType(Image)
                
                for img_elem in image_elements:
                    href = img_elem.getAttribute('href')
                    if href and href in image_data:
                        img_bytes = image_data[href]
                        ext = os.path.splitext(href)[1].lower()
                        fmt = 'jpeg' if ext in ('.jpg', '.jpeg') else ext[1:] if ext else 'png'
                        
                        images.append({
                            "data": img_bytes,
                            "format": fmt,
                            "path": href
                        })
        
        return images
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary file."""
        try:
            os.unlink(file_path)
        except:
            pass


class BaseContentGrouper(ABC):
    """Base class for content grouping strategies."""
    
    def __init__(self):
        self.current_question = None
        self.questions = []
    
    @abstractmethod
    def process_content_items(self, content_items: List[ContentItem]) -> Any:
        """Process content items and return grouped result."""
        pass
    
    def _create_question_from_item(self, item: ContentItem) -> Dict[str, Any]:
        """Create a new question dictionary from content item."""
        text = item.content
        q_number = get_question_number(text)
        q_type = get_question_type(text)
        
        return {
            "number": q_number,
            "type": q_type,
            "content_items": [item.to_dict()],
            "text": text,
            "images": item.images.copy()
        }
    
    def _add_item_to_current_question(self, item: ContentItem):
        """Add content item to current question."""
        if self.current_question:
            self.current_question["content_items"].append(item.to_dict())
            self.current_question["text"] += "\n" + item.content
            
            if item.images:
                self.current_question["images"].extend(item.images)
    
    def _finalize_current_question(self):
        """Finalize current question and add to results."""
        if self.current_question:
            self.questions.append(self.current_question)
            self.current_question = None


class SimpleQuestionGrouper(BaseContentGrouper):
    """Groups content into simple questions only."""
    
    def process_content_items(self, content_items: List[ContentItem]) -> List[Dict[str, Any]]:
        """Group content items into simple questions."""
        for item in content_items:
            if item.has_question_start():
                self._finalize_current_question()
                self.current_question = self._create_question_from_item(item)
            elif self.current_question:
                self._add_item_to_current_question(item)
        
        # Add the final question
        self._finalize_current_question()
        
        return self.questions