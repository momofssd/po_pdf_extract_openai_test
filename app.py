import streamlit as st
import PyPDF2
import json
import re
from openai import OpenAI
import uuid  # Used to generate unique keys

# Set Streamlit Page Layout
st.set_page_config(page_title="📄 LLM-Powered Purchase Order Extractor", layout="wide")

# Initialize session state variables
if "uploaded_files_list" not in st.session_state:
    st.session_state.uploaded_files_list = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())  # Unique key to force refresh

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

# Define system message for OpenAI
system_message = (
    "You are an AI extracting relevant content from a purchase order. "
    "Find the following details and return ONLY a valid JSON object with these fields:"
    "\n- Customer Name (Look for terms and condition and header section)"
    "\n- Purchase Order Number"
    "\n- Required Delivery Date (convert to ISO format YYYY-MM-DD)" 
    "\n- Material Number (Extract from the line item section, ignore `material description`,usually in the same row as 'Order Qty' and 'UOM')"
    "\n- Order Quantity in kg (only the converted kg value, do not include pounds or extra text, round to the nearest integer)"
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

        # Call OpenAI API
        client = OpenAI(api_key=openai_api_key)
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=prompts,
                temperature=0,
                top_p=0.1
            )
            extract_contents = response.choices[0].message.content

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

        except Exception as e:
            st.error(f"⚠ Error processing {pdf_file.name}: {e}")

    # Display extracted JSON results
    if extracted_data:
        st.subheader("📊 Extracted Purchase Order Data")
        for item in extracted_data:
            st.write(f"📄 **File:** {item['filename']}")
            st.json(item['data'])
