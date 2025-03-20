import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime

st.set_page_config(page_title="SAP Endpoint", page_icon="🔄", layout="wide")

# Set up the page
st.title("SAP Endpoint")

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
        
        return {
            "status": "success",
            "message": f"Received {idoc_count} IDOCs",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except ET.ParseError:
        return {"status": "error", "message": "Invalid XML data"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Add a form to manually input XML data for testing
with st.expander("Test with XML Input"):
    with st.form("xml_input_form"):
        test_xml = st.text_area("Enter XML Data for Testing", 
                               height=200,
                               value="""<?xml version="1.0" encoding="UTF-8"?>
<ORDERS05>
  <IDOC BEGIN="DOC1001">
    <E1EDK01>
      <ACTION>0</ACTION>
      <CURRENCY>USD</CURRENCY>
    </E1EDK01>
    <E1EDKA1>
      <PARVW>AG</PARVW>
      <PARTN>CUST123</PARTN>
    </E1EDKA1>
    <E1EDK02>
      <QUALF>001</QUALF>
      <BELNR>PO12345</BELNR>
    </E1EDK02>
  </IDOC>
</ORDERS05>""")
        submitted = st.form_submit_button("Process Test XML")
        if submitted and test_xml:
            # Process the XML
            result = process_xml(test_xml)
            
            # Add to request history
            st.session_state.requests.append({
                "timestamp": result["timestamp"],
                "data": test_xml,
                "status": result["status"]
            })
            
            # Show a notification
            st.success("Test XML processed!")
            st.experimental_rerun()

# For real requests coming from the main app
# Using the newer st.query_params instead of experimental_get_query_params
if hasattr(st, 'query_params') and 'xml_data' in st.query_params:
    # Get the XML data from query parameters
    xml_data = st.query_params['xml_data']
    
    # Process the XML
    result = process_xml(xml_data)
    
    # Add to request history
    st.session_state.requests.append({
        "timestamp": result["timestamp"],
        "data": xml_data,
        "status": result["status"]
    })
    
    # Show a notification
    st.success("Received new IDoc-XML data!")
    
    # Clear the query parameter
    if hasattr(st, 'query_params'):
        st.query_params.clear()
    
    # Force a rerun to update the UI
    st.experimental_rerun()

# Display received XML data
if not st.session_state.requests:
    st.info("No XML data received yet. Send data from your main application.")
else:
    # Show the most recent request first
    for i, req in enumerate(reversed(st.session_state.requests)):
        st.subheader(f"Received XML ({req['timestamp']})")
        st.code(req["data"], language="xml")
        
        # Add a separator between requests
        if i < len(st.session_state.requests) - 1:
            st.markdown("---")

# Add a small note at the bottom
st.markdown("---")
st.caption("SAP Endpoint for receiving IDoc-XML data")
