import streamlit as st
import PyPDF2
import json
import re
import pandas as pd  # Added for Excel conversion
from openai import OpenAI
import uuid  # Used to generate unique keys
import io  # Added for BytesIO operations
from prompts import create_prompts  # Import the prompts module

# Set Streamlit Page Layout
st.set_page_config(page_title="📄 LLM-Powered Purchase Order Extractor", layout="wide")

# Initialize session state variables
if "uploaded_files_list" not in st.session_state:
    st.session_state.uploaded_files_list = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())  # Unique key to force refresh
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = []
if "edited_df" not in st.session_state:
    st.session_state.edited_df = pd.DataFrame()

# Sidebar: API Key and File Upload
with st.sidebar:
    st.header("🔑 API Key & Upload")

    # Store OpenAI API key securely using session state
    if "api_key_valid" not in st.session_state:
        st.session_state.api_key_valid = False

    # User enters OpenAI API key
    openai_api_key = st.text_input("Enter OpenAI API Key", type="password")

    if st.button("Validate API Key"):
        try:
            client = OpenAI(api_key=openai_api_key)
            client.models.list()
            st.session_state.api_key_valid = True
            st.success("✅ API Key validated successfully!")
        except Exception as e:
            st.session_state.api_key_valid = False
            st.error("❌ Invalid API Key. Please try again.")

    # File uploader with dynamic key (forces reset)
    uploaded_files = st.file_uploader(
        "📂 Upload Purchase Order PDFs", 
        type="pdf", 
        accept_multiple_files=True, 
        key=st.session_state.uploader_key  # Dynamic key to reset uploader
    )

    # Store uploaded files in session state
    if uploaded_files:
        st.session_state.uploaded_files_list = uploaded_files
        st.session_state.processed = False  # Ensure files aren't processed immediately
        st.success(f"📂 {len(uploaded_files)} files uploaded. Click 'Process' to extract data.")

    # Reset Button (Clears UI and uploaded files)
    if st.button("Reset Files"):
        st.session_state.uploaded_files_list = []  # Clear stored files
        st.session_state.processed = False  # Reset processing state
        st.session_state.extracted_data = []  # Clear extracted data
        st.session_state.edited_df = pd.DataFrame()  # Clear edited dataframe
        st.session_state.uploader_key = str(uuid.uuid4())  # Change uploader key to reset UI
        st.rerun()  # Force full UI refresh

    # Process Button (Only appears when API key is valid and files exist)
    if st.session_state.api_key_valid and st.session_state.uploaded_files_list:
        if st.button("Process Files"):
            st.session_state.processed = True  # Set processing flag

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

# Function to convert extracted data to pandas DataFrame
def convert_to_dataframe(extracted_data):
    all_records = []
    
    for item in extracted_data:
        filename = item['filename']
        data = item['data']
        
        # Handle both single PO and multiple line items
        if isinstance(data, list):
            # Multiple line items
            for line_item in data:
                line_item['filename'] = filename
                # Fix delivery address formatting - replace newlines with spaces
                if 'Delivery Address' in line_item:
                    line_item['Delivery Address'] = line_item['Delivery Address'].replace('\n', ' ').replace('\r', ' ')
                all_records.append(line_item)
        else:
            # Single PO
            data['filename'] = filename
            # Fix delivery address formatting - replace newlines with spaces
            if 'Delivery Address' in data:
                data['Delivery Address'] = data['Delivery Address'].replace('\n', ' ').replace('\r', ' ')
            all_records.append(data)
    
    # Create DataFrame
    if all_records:
        df = pd.DataFrame(all_records)
        # Reorder columns to put filename first
        cols = ['filename'] + [col for col in df.columns if col != 'filename']
        return df[cols]
    else:
        return pd.DataFrame()  # Empty DataFrame if no records

# Function to update extracted_data from edited DataFrame
def update_extracted_data_from_df(df):
    # Group by filename to reconstruct the original structure
    grouped = df.groupby('filename')
    new_extracted_data = []
    
    for filename, group in grouped:
        group_data = group.drop('filename', axis=1).to_dict('records')
        
        # If there's only one record for this filename, store it as a dict
        # Otherwise, store as a list of dicts
        if len(group_data) == 1:
            new_extracted_data.append({"filename": filename, "data": group_data[0]})
        else:
            new_extracted_data.append({"filename": filename, "data": group_data})
    
    return new_extracted_data

# Processing Logic (Only runs when Process is clicked)
if st.session_state.api_key_valid and st.session_state.uploaded_files_list and st.session_state.processed:
    extracted_data = []

    for pdf_file in st.session_state.uploaded_files_list:
        st.write(f"🔍 Processing: {pdf_file.name}")

        # Extract and clean text from PDF
        pdf_text = extract_text_from_pdf(pdf_file)
        pdf_text = fix_number_format(pdf_text)

        # Create prompts using the imported module
        prompts = create_prompts(pdf_text)

        # Call OpenAI API
        client = OpenAI(api_key=openai_api_key)
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=prompts,
                temperature=0,
                top_p=0
            )
            extract_contents = response.choices[0].message.content

            # Convert to JSON
            try:
                # Clean and validate JSON before parsing
                extract_contents = extract_contents.strip().strip("```json").strip("```")
                extract_contents_json = json.loads(extract_contents)
                
                # Process and fix any potential address formatting issues in the JSON
                if isinstance(extract_contents_json, list):
                    for item in extract_contents_json:
                        if 'Delivery Address' in item:
                            item['Delivery Address'] = item['Delivery Address'].replace('\n', ' ').replace('\r', ' ')
                elif isinstance(extract_contents_json, dict):
                    if 'Delivery Address' in extract_contents_json:
                        extract_contents_json['Delivery Address'] = extract_contents_json['Delivery Address'].replace('\n', ' ').replace('\r', ' ')
                
                extracted_data.append({"filename": pdf_file.name, "data": extract_contents_json})
            except json.JSONDecodeError:
                st.error(f"⚠ OpenAI returned invalid JSON for {pdf_file.name}")
                st.text("Raw API Response:")
                st.code(extract_contents, language="json")  # Show the invalid response for debugging

        except Exception as e:
            st.error(f"⚠ Error processing {pdf_file.name}: {e}")

    # Store extracted data in session state for later use
    st.session_state.extracted_data = extracted_data

    # Display extracted JSON results
    if extracted_data:
        st.subheader(" Extracted Purchase Order Data")
        for item in extracted_data:
            st.write(f"📄 **File:** {item['filename']}")
            st.json(item['data'])

# Data Editing and Download Section (always visible if data exists)
if st.session_state.get("extracted_data"):
    # Convert extracted data to DataFrame
    df = convert_to_dataframe(st.session_state.extracted_data)
    
    if not df.empty:
        # Add data editing section
        st.subheader("✏️ Edit Extracted Data")
        
        # Create a button to enter edit mode
        if st.button("Edit Data"):
            st.session_state.edit_mode = True
            # Initialize edited_df in session state if it's empty
            if st.session_state.edited_df.empty:
                st.session_state.edited_df = df.copy()
        
        # Create a button to exit edit mode
        if st.session_state.get("edit_mode", False):
            if st.button("Exit Edit Mode"):
                st.session_state.edit_mode = False
                # Update the extracted_data with the edited values
                st.session_state.extracted_data = update_extracted_data_from_df(st.session_state.edited_df)
        
        # Display editable dataframe when in edit mode
        if st.session_state.get("edit_mode", False):
            st.write("Make your changes directly in the table below. Click 'Exit Edit Mode' when finished.")
            
            # Use Streamlit's data editor to allow editing
            edited_df = st.data_editor(
                st.session_state.edited_df,
                num_rows="dynamic",
                key="edited_data",
                use_container_width=True
            )
            
            # Store the edited dataframe in session state
            st.session_state.edited_df = edited_df
            
            # Use the edited dataframe for downloads
            download_df = st.session_state.edited_df
        else:
            # Use the original dataframe for downloads and display
            download_df = df
            
            # Display as table (non-editable)
            st.subheader("📊 Data Preview")
            st.dataframe(download_df)
        
        # Download section
        st.subheader("📥 Download Data")
        
        # Create CSV file in memory (more reliable than Excel in Streamlit)
        csv = download_df.to_csv(index=False)
        
        # Create download button for CSV
        st.download_button(
            label=" Download as CSV",
            data=csv,
            file_name="Purchase_Order_Data.csv",
            mime="text/csv",
        )
        
        # Try to create Excel file if possible (with fallback)
        try:
            output = io.BytesIO()
            
            # Try different Excel engines
            try:
                # Try using xlsxwriter first (often available in Streamlit)
                download_df.to_excel(output, engine='xlsxwriter', index=False, sheet_name='Purchase Orders')
                excel_available = True
            except ImportError:
                try:
                    # Try using openpyxl as fallback
                    download_df.to_excel(output, engine='openpyxl', index=False, sheet_name='Purchase Orders')
                    excel_available = True
                except ImportError:
                    # If both fail, use basic Excel writer
                    download_df.to_excel(output, index=False, sheet_name='Purchase Orders')
                    excel_available = True
            
            # Create download button for Excel if available
            if excel_available:
                excel_data = output.getvalue()
                st.download_button(
                    label=" Download as Excel",
                    data=excel_data,
                    file_name="Purchase_Order_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as e:
            st.info("Excel download not available. Please use CSV format.")
    else:
        st.info("No data available to download. Process files to extract data.")