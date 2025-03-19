import streamlit as st
from utils import extract_text_from_pdf, fix_number_format, save_pdf_for_display
from api import extract_data_from_text
from data_processing import process_api_response
from prompts import create_prompts

# Function to process uploaded files
def process_files(uploaded_files, openai_api_key):
    # Show a progress indicator
    with st.spinner("🔍 Processing files... Please wait."):
        progress_bar = st.progress(0)
        extracted_data = []
        total_files = len(uploaded_files)

        for i, pdf_file in enumerate(uploaded_files):
            # Update progress bar
            progress_bar.progress((i + 0.5) / total_files)
            
            # Save PDF for later display
            save_pdf_for_display(pdf_file)
            
            # Reset file pointer for text extraction
            pdf_file.seek(0)
            
            # Extract and clean text from PDF
            pdf_text = extract_text_from_pdf(pdf_file)
            pdf_text = fix_number_format(pdf_text)

            # Create prompts using the imported module
            prompts = create_prompts(pdf_text)

            # Call OpenAI API
            extract_contents = extract_data_from_text(pdf_text, openai_api_key, prompts)
            
            if extract_contents:
                # Process the API response
                processed_data = process_api_response(extract_contents, pdf_file.name)
                if processed_data:
                    extracted_data.append(processed_data)
            
            # Update progress bar to completion for this file
            progress_bar.progress((i + 1) / total_files)

        # Complete the progress bar
        progress_bar.progress(1.0)
        
        # Show success message
        st.success(f"✅ Successfully processed {len(extracted_data)} files!")

    return extracted_data
