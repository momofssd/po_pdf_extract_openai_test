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

# Function to create PDF display HTML
def create_pdf_display_html(filename, pdf_bytes):
    # Create a download button for the PDF
    download_button = f'''
    <div style="margin-bottom: 10px;">
        <h3>Viewing: {filename}</h3>
        <p>Chrome security policies may block embedded PDFs. Use the download button below to view the PDF:</p>
        <a href="data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('utf-8')}" 
           download="{filename}" 
           target="_blank"
           style="display: inline-block; 
                  padding: 10px 20px; 
                  background-color: #4CAF50; 
                  color: white; 
                  text-decoration: none; 
                  border-radius: 4px;
                  margin-bottom: 15px;">
           Download PDF
        </a>
    </div>
    '''
    
    # Use object tag instead of iframe for better browser compatibility
    pdf_viewer = f'''
    <object data="data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('utf-8')}" 
            type="application/pdf" 
            width="100%" 
            height="800">
        <p>Your browser doesn't support embedded PDFs. Please use the download button above.</p>
    </object>
    '''
    
    return download_button + pdf_viewer
