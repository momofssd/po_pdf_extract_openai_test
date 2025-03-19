# Streamlit PDF Purchase Order Extractor

A Streamlit-based web application for extracting and processing purchase order information from PDF documents. This application uses OpenAI's GPT-4o model to intelligently extract key information from purchase order PDFs and present it in a structured format.

**Try the deployed application here: [https://poextrationopenai.streamlit.app/](https://poextrationopenai.streamlit.app/)**

## Overview

This project has been modularized for better maintainability and consists of the following components:

1. **app.py**: The main Streamlit application entry point
2. **utils.py**: Utility functions for PDF processing and display
3. **data_processing.py**: Functions for data transformation and handling
4. **api.py**: OpenAI API integration
5. **session_state.py**: Session state management
6. **ui_components.py**: UI components and layout
7. **processing.py**: Core processing logic
8. **prompts.py**: Prompt engineering for OpenAI API

## Application Structure

The application follows a modular architecture for better maintainability:

### Main Application (app.py)
```python
import streamlit as st
from session_state import initialize_session_state
from ui_components import create_sidebar, display_data_and_downloads
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

```

### Module Responsibilities

1. **utils.py**: Contains utility functions for PDF text extraction and number formatting
   - `extract_text_from_pdf()`: Extracts text from PDF files
   - `fix_number_format()`: Standardizes number formats

2. **data_processing.py**: Handles data transformation and processing
   - `convert_to_dataframe()`: Converts extracted data to pandas DataFrame
   - `process_api_response()`: Processes and cleans API responses

3. **api.py**: Manages OpenAI API interactions
   - `validate_api_key()`: Validates the OpenAI API key
   - `extract_data_from_text()`: Calls the OpenAI API with the provided text

4. **session_state.py**: Manages Streamlit session state
   - `initialize_session_state()`: Sets up initial session state variables
   - `reset_session_state()`: Resets session state variables

5. **ui_components.py**: Contains UI components and layout functions
   - `create_sidebar()`: Creates the sidebar with API key input and file upload
   - `display_data_and_downloads()`: Displays data and download options

6. **processing.py**: Contains the core processing logic
   - `process_files()`: Processes uploaded files and extracts data

7. **prompts.py**: Contains prompt engineering for OpenAI API
   - `get_system_message()`: Returns the system message for the OpenAI API
   - `get_multi_line_prompt()`: Returns the multi-line prompt for the OpenAI API
   - `create_prompts()`: Creates the prompts for the OpenAI API

## How It Works: OpenAI-Powered Extraction

This system leverages OpenAI's GPT-4o model to extract relevant information from purchase order documents through a streamlined process:

### 1. Text Extraction

```python
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text
```

- The system extracts raw text from PDF documents using PyPDF2
- All pages of the PDF are processed and combined into a single text string

### 2. Text Preprocessing

```python
def fix_number_format(text):
    text = re.sub(r'(\d{1,3}),(\d{3}\.\d+)', r'\1\2', text)  # Convert "41,976.050" → "41976.050"
    return text
```

- The extracted text undergoes preprocessing to fix common formatting issues
- Number formats are standardized to ensure accurate extraction

### 3. OpenAI API Integration

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=prompts,
    temperature=0,
    top_p=0
)
```

- The preprocessed text is sent to OpenAI's GPT-4o model
- A carefully crafted system prompt guides the model to extract specific fields
- Temperature is set to 0 for deterministic outputs

### 4. Information Extraction

The system prompt instructs the model to extract:
- Customer Name (from the 'SHIP TO' section)
- Purchase Order Number
- Required Delivery Date (converted to ISO format)
- Material Number
- Order Quantity in kg (standardized format)
- Delivery Address (only the 'SHIP TO' address)

### 5. JSON Parsing and Validation

```python
try:
    extract_contents_json = json.loads(extract_contents)
except json.JSONDecodeError:
    st.error("⚠ OpenAI returned invalid JSON")
```

- The model's response is parsed as JSON
- Validation ensures the extracted information is properly structured
- Error handling manages cases where the model doesn't return valid JSON

## Streamlit Frontend Features

The Streamlit application provides a user-friendly interface with the following features:

### 1. API Key Management

- Secure input for OpenAI API key
- Validation to ensure the API key is valid
- Session state management to maintain the key during the session

### 2. File Upload

- Support for multiple PDF uploads
- File validation to ensure only PDFs are processed
- Session state management to track uploaded files

### 3. Processing Controls

- Process button to trigger extraction
- Reset button to clear uploaded files and results
- Visual feedback during processing

### 4. Results Display

- Structured display of extracted information
- Data editing capabilities
- Export options for CSV and Excel

## Prerequisites

- Python 3.7+
- Streamlit
- PyPDF2
- OpenAI Python SDK
- pandas
- python-dotenv (for openAI_extraction.py)
- Valid OpenAI API key with access to GPT-4o

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. For openAI_extraction.py, create a .env file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Running the Streamlit App

```
streamlit run app.py
```

The application will open in your default web browser, typically at http://localhost:8501.

### Using the Application

1. Enter your OpenAI API key in the sidebar
2. Click "Validate API Key" to verify the key
3. Upload one or more PDF purchase orders
4. Click "Process Files" to extract information
5. View the structured results for each file
6. Use "Reset Files" to clear and start over

### Running the Backend Script Directly

```
python openAI_extraction.py
```

Note: The backend script is configured to process a specific file (4700414082.pdf). Modify the script to process different files.

## System Prompt Details

The system uses a carefully crafted prompt to guide the OpenAI model:

```
You are an AI extracting relevant content from a purchase order.
Find the following details and return ONLY a valid JSON object with these fields:
- Customer Name (Extract from the 'SHIP TO' section only)
- Purchase Order Number
- Required Delivery Date (convert to ISO format YYYY-MM-DD)
- Material Number (Extract from the line item section)
- Order Quantity in kg (only the converted kg value)
- Delivery Address (extract ONLY the 'SHIP TO' address)

IMPORTANT:
- Return ONLY a valid JSON object
- Ensure 'Order Quantity in kg' is a clean number
- Ensure 'Required Delivery Date' follows ISO 8601 format
- Ensure 'Delivery Address' is the correct 'SHIP TO' address
- Ignore addresses related to 'Vendor', 'Invoice', 'Billing', etc.
```

This prompt ensures the model focuses on extracting the specific information needed in the correct format.

## Extending the Application

To enhance the application:

1. **Add Authentication**: Implement user authentication for secure access
2. **Database Integration**: Store extracted information in a database
3. **Custom Extraction Rules**: Add support for different purchase order formats
4. **Export Options**: Add functionality to export results as CSV, Excel, etc.
5. **Batch Processing Improvements**: Add progress tracking for large batches
6. **Additional Modules**: Create new modules for specific functionality
7. **API Endpoints**: Add API endpoints for programmatic access
