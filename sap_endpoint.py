import http.server
import socketserver
import json
import logging
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sap_endpoint.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SAP-Endpoint")

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
            logger.info(f"Received XML data: {xml_data[:500]}...")  # Log first 500 chars
            
            # Count the number of IDOCs
            idocs = root.findall('.//IDOC')
            idoc_count = len(idocs)
            logger.info(f"Number of IDOCs in XML: {idoc_count}")
            
            # Log information about each IDOC
            for idx, idoc in enumerate(idocs):
                idoc_id = idoc.get('BEGIN', f'Unknown-{idx}')
                logger.info(f"IDOC {idx+1}/{idoc_count} - ID: {idoc_id}")
                
                # Try to extract PO number
                po_elem = idoc.find('.//E1EDK02/BELNR')
                po_number = po_elem.text if po_elem is not None and po_elem.text else "N/A"
                logger.info(f"  PO Number: {po_number}")
                
                # Try to extract customer number
                cust_elem = idoc.find('.//E1EDKA1/PARTN')
                customer = cust_elem.text if cust_elem is not None and cust_elem.text else "N/A"
                logger.info(f"  Customer: {customer}")
                
                # Try to extract part number
                part_elem = idoc.find('.//E1EDP19/IDTNR')
                part_number = part_elem.text if part_elem is not None and part_elem.text else "N/A"
                logger.info(f"  Part Number: {part_number}")
                
                # Try to extract quantity
                qty_elem = idoc.find('.//E1EDP01/MENGE')
                quantity = qty_elem.text if qty_elem is not None and qty_elem.text else "N/A"
                logger.info(f"  Quantity: {quantity}")
            
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
