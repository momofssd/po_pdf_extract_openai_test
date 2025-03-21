import streamlit as st
import PyPDF2
import re
import json
from fuzzywuzzy import process

## Function to extract text from PDF
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
            data = json.load(file)
            print(f"Successfully loaded customer master data with {len(data)} entries")
            # Print the first entry to help debug structure
            if data:
                first_key = next(iter(data))
                print(f"First customer data structure: {data[first_key]}")
            return data
    except FileNotFoundError:
        print("customer_master_data.json file not found")
        st.warning("Customer master data file not found. Customer matching will not be available.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding customer master data JSON: {e}")
        st.error(f"Error decoding customer master data: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error loading customer master data: {e}")
        st.error(f"Error loading customer master data: {e}")
        return {}

# Function to find customer number using fuzzy matching
def find_customer_number(customer_name, customer_master_data):
    if not customer_name or not customer_master_data:
        print(f"Missing data: customer_name={customer_name}, customer_master_data has {len(customer_master_data) if customer_master_data else 0} entries")
        return None, None
    
    # Create a dictionary mapping customer names to customer numbers
    customer_dict = {}
    try:
        for cust_num, data in customer_master_data.items():
            # Print data structure for debugging
            if cust_num == next(iter(customer_master_data)):
                print(f"Customer data structure for {cust_num}: {data}")
            
            # Handle different possible data structures
            if isinstance(data, dict):
                if 'customer_names' in data and isinstance(data['customer_names'], list):
                    # Handle list of customer names
                    for name in data['customer_names']:
                        if name:  # Ensure name is not empty
                            customer_dict[name] = cust_num
                elif 'customer_name' in data:  # Backward compatibility for singular 'customer_name'
                    if data['customer_name']:  # Ensure name is not empty
                        customer_dict[data['customer_name']] = cust_num
                elif 'customer_names' in data and isinstance(data['customer_names'], str):
                    # Handle case where customer_names is a string instead of a list
                    if data['customer_names']:  # Ensure name is not empty
                        customer_dict[data['customer_names']] = cust_num
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
                # Handle case where data is directly a list of names
                for name in data:
                    if name:  # Ensure name is not empty
                        customer_dict[name] = cust_num
    except Exception as e:
        print(f"Error creating customer dictionary: {e}")
        st.error(f"Error processing customer data: {e}")
        return None, None
    
    # Use fuzzy matching to find the best match
    best_match = process.extractOne(customer_name, customer_dict.keys())
    
    # If match score is above threshold (adjust as needed)
    if best_match and best_match[1] >= 90:  
        matched_customer_name = best_match[0]
        customer_number = customer_dict[matched_customer_name]
        return customer_number, matched_customer_name
    
    return None, None

# Function to find ship to number based on address
def find_ship_to_number(customer_number, delivery_address, customer_master_data):
    if not customer_number or not delivery_address or not customer_master_data:
        print(f"Missing data for ship_to lookup: customer_number={customer_number}, delivery_address available: {bool(delivery_address)}")
        return None
    
    try:
        # Get ship_to data for the customer
        customer_data = customer_master_data.get(customer_number)
        if not customer_data:
            print(f"No customer data found for customer number: {customer_number}")
            return None
        
        # Print customer data structure for debugging
        print(f"Customer data structure for ship_to lookup: {type(customer_data)}")
        
        # Handle different possible data structures
        ship_to_dict = {}
        if isinstance(customer_data, dict):
            if 'ship_to' in customer_data and isinstance(customer_data['ship_to'], dict):
                ship_to_dict = customer_data['ship_to']
            elif 'ship_to' in customer_data and isinstance(customer_data['ship_to'], list):
                # Handle case where ship_to is a list of dictionaries
                for item in customer_data['ship_to']:
                    if isinstance(item, dict) and 'number' in item and 'address' in item:
                        ship_to_dict[item['address']] = item['number']
        
        if not ship_to_dict:
            print(f"No ship_to data found for customer: {customer_number}")
            return None
        
        # Create a dictionary mapping addresses to ship_to numbers
        address_dict = {address: ship_num for ship_num, address in ship_to_dict.items()}
        
        if not address_dict:
            print(f"No addresses found in ship_to data for customer: {customer_number}")
            return None
        
        # Use fuzzy matching to find the best match
        best_match = process.extractOne(delivery_address, address_dict.keys())
        
        # If match score is above threshold
        if best_match and best_match[1] >= 60:  # 60% match threshold for addresses
            matched_address = best_match[0]
            return address_dict[matched_address]
        else:
            print(f"No good match found for delivery address. Best match score: {best_match[1] if best_match else 'None'}")
            return None
    except Exception as e:
        print(f"Error finding ship_to number: {e}")
        return None