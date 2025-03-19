import streamlit as st
import PyPDF2
import re
import json
from fuzzywuzzy import process

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

# Load customer master data from JSON file
def load_customer_master_data():
    try:
        with open('customer_master_data.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading customer master data: {e}")
        return {}

# Function to find customer number using fuzzy matching
def find_customer_number(customer_name, customer_master_data):
    if not customer_name or not customer_master_data:
        return None, None
    
    # Create a dictionary mapping customer names to customer numbers
    customer_dict = {}
    for cust_num, data in customer_master_data.items():
        if 'customer_names' in data:  # Check if using the plural 'customer_names' field
            # Handle list of customer names
            for name in data['customer_names']:
                customer_dict[name] = cust_num
        elif 'customer_name' in data:  # Backward compatibility for singular 'customer_name'
            customer_dict[data['customer_name']] = cust_num
    
    # Use fuzzy matching to find the best match
    best_match = process.extractOne(customer_name, customer_dict.keys())
    
    # If match score is above threshold (adjust as needed)
    if best_match and best_match[1] >= 70:  # 70% match threshold
        matched_customer_name = best_match[0]
        customer_number = customer_dict[matched_customer_name]
        return customer_number, matched_customer_name
    
    return None, None

# Function to find ship to number based on address
def find_ship_to_number(customer_number, delivery_address, customer_master_data):
    if not customer_number or not delivery_address or not customer_master_data:
        return None
    
    # Get ship_to data for the customer
    customer_data = customer_master_data.get(customer_number)
    if not customer_data or 'ship_to' not in customer_data:
        return None
    
    ship_to_dict = customer_data['ship_to']
    
    # Create a dictionary mapping addresses to ship_to numbers
    address_dict = {address: ship_num for ship_num, address in ship_to_dict.items()}
    
    # Use fuzzy matching to find the best match
    best_match = process.extractOne(delivery_address, address_dict.keys())
    
    # If match score is above threshold
    if best_match and best_match[1] >= 60:  # 60% match threshold for addresses
        matched_address = best_match[0]
        return address_dict[matched_address]
    
    return None
