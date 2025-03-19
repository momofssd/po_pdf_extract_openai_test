import pandas as pd
import streamlit as st
from utils import load_customer_master_data, find_customer_number, find_ship_to_number

# Function to convert extracted data to pandas DataFrame
def convert_to_dataframe(extracted_data):
    all_records = []
    
    # Load customer master data
    customer_master_data = load_customer_master_data()
    
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
                
                # Add customer number and ship to number using fuzzy matching
                if 'Customer Name' in line_item:
                    customer_number, _ = find_customer_number(line_item['Customer Name'], customer_master_data)
                    line_item['Customer Number'] = customer_number or ""
                    
                    # Find ship to number if customer number and delivery address are available
                    if customer_number and 'Delivery Address' in line_item:
                        ship_to_number = find_ship_to_number(
                            customer_number, 
                            line_item['Delivery Address'], 
                            customer_master_data
                        )
                        line_item['Ship To Number'] = ship_to_number or ""
                    else:
                        line_item['Ship To Number'] = ""
                else:
                    line_item['Customer Number'] = ""
                    line_item['Ship To Number'] = ""
                
                all_records.append(line_item)
        else:
            # Single PO
            data['filename'] = filename
            # Fix delivery address formatting - replace newlines with spaces
            if 'Delivery Address' in data:
                data['Delivery Address'] = data['Delivery Address'].replace('\n', ' ').replace('\r', ' ')
            
            # Add customer number and ship to number using fuzzy matching
            if 'Customer Name' in data:
                customer_number, _ = find_customer_number(data['Customer Name'], customer_master_data)
                data['Customer Number'] = customer_number or ""
                
                # Find ship to number if customer number and delivery address are available
                if customer_number and 'Delivery Address' in data:
                    ship_to_number = find_ship_to_number(
                        customer_number, 
                        data['Delivery Address'], 
                        customer_master_data
                    )
                    data['Ship To Number'] = ship_to_number or ""
                else:
                    data['Ship To Number'] = ""
            else:
                data['Customer Number'] = ""
                data['Ship To Number'] = ""
            
            all_records.append(data)
    
    # Create DataFrame
    if all_records:
        df = pd.DataFrame(all_records)
        # Reorder columns to put filename first, followed by customer number and ship to number
        priority_cols = ['filename', 'Customer Number', 'Ship To Number']
        other_cols = [col for col in df.columns if col not in priority_cols]
        cols = priority_cols + other_cols
        return df[cols]
    else:
        return pd.DataFrame()  # Empty DataFrame if no records

# Function to clean and parse JSON response from OpenAI
def process_api_response(extract_contents, pdf_file_name):
    import json
    
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
        
        return {"filename": pdf_file_name, "data": extract_contents_json}
    except json.JSONDecodeError:
        st.error(f"⚠ OpenAI returned invalid JSON for {pdf_file_name}")
        st.text("Raw API Response:")
        st.code(extract_contents, language="json")  # Show the invalid response for debugging
        return None
