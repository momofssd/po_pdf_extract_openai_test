# Streamlit PDF Purchase Order Extractor

A Streamlit-based web application for extracting and processing purchase order information from PDF documents. This application uses OpenAI's GPT-4o model to intelligently extract key information from purchase order PDFs and present it in a structured format.

**Try the deployed application here: [https://poextrationopenai.streamlit.app/](https://poextrationopenai.streamlit.app/)**

## Overview

This project consists of two main components:

1. **openAI_extraction.py**: A backend script that handles PDF text extraction and OpenAI API integration
2. **app.py**: A Streamlit frontend application that provides a user-friendly interface for the extraction process

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
    top_p=0.1
)
```

- The preprocessed text is sent to OpenAI's GPT-4o model
- A carefully crafted system prompt guides the model to extract specific fields
- Temperature is set to 0 for deterministic outputs
- Low top_p value (0.1) ensures high-precision responses

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

## Streamlit Frontend (app.py)

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
- JSON formatting for clear presentation
- Error handling for invalid responses

## Differences from Backend-Only Approach

While openAI_extraction.py provides the core functionality, app.py enhances it with:

1. **Interactive UI**: User-friendly interface for uploading files and viewing results
2. **Multiple File Processing**: Support for batch processing multiple PDFs
3. **Real-time Feedback**: Visual indicators of processing status and results
4. **Error Handling**: Improved error messages and recovery options
5. **Session Management**: Persistence of uploads and results during the session

## Prerequisites

- Python 3.7+
- Streamlit
- PyPDF2
- OpenAI Python SDK
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
