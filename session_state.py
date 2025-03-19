import streamlit as st
import uuid

# Function to initialize session state variables
def initialize_session_state():
    if "uploaded_files_list" not in st.session_state:
        st.session_state.uploaded_files_list = []
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = str(uuid.uuid4())  # Unique key to force refresh
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = []
    if "api_key_valid" not in st.session_state:
        st.session_state.api_key_valid = False
    if "processed" not in st.session_state:
        st.session_state.processed = False

# Function to reset session state
def reset_session_state():
    st.session_state.uploaded_files_list = []  # Clear stored files
    st.session_state.processed = False  # Reset processing state
    st.session_state.extracted_data = []  # Clear extracted data
    st.session_state.uploader_key = str(uuid.uuid4())  # Change uploader key to reset UI
