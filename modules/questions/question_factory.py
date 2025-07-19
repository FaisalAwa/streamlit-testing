"""
Factory class for creating appropriate question objects based on question type.
"""

from typing import Dict, Any
from .question_types import HotspotQuestion, DragDropQuestion, DropdownQuestion, TextBasedQuestion, FillInTheBlankQuestion, SimulationQuestion,PositionedDropdownQuestion,PositionedDragDropQuestion

class QuestionFactory:
    """Factory for creating question objects"""
    
    @staticmethod
    def create_question(question_data: Dict[str, Any]):
        """
        Create appropriate question object based on question type.
        
        Args:
            question_data: Dictionary containing question information
            
        Returns:
            Question object of appropriate type
        """
        q_type = question_data.get("type", "").upper()
        
        # Map question types to their respective classes
        if q_type == "HOTSPOT":
            return HotspotQuestion(question_data)
        elif q_type == "DRAGDROP":
            return DragDropQuestion(question_data)
        elif q_type == "DROPDOWN":
            return DropdownQuestion(question_data)
        elif q_type == "FILLINTHEBLANK":  # ← Add here
            return FillInTheBlankQuestion(question_data)
        elif q_type == "POSITIONEDDROPDOWN":  # ← Add the new question type here
            return PositionedDropdownQuestion(question_data)
        elif q_type == "POSITIONEDDRAGDROP":  # ← Add the new question type here
            return PositionedDragDropQuestion(question_data)        
        elif q_type == "SIMULATION":
            return SimulationQuestion(question_data)
        elif q_type in ["SINGLECHOICE", "MULTIPLECHOICE", "RADIOBUTTON"]:
            return TextBasedQuestion(question_data)
        else:
            # Default fallback for unknown question types
            return TextBasedQuestion(question_data)
    
    @staticmethod
    def get_supported_types() -> list:
        """
        Get list of supported question types.
        
        Returns:
            List of supported question type strings
        """
        return [
            "HOTSPOT",
            "DRAGDROP", 
            "DROPDOWN",
            "SINGLECHOICE",
            "MULTIPLECHOICE",
            "RADIOBUTTON",
            "FILLINTHEBLANK",
            "POSITIONEDDROPDOWN",  # ← Add here too
            "POSITIONEDDRAGDROP"
        ]
    
    @staticmethod
    def is_supported_type(q_type: str) -> bool:
        """
        Check if a question type is supported.
        
        Args:
            q_type: Question type string
            
        Returns:
            Boolean indicating if type is supported
        """
        return q_type.upper() in QuestionFactory.get_supported_types()