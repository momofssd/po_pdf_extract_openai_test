import http.server
import socketserver
import json
import logging
import os
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as ET

# File paths
LOG_FILE = "sap_endpoint.log"
XML_FILE = "sap_endpoint_xml.log"

# Function to reset log files
def reset_log_files():
    # Clear the log file by opening it in write mode
    with open(LOG_FILE, 'w') as f:
        f.write("")  # Write empty string to clear the file
    
    # Clear the XML log file
    with open(XML_FILE, 'w') as f:
        f.write("")  # Write empty string to clear the file
    
    print(f"Log files {LOG_FILE} and {XML_FILE} have been reset")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SAP-Endpoint")

# Reset log files on startup
reset_log_files()
logger.info("SAP Endpoint server starting - log files reset")

# Define the port
PORT = 8000

class SAPEndpointHandler(http.server.BaseHTTPRequestHandler):
    def _set_response(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self._set_response()
    
    def do_GET(self):
        # Simple status endpoint
        self._set_response()
        response = {'status': 'SAP Endpoint is running', 'message': 'Use POST to send IDoc-XML data'}
        self.wfile.write(json.dumps(response).encode('utf-8'))
        logger.info(f"GET request received at {self.path}")
    
    def do_POST(self):
        # Reset log files for each new request
        reset_log_files()
        logger.info("Log files reset for new request")
        
        # Get content length
        content_length = int(self.headers['Content-Length'])
        # Read the data
        post_data = self.rfile.read(content_length)
        
        # Parse the URL to get query parameters
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Log the received data
        logger.info(f"POST request received at {self.path}")
        logger.info(f"Query parameters: {params}")
        
        # Check if it's XML data
        try:
            # Try to parse as XML
            xml_data = post_data.decode('utf-8')
            root = ET.fromstring(xml_data)
            
            # Log a message about receiving XML
            logger.info("Received XML data (see sap_endpoint_xml.log for complete XML)")
            
            # Write the complete XML to a separate file
            with open(XML_FILE, 'w') as f:
                f.write(xml_data)
            
            # Count the number of IDOCs
            idocs = root.findall('.//IDOC')
            idoc_count = len(idocs)
            logger.info(f"Number of IDOCs in XML: {idoc_count}")
            
            # Log information about each IDOC
            for idx, idoc in enumerate(idocs):
                idoc_id = idoc.get('BEGIN', f'Unknown-{idx}')
                logger.info(f"IDOC {idx+1}/{idoc_count} - ID: {idoc_id}")
                
                # Log the entire IDOC structure
                logger.info(f"  IDOC XML Structure:")
                
                # Convert IDOC element to string and log it
                idoc_str = ET.tostring(idoc, encoding='unicode')
                logger.info(f"  {idoc_str}")
                
                # Also log specific fields for quick reference
                logger.info(f"  Key Fields Summary:")
                
                # Try to extract PO number
                po_elem = idoc.find('.//E1EDK02/BELNR')
                po_number = po_elem.text if po_elem is not None and po_elem.text else "N/A"
                logger.info(f"    PO Number: {po_number}")
                
                # Try to extract customer number
                cust_elem = idoc.find('.//E1EDKA1/PARTN')
                customer = cust_elem.text if cust_elem is not None and cust_elem.text else "N/A"
                logger.info(f"    Customer: {customer}")
                
                # Try to extract part number
                part_elem = idoc.find('.//E1EDP19/IDTNR')
                part_number = part_elem.text if part_elem is not None and part_elem.text else "N/A"
                logger.info(f"    Part Number: {part_number}")
                
                # Try to extract quantity
                qty_elem = idoc.find('.//E1EDP01/MENGE')
                quantity = qty_elem.text if qty_elem is not None and qty_elem.text else "N/A"
                logger.info(f"    Quantity: {quantity}")
                
                # Try to extract delivery date
                date_elem = idoc.find('.//E1EDK02/DATUM')
                delivery_date = date_elem.text if date_elem is not None and date_elem.text else "N/A"
                logger.info(f"    Delivery Date: {delivery_date}")
                
                # Try to extract currency
                currency_elem = idoc.find('.//E1EDK01/CURRENCY')
                currency = currency_elem.text if currency_elem is not None and currency_elem.text else "N/A"
                logger.info(f"    Currency: {currency}")
            
            # Simulate SAP processing
            # In a real scenario, this would validate the XML against SAP schemas
            # and process the data into the SAP system
            
            # Return success response
            self._set_response()
            response = {
                'status': 'success',
                'message': f'Received {idoc_count} IDOCs for processing',
                'details': 'This is a dummy SAP endpoint for demonstration purposes'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except ET.ParseError:
            # Not XML or invalid XML
            logger.error("Failed to parse XML data")
            self._set_response(400)
            response = {'status': 'error', 'message': 'Invalid XML data'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            # Other errors
            logger.error(f"Error processing request: {str(e)}")
            self._set_response(500)
            response = {'status': 'error', 'message': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))

def run_server():
    with socketserver.TCPServer(("", PORT), SAPEndpointHandler) as httpd:
        logger.info(f"SAP Endpoint server started at port {PORT}")
        print(f"SAP Endpoint server started at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            print("Server stopped")

if __name__ == "__main__":
    run_server()
