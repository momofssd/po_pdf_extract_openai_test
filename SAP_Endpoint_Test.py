import streamlit as st
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import base64

st.set_page_config(page_title="SAP Endpoint Test", page_icon="🔄", layout="wide")

# Set up the page
st.title("SAP Endpoint Test")
st.write("This app simulates a SAP endpoint for receiving IDoc-XML data")

# Initialize session state for storing request history
if "requests" not in st.session_state:
    st.session_state.requests = []

# Function to process incoming XML
def process_xml(xml_data):
    try:
        # Parse XML
        root = ET.fromstring(xml_data)
        
        # Count IDOCs
        idoc_count = len(root.findall('.//IDOC'))
        
        # Extract some basic info for display
        idocs = []
        for idx, idoc in enumerate(root.findall('.//IDOC')):
            idoc_info = {
                "id": idoc.get('BEGIN', f'Unknown-{idx}'),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Try to extract PO number
            po_elem = idoc.find('.//E1EDK02/BELNR')
            if po_elem is not None and po_elem.text:
                idoc_info["po_number"] = po_elem.text
            else:
                idoc_info["po_number"] = "N/A"
            
            # Try to extract customer number
            cust_elem = idoc.find('.//E1EDKA1/PARTN')
            if cust_elem is not None and cust_elem.text:
                idoc_info["customer"] = cust_elem.text
            else:
                idoc_info["customer"] = "N/A"
                
            # Try to extract part number
            part_elem = idoc.find('.//E1EDP19/IDTNR')
            if part_elem is not None and part_elem.text:
                idoc_info["part_number"] = part_elem.text
            else:
                idoc_info["part_number"] = "N/A"
                
            # Try to extract quantity
            qty_elem = idoc.find('.//E1EDP01/MENGE')
            if qty_elem is not None and qty_elem.text:
                idoc_info["quantity"] = qty_elem.text
            else:
                idoc_info["quantity"] = "N/A"
                
            # Print detailed info for debugging
            print(f"Processing IDOC {idx+1}: ID={idoc_info['id']}, PO={idoc_info['po_number']}, Customer={idoc_info['customer']}")
                
            idocs.append(idoc_info)
        
        return {
            "status": "success",
            "message": f"Received {idoc_count} IDOCs for processing",
            "idocs": idocs,
            "details": "This is a dummy SAP endpoint for demonstration purposes"
        }
    except ET.ParseError:
        return {"status": "error", "message": "Invalid XML data"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to create a download link for a dataframe
def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given dataframe to be downloaded"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["Endpoint Status", "Request History", "Documentation"])

# Endpoint Status tab
with tab1:
    st.header("Endpoint Status")
    st.success("✅ SAP Endpoint is running")
    
    # Display the app URL
    app_url = st.text_input("Your Streamlit App URL (when deployed)", 
                           value="https://your-app-name.streamlit.app/", 
                           help="Update this with your actual Streamlit app URL after deployment")
    
    st.write("Use this URL in your main application's SAP integration")
    
    # Code to update the endpoint URL in the main app
    st.subheader("How to update your main app")
    st.code(f"""
# In sap_integration.py, update the default endpoint URL:
def send_idoc_xml_to_sap(xml_data, endpoint_url="{app_url}"):
    # Rest of the function remains the same
    """)

# Request History tab
with tab2:
    st.header("Request History")
    
    # Add controls to clear history
    if st.session_state.requests and st.button("Clear History"):
        st.session_state.requests = []
        st.experimental_rerun()
    
    if not st.session_state.requests:
        st.info("No requests received yet")
    else:
        # Create a dataframe for easier viewing
        request_data = []
        for req in st.session_state.requests:
            for idoc in req.get("response", {}).get("idocs", []):
                request_data.append({
                    "Timestamp": req["timestamp"],
                    "IDOC ID": idoc.get("id", "Unknown"),
                    "PO Number": idoc.get("po_number", ""),
                    "Customer": idoc.get("customer", ""),
                    "Part Number": idoc.get("part_number", ""),
                    "Quantity": idoc.get("quantity", ""),
                    "Status": req.get("response", {}).get("status", "")
                })
        
        if request_data:
            df = pd.DataFrame(request_data)
            st.dataframe(df)
            
            # Download link for history
            st.markdown(get_table_download_link(df, "sap_request_history.csv", "Download Request History"), unsafe_allow_html=True)
        
        # Show detailed history
        st.subheader("Detailed Request History")
        for i, req in enumerate(reversed(st.session_state.requests)):
            with st.expander(f"Request {len(st.session_state.requests) - i}: {req['timestamp']}"):
                # Show the XML data
                st.subheader("Request XML")
                st.code(req["data"], language="xml")
                
                # Show the response
                st.subheader("Response")
                st.json(req["response"])

# Documentation tab
with tab3:
    st.header("Documentation")
    st.write("This endpoint accepts IDoc-XML data from your main application.")
    st.write("When your main app sends IDoc-XML data to this endpoint, it will be processed and displayed in the Request History tab.")
    
    st.subheader("Response Format")
    st.code("""
{
  "status": "success",
  "message": "Received 1 IDOCs for processing",
  "idocs": [
    {
      "id": "DOC1001",
      "timestamp": "2025-03-19 22:15:30",
      "po_number": "PO12345",
      "customer": "CUST123",
      "part_number": "PART-XYZ",
      "quantity": "50"
    }
  ],
  "details": "This is a dummy SAP endpoint for demonstration purposes"
}
    """, language="json")

# Handle incoming requests
# This is where we would normally process POST requests, but Streamlit doesn't directly support this
# Instead, we'll use query parameters and a form to simulate receiving data

# Check for query parameters (this is a workaround for demonstration)
query_params = st.experimental_get_query_params()
if "xml_data" in query_params:
    # In a real implementation, this would be handled differently
    xml_data = query_params["xml_data"][0]
    
    # Process the XML
    result = process_xml(xml_data)
    
    # Add to request history
    st.session_state.requests.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": xml_data,
        "response": result
    })
    
    # Show a notification
    st.success("Received new IDoc-XML data!")
    
    # Clear the query parameter to avoid processing it again on refresh
    st.experimental_set_query_params()

# Note about limitations
st.warning("""
**Note:** This is a simplified simulation. Streamlit apps don't natively support functioning as API endpoints.

For a production-ready mock endpoint, consider:
1. Using a dedicated API platform like FastAPI, Flask, or Express
2. Deploying to a service like Heroku, Render, or Railway

However, for demonstration and testing purposes, this app provides a visual interface to see how your IDoc-XML data would be processed by a SAP system.
""")

# Instructions for deployment
st.header("Deployment Instructions")
st.markdown("""
1. Save this file as `SAP_Endpoint_Test.py`
2. Create a `requirements.txt` file with the following content:
   ```
   streamlit
   pandas
   ```
3. Create a GitHub repository and push these files
4. Deploy to Streamlit Cloud by connecting to your GitHub repository
5. Once deployed, update the URL in your main app's `sap_integration.py` file
""")
