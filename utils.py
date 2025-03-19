import streamlit as st
import PyPDF2
import re
import base64
import io

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

# Function to fix number formatting issues
def fix_number_format(text):
    text = re.sub(r'(\d{1,3}),(\d{3}\.\d+)', r'\1\2', text)  # Convert "41,976.050" → "41976.050"
    return text

# Function to save PDF bytes for later display
def save_pdf_for_display(pdf_file):
    # Reset file pointer to beginning
    pdf_file.seek(0)
    # Read bytes and store in session state
    pdf_bytes = pdf_file.read()
    st.session_state.pdf_contents[pdf_file.name] = pdf_bytes
    return pdf_bytes

# Function to create PDF display HTML (kept for backward compatibility)
def create_pdf_display_html(filename, pdf_bytes):
    # This function is no longer used for PDF display
    # PDF display is now handled directly in ui_components.py
    # Keeping this function for backward compatibility
    return f"PDF: {filename}"
