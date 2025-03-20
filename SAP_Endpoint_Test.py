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

# Check for query parameters (this is a workaround for demonstration)
query_params = st.experimental_get_query_params()
if "xml_data" in query_params:
    # In a real implementation, this would be handled differently
    xml_data = query_params["xml_data"][0]
    
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
    
    # Clear the query parameter to avoid processing it again on refresh
    st.experimental_set_query_params()

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
