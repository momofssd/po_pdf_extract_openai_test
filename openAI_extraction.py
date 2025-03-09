from dotenv import dotenv_values
from openai import OpenAI
import PyPDF2
import json


env_vars=dotenv_values(".env")
OPENAI_API_KEY=env_vars.get("OPENAI_API_KEY")

if OPENAI_API_KEY:
  try:
    openai_client=OpenAI(api_key=OPENAI_API_KEY)
    openai_client.models.list()
  except Exception as e:
    print (f"Incorrect Key{e}")
    

def extract_text_from_pdf(pdf_filename):
    text = ""
    try:
        with open(pdf_filename, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

import re

def fix_number_format(text):

    text = re.sub(r'(\d{1,3}),(\d{3}\.\d+)', r'\1\2', text)  

    return text

pdf_filename = "pdf_file.pdf"
pdf_text = extract_text_from_pdf(pdf_filename)

pdf_text = fix_number_format(pdf_text)


system_message = (
    "You are an AI extracting relevant content from a purchase order. "
    "Find the following details and return ONLY a valid JSON object with these fields:"
    "\n- Customer Name (Extract from the 'SHIP TO' section only)"
    "\n- Purchase Order Number"
    "\n- Required Delivery Date (convert to ISO format YYYY-MM-DD)" 
    "\n- Material Number (Extract from the line item section, usually in the same row as 'Order Qty' and 'UOM')"
    "\n- Order Quantity in kg (only the converted kg value, do not include pounds or extra text, round to the nearest integer)"
    "\n- Delivery Address (extract ONLY the 'SHIP TO' address, ignore all other addresses including 'Vendor', 'Invoice', 'Billing', and any address containing 'PO Box')"
    "\n\nIMPORTANT: "
    "- Return ONLY a valid JSON object. Do NOT include explanations, introductions, or Markdown formatting."
    "- Ensure 'Order Quantity in kg' is a clean number without thousand separators or extra text."
    "- Ensure 'Required Delivery Date' follows ISO 8601 format (YYYY-MM-DD)."
    "- Ensure 'Delivery Address' is the correct 'SHIP TO' address."
    "- The correct 'SHIP TO' address is usually labeled with 'SHIP TO' or similar wording in the purchase order."
    "- Ignore addresses related to 'Vendor', 'Invoice', 'Billing', 'Remit To', 'PO Box', or 'Mailing Address'."
    "- Ignore Material Number related to 'Vendor', 'Invoice', 'Billing', 'Remit To', 'PO Box', or 'Mailing "
    "- Ignore **Price per unit** label."
)





user_prompt=f"Extract relevant details from the following purchase order:\n{pdf_text}"
prompts=[
  {"role":"system","content":system_message},
  {"role":"user","content":user_prompt},
]


MODEL='gpt-4o'
response=openai_client.chat.completions.create(
  model=MODEL,
  messages=prompts,
  temperature=0,
  top_p=0.1
)
print(response.choices[0].message.content)
extract_contents=response.choices[0].message.content



# Convert string to JSON format
try:
    extract_contents_json = json.loads(extract_contents)  # Convert to dictionary
    print("Valid JSON Output:\n", json.dumps(extract_contents_json, indent=4))  # Pretty print JSON
except json.JSONDecodeError as e:
    print("Error: OpenAI did not return valid JSON.\n", e)
    print("Raw API Response:\n", extract_contents)