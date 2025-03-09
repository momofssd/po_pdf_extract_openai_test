import streamlit as st
import PyPDF2
import json
import re
from openai import OpenAI
import uuid  # Used to generate unique keys
import time  # For implementing retries
import logging  # For better error logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Streamlit Page Layout
st.set_page_config(page_title="📄 LLM-Powered Purchase Order Extractor", layout="wide")

# Initialize session state variables
if "uploaded_files_list" not in st.session_state:
    st.session_state.uploaded_files_list = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())  # Unique key to force refresh
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Sidebar: API Key and File Upload
with st.sidebar:
    st.header("🔑 API Key & Upload")

    # Store OpenAI API key securely using session state
    if "api_key_valid" not in st.session_state:
        st.session_state.api_key_valid = False

    # User enters OpenAI API key
    openai_api_key = st.text_input("Enter OpenAI API Key", type="password", value=st.session_state.api_key)
    
    # Update session state when API key changes
    if openai_api_key != st.session_state.api_key:
        st.session_state.api_key = openai_api_key
        st.session_state.api_key_valid = False  # Reset validation when key changes

    if st.button("Validate API Key"):
        if not openai_api_key:
            st.error("❌ Please enter an API key.")
        else:
            # Function to validate API key with retries
            def validate_api_key(api_key, max_retries=3, retry_delay=1):
                for attempt in range(max_retries):
                    try:
                        # Create a client with minimal configuration
                        client = OpenAI(api_key=api_key)
                        
                        # Make a lightweight API call to validate the key
                        # Use a simple models.list() call which is more reliable across environments
                        models = client.models.list()
                        # Just check if we got any models back
                        if len(list(models)) > 0:
                            return True, None
                        return False, "No models returned"
                    except Exception as e:
                        error_message = str(e)
                        logger.warning(f"API key validation attempt {attempt+1} failed: {error_message}")
                        
                        # Don't retry for authentication errors
                        if "Unauthorized" in error_message or "Invalid API key" in error_message:
                            return False, error_message
                        
                        # For other errors, retry after delay
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                        else:
                            return False, error_message
                return False, "Maximum retries exceeded"
            
            # Validate the API key
            is_valid, error_message = validate_api_key(openai_api_key)
            
            if is_valid:
                # If successful, store the key and mark as valid
                st.session_state.api_key = openai_api_key
                st.session_state.api_key_valid = True
                st.success("✅ API Key validated successfully!")
            else:
                st.session_state.api_key_valid = False
                
                if "unexpected keyword argument" in error_message:
                    st.error("❌ OpenAI client initialization error. This may be due to a version mismatch.")
                    st.info("If running locally, try: pip install --upgrade openai")
                elif "Unauthorized" in error_message or "Invalid API key" in error_message:
                    st.error("❌ Invalid API Key. Please check and try again.")
                elif "Connection" in error_message or "timeout" in error_message.lower():
                    st.error("❌ Connection error. This may be a temporary issue with the OpenAI API or network connectivity.")
                    st.info("Please try again in a few moments.")
                else:
                    st.error(f"❌ Error validating API key: {error_message}")
                    logger.error(f"Detailed validation error: {error_message}")

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
        st.session_state.uploader_key = str(uuid.uuid4())  # Change uploader key to reset UI
        # Keep API key and validation status
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

# Define system message for OpenAI
system_message = (
    "You are an AI extracting relevant content from a purchase order. "
    "Find the following details and return ONLY a valid JSON object with these fields:"
    "\n- Customer Name (Extract from the 'SHIP TO' section only)"
    "\n- Purchase Order Number"
    "\n- Required Delivery Date (convert to ISO format YYYY-MM-DD)" 
    "\n- Material Number (Extract from the line item section, usually in the same row as 'Order Qty' and 'UOM')"
    "\n- Order Quantity in kg (only the converted kg value, do not include pounds or extra text, round to the nearest integer)"
    "\n- Delivery Address (extract ONLY the 'SHIP TO' address, includes distribution name, ignore all other addresses including 'Vendor', 'Invoice', 'Billing', and any address containing 'PO Box')"
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

        # Function to call OpenAI API with retries
        def call_openai_with_retry(api_key, messages, max_retries=3, retry_delay=2):
            for attempt in range(max_retries):
                try:
                    # Create client with minimal configuration
                    client = OpenAI(api_key=api_key)
                    
                    # Make API call
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0,
                        top_p=0.1
                    )
                    return response.choices[0].message.content, None
                except Exception as e:
                    error_message = str(e)
                    logger.warning(f"OpenAI API call attempt {attempt+1} failed: {error_message}")
                    
                    # Don't retry for authentication errors
                    if "Unauthorized" in error_message or "Invalid API key" in error_message:
                        return None, error_message
                    
                    # For other errors, retry after delay
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        return None, error_message
            return None, "Maximum retries exceeded"
        
        # Call OpenAI API with retry mechanism
        extract_contents, api_error = call_openai_with_retry(st.session_state.api_key, prompts)
        
        if extract_contents:

            # Convert to JSON
            try:
                # Clean and validate JSON before parsing
                extract_contents = extract_contents.strip().strip("```json").strip("```")
                extract_contents_json = json.loads(extract_contents)
                extracted_data.append({"filename": pdf_file.name, "data": extract_contents_json})
            except json.JSONDecodeError:
                st.error(f"⚠ OpenAI returned invalid JSON for {pdf_file.name}")
                st.text("Raw API Response:")
                st.code(extract_contents, language="json")  # Show the invalid response for debugging
        else:
            # Handle API error
            st.error(f"⚠ Error processing {pdf_file.name}: {api_error}")
            logger.error(f"API error for {pdf_file.name}: {api_error}")

    # Display extracted JSON results
    if extracted_data:
        st.subheader("📊 Extracted Purchase Order Data")
        for item in extracted_data:
            st.write(f"📄 **File:** {item['filename']}")
            st.json(item['data'])
