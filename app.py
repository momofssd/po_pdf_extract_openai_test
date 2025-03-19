import streamlit as st
from session_state import initialize_session_state
from ui_components import create_sidebar, display_data_and_downloads, display_pdf_viewer
from processing import process_files
from api import validate_api_key

# Set Streamlit Page Layout
st.set_page_config(page_title="📄 LLM-Powered Purchase Order Extractor", layout="wide")

# Initialize session state variables
initialize_session_state()

# Sidebar: API Key and File Upload
openai_api_key, process_clicked = create_sidebar(validate_api_key)

# Processing Logic (Only runs when Process is clicked)
if st.session_state.api_key_valid and st.session_state.uploaded_files_list and st.session_state.processed:
    # Process the files and store results in session state
    extracted_data = process_files(st.session_state.uploaded_files_list, openai_api_key)
    st.session_state.extracted_data = extracted_data

# Display data and download options
edited_df = display_data_and_downloads()

# Display PDF viewer
display_pdf_viewer(edited_df)
