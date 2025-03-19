import streamlit as st
import PyPDF2
import json
import re
import pandas as pd  # Added for Excel conversion
from openai import OpenAI
import uuid  # Used to generate unique keys
import io  # Added for BytesIO operations

# Set Streamlit Page Layout
st.set_page_config(page_title="📄 LLM-Powered Purchase Order Extractor", layout="wide")

# Initialize session state variables
if "uploaded_files_list" not in st.session_state:
    st.session_state.uploaded_files_list = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())  # Unique key to force refresh
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = []

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

# Define system message for OpenAI
system_message = (
    "You are an AI extracting relevant content from a purchase order. "
    "Find the following details and return ONLY a valid JSON object with these fields:"
    "\n- Customer Name (Look for terms and condition and header section)"
    "- Purchase Order Number"
    "\n- Required Delivery Date (convert to ISO format YYYY-MM-DD)" 
    "\n- Material Number (Extract from the line item section, ignore `material description`,usually in the same row as 'Order Qty' and 'UOM'),(it could have different naming convenstion such as `Our Ref`)"
    "\n- Order Quantity in kg (only the converted kg value, if the UOM is not specificied in kg or lb, consider it as kg, do not include pounds or extra text, round down to the nearest integer)"
    "\n- Delivery Address (extract ONLY the 'SHIP TO' address, includes distribution name if it is there, ignore all other addresses including 'Vendor', 'Invoice', 'Billing', and any address containing 'PO Box')"
    "\n\nIMPORTANT: "
    "- Return ONLY a valid JSON object. Do NOT include explanations, introductions, or Markdown formatting."
    "- Ensure 'Order Quantity in kg' is a clean number without thousand separators or extra text."
    "- Ensure 'Required Delivery Date' follows ISO 8601 format (YYYY-MM-DD)."
    "- Ensure 'Delivery Address' is the correct 'SHIP TO' address."
    "- Ignore addresses related to 'Vendor', 'Invoice', 'Billing', 'Remit To', 'PO Box', or 'Mailing Address'."
    "- Ignore Material Number related to 'Vendor', 'Invoice', 'Billing', 'Remit To', 'PO Box', or 'Mailing "
    "- Ignore **Price per unit** label."
   
)

# Processing Logic (Only runs when Process is clicked)
if st.session_state.api_key_valid and st.session_state.uploaded_files_list and st.session_state.processed:
    extracted_data = []

    for pdf_file in st.session_state.uploaded_files_list:
        st.write(f"🔍 Processing: {pdf_file.name}")

        # Extract and clean text from PDF
        pdf_text = extract_text_from_pdf(pdf_file)
        pdf_text = fix_number_format(pdf_text)

        # Create prompt for OpenAI
        user_prompt = f"Extract relevant details from the following purchase order:\n{pdf_text}"
        prompts = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]
        prompts.append({
            "role": "system",
            "content": (
                "Analyze the purchase order details provided. If the item section contains more than one item number, this indicates there are multiple purchase order lines. "
                "In that case, extract and output each line separately as a JSON array, where each element represents a single purchase order line with all its details. "
                "If there's only one line, output it as a single JSON object. Ensure that no line is omitted."
                "\n\nIMPORTANT: Format the Delivery Address as a single line with spaces instead of line breaks."
            )
        })

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

# Excel Download Section (always visible if data exists)
if st.session_state.get("extracted_data"):
    st.subheader("📥 Download Data")
    
    # Convert extracted data to DataFrame
    df = convert_to_dataframe(st.session_state.extracted_data)
    
    if not df.empty:
        # Create CSV file in memory (more reliable than Excel in Streamlit)
        csv = df.to_csv(index=False)
        
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
                df.to_excel(output, engine='xlsxwriter', index=False, sheet_name='Purchase Orders')
                excel_available = True
            except ImportError:
                try:
                    # Try using openpyxl as fallback
                    df.to_excel(output, engine='openpyxl', index=False, sheet_name='Purchase Orders')
                    excel_available = True
                except ImportError:
                    # If both fail, use basic Excel writer
                    df.to_excel(output, index=False, sheet_name='Purchase Orders')
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
        
        # Also display as table
        st.subheader(" Data Preview")
        st.dataframe(df)
    else:
        st.info("No data available to download. Process files to extract data.")