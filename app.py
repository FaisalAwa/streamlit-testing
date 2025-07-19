"""
Main Streamlit application for ODT processing.
"""

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
import streamlit as st
import time
import os
st.set_page_config(page_title="ODT Processor", layout="wide")

import google.generativeai as genai
from modules.config import GEMINI_API_KEY

# Import necessary modules
from modules.core.content_processor import (
    extract_content_from_odt,
    group_content_into_questions_and_case_studies,
    get_question_stats,
    check_missing_images
)
from modules.output.xml_generator import generate_xml_output
from modules.utils.ui_components import (
    display_header,
    display_file_uploader,
    display_process_button
)
from modules.image_processing.image_validation import validate_question_images, validate_case_study_questions

# Configure API
genai.configure(api_key=GEMINI_API_KEY)

def main():
    """Main application function."""
    # Display header and app description
    display_header()
    
    # Setup session state - make sure we have all the variables we need
    if "processed_questions" not in st.session_state:
        st.session_state.processed_questions = []
    
    if "processed_case_studies" not in st.session_state:
        st.session_state.processed_case_studies = []
    
    if "missing_images_info" not in st.session_state:
        st.session_state.missing_images_info = {}
    
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False
    
    # File uploader
    uploaded_file = display_file_uploader()
    
    if uploaded_file:
        # Process button
        if display_process_button(uploaded_file):
            with st.spinner("Processing ODT file..."):
                try:
                    # Get file bytes
                    file_bytes = uploaded_file.getvalue()
                    
                    # Extract content in sequential order
                    st.info("Extracting content from ODT file...")
                    content_items = extract_content_from_odt(file_bytes)
                    
                    # Group content into questions and case studies
                    st.info("Grouping content into questions and case studies...")
                    standalone_questions, case_studies = group_content_into_questions_and_case_studies(content_items)
                    
                    # Validate question images
                    st.info("Validating question images...")
                    
                    # Validate standalone questions
                    standalone_valid, standalone_errors = validate_question_images(standalone_questions)
                    
                    # Validate case study questions
                    case_studies_valid, case_studies_errors = validate_case_study_questions(case_studies)
                    
                    # If any validation failed, stop processing
                    if not standalone_valid or not case_studies_valid:
                        error_messages = []
                        
                        if not standalone_valid:
                            error_messages.append("Standalone questions have missing images:")
                            error_messages.extend(standalone_errors)
                            error_messages.append("")  # Add blank line for readability
                        
                        if not case_studies_valid:
                            error_messages.append("Case study questions have missing images:")
                            error_messages.extend(case_studies_errors)
                        
                        # Display all error messages
                        st.error("Validation failed. Please fix the following issues:")
                        for error in error_messages:
                            st.write(error)
                        
                        # Stop processing
                        st.stop()
                    
                    # Continue only if validation passed
                    st.success("All images validated successfully!")
                    
                    # Store in session state
                    st.session_state.processed_questions = standalone_questions
                    st.session_state.processed_case_studies = case_studies
                    
                    # Check for missing images (for informational purposes)
                    missing_images_info = check_missing_images(standalone_questions, case_studies)
                    st.session_state.missing_images_info = missing_images_info
                    
                    total_questions = len(standalone_questions) + sum(len(cs["questions"]) for cs in case_studies)
                    st.success(f"Successfully processed {total_questions} questions from the ODT file.")
                    
                    # Set flag to indicate processing is complete
                    st.session_state.processing_complete = True
                    
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    st.exception(e)
    
    # Always display the Generate XML section if processing is complete
    if st.session_state.processing_complete:
        # Generate question statistics
        question_stats, total_images, question_types = get_question_stats(st.session_state.processed_questions)
        
        # Add case study questions to stats
        if "processed_case_studies" in st.session_state:
            for case_study in st.session_state.processed_case_studies:
                cs_stats, cs_images, cs_types = get_question_stats(case_study["questions"])
                question_stats.extend(cs_stats)
                total_images += cs_images
                
                # Update question types counts
                for q_type, count in cs_types.items():
                    if q_type in question_types:
                        question_types[q_type] += count
                    else:
                        question_types[q_type] = count

        # XML Generation Section
        st.markdown("---")
        st.header("Generate XML Output")
        
        if st.button("Generate XML", key="generate_xml_button"):
            # Progress bar for XML generation
            progress_bar = st.progress(0)
            percentage_text = st.empty()  # For dynamic percentage text
            
            with st.spinner("Just Wait, Processing Is In Progress..."):
                # Simulate XML generation process with progress updates
                for i in range(1, 101):
                    # Simulate the progress of XML generation
                    time.sleep(0.05)  # Sleep for a short time to simulate the processing time
                    
                    # Update the progress bar
                    progress_bar.progress(i)
                    
                    # Update the percentage text dynamically
                    percentage_text.text(f"Processing: {i}%")
                
                # Generate XML
                xml_output = generate_xml_output(
                    st.session_state.processed_questions,
                    st.session_state.processed_case_studies
                )
                
                # Display download button and preview for generated XML
                if xml_output:
                    # Download button
                    filename = f"{os.path.splitext(uploaded_file.name)[0]}.xml" if uploaded_file else "output.xml"
                    st.download_button(
                        label="Download XML",
                        data=xml_output,
                        file_name=filename,
                        mime="application/xml",
                    )
                    
                    # Preview XML
                    with st.expander("Preview XML"):
                        st.code(xml_output, language="xml")
        
        st.markdown("---")

if __name__ == "__main__":
    main()