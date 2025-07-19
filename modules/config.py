# Image Types Supported:
# - QuestionDescriptionImage: Regular description images (ContentType: Image)
# - QuestionOptionImage: Question option images for processing
# - AnswerOptionImage: Answer option images for processing  
# - JustDropDown: Special dropdown images
# - PositionedImage: Positioned element images
# - BackgroundImage: Background images for positioned questions (ContentType: BImage)  ← ADD THIS

"""
Configuration settings for the ODT processor application.
"""

import streamlit as st
import toml

# Load secrets from secrets.toml
secrets = toml.load(".streamlit/secrets.toml")

# API Settings
GEMINI_API_KEY = secrets['general']['GEMINI_API_KEY']
ANTHROPIC_API_KEY = secrets['general']['ANTHROPIC_API_KEY']
GEMINI_MODEL = secrets['general']['GEMINI_MODEL']

# The rest of your configuration


# Question Types
QUESTION_TYPES = [
    "HOTSPOT",
    "DRAGDROP", 
    "DROPDOWN", 
    "RADIOBUTTON", 
    "MULTIPLECHOICE",
    "FILLINTHEBLANK",
    "SIMULATION",
    "POSITIONEDDROPDOWN",
    "POSITIONEDDRAGDROP"  # ← ADD THIS NEW TYPE
]

# API Retry Settings
MAX_API_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds

# Image Processing
MINIMUM_IMAGE_SIZE = 100  # bytes, for considering an image valid

# App Settings
APP_TITLE = "ODT to XML Complete Processing "
APP_DESCRIPTION = "This application processes ODT files sequentially, maintaining the natural order of content and using Gemini to analyze images."