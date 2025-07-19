"""
Streamlit UI components for the ODT processor application.
"""

import base64
import time
import pandas as pd
import streamlit as st

def display_header():
    """Display the application header and description."""
    st.title("ODT to XML Complete Processing -- Version 1.0")
    st.write("This application processes ODT files sequentially, maintaining the natural order of content and using Gemini to analyze images.")


def display_file_uploader():
    """Display the file uploader widget."""
    return st.file_uploader("Upload an ODT file", type=["odt"])


def display_process_button(uploaded_file):
    """
    Display a button to process the uploaded file.
    
    Args:
        uploaded_file: The uploaded ODT file
        
    Returns:
        bool: True if processing should proceed, False otherwise
    """
    if uploaded_file:
        file_name = uploaded_file.name
        button_key = f"process_button_{file_name}"
        
        if st.button("Process ODT File", key=button_key):
            # Always set this flag to True after successful processing
            st.session_state.show_generate_xml = True
            return True
    
    return False
