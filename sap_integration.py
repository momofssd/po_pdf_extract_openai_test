import io
import datetime
import requests
import json

# Function to generate IDoc-XML data for SAP integration
def generate_idoc_xml_data(df):
    """
    Generate IDoc-XML data for SAP integration based on the provided guideline.
    
    Args:
        df (pandas.DataFrame): DataFrame containing purchase order data
    
    Returns:
        str: IDoc-XML data in a structured format
    """
    if df.empty:
        return None
    
    # Create a buffer to hold the XML data
    buffer = io.StringIO()
    
    # Write XML header
    buffer.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    buffer.write('<ORDERS05>\n')
    
    # Process each row in the DataFrame as a separate IDoc
    for idx, row in df.iterrows():
        # Get required fields, with fallbacks for missing data
        po_number = row.get('Purchase Order Number', f'PO{10000+idx}')
        customer_number = row.get('Customer Number', '')
        ship_to_number = row.get('Ship To Number', '')
        delivery_date = row.get('Required Delivery Date', '')
        customer_part_number = row.get('Customer Part Number', '')
        order_quantity = row.get('Order Quantity', '1')
        customer_name = row.get('Customer Name', '')
        
        # Format date if available (YYYYMMDD format)
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        formatted_delivery_date = current_date
        if delivery_date:
            try:
                # Try to parse the date and format it as YYYYMMDD for IDoc
                date_obj = datetime.datetime.strptime(delivery_date, '%Y-%m-%d')
                formatted_delivery_date = date_obj.strftime('%Y%m%d')
            except ValueError:
                # If date parsing fails, use current date
                pass
        
        # Generate a unique document number
        doc_number = f"DOC{1000 + idx:04d}"
        
        # Start IDoc record
        buffer.write(f'  <IDOC BEGIN="{doc_number}">\n')
        
        # E1EDK01: Header general data
        buffer.write('    <E1EDK01>\n')
        buffer.write('      <ACTION>0</ACTION>\n')
        buffer.write('      <CURRENCY>USD</CURRENCY>\n')
        buffer.write('    </E1EDK01>\n')
        
        # E1EDK14: Header org data - Order type (always "OR" as specified)
        buffer.write('    <E1EDK14>\n')
        buffer.write('      <QUALF>012</QUALF>\n')
        buffer.write('      <ORGID>OR</ORGID>\n')
        buffer.write('    </E1EDK14>\n')
        
        # E1EDK14: Header org data - PO type
        buffer.write('    <E1EDK14>\n')
        buffer.write('      <QUALF>019</QUALF>\n')
        buffer.write('      <ORGID>B2B</ORGID>\n')
        buffer.write('    </E1EDK14>\n')
        
        # E1EDKA1: Header partner info - Sold-to party
        buffer.write('    <E1EDKA1>\n')
        buffer.write('      <PARVW>AG</PARVW>\n')
        buffer.write(f'      <PARTN>{customer_number}</PARTN>\n')
        buffer.write('      <LIFNR>Vendor number at customer location</LIFNR>\n')
        buffer.write('    </E1EDKA1>\n')
        
        # E1EDKA1: Header partner info - Ship-to party
        buffer.write('    <E1EDKA1>\n')
        buffer.write('      <PARVW>WE</PARVW>\n')
        buffer.write(f'      <PARTN>{ship_to_number}</PARTN>\n')
        buffer.write('      <LIFNR>Vendor number at customer location</LIFNR>\n')
        if customer_name:
            buffer.write(f'      <NAME1>{customer_name}</NAME1>\n')
        buffer.write('    </E1EDKA1>\n')
        
        # E1EDK02: Header reference data - Customer PO
        buffer.write('    <E1EDK02>\n')
        buffer.write('      <QUALF>001</QUALF>\n')
        buffer.write(f'      <BELNR>{po_number}</BELNR>\n')
        buffer.write(f'      <DATUM>{formatted_delivery_date}</DATUM>\n')
        buffer.write('    </E1EDK02>\n')
        
        # E1EDP01: Item reference data
        buffer.write('    <E1EDP01>\n')
        buffer.write('      <POSEX>1</POSEX>\n')  # Item number, using 1 as default
        buffer.write(f'      <MENGE>{order_quantity}</MENGE>\n')
        buffer.write('      <MENEE>KG</MENEE>\n')  # UOM is always KG as specified
        buffer.write('    </E1EDP01>\n')
        
        # E1EDP02: Item reference data - Customer PO
        buffer.write('    <E1EDP02>\n')
        buffer.write('      <QUALF>001</QUALF>\n')
        buffer.write(f'      <BELNR>{po_number}</BELNR>\n')
        buffer.write('      <ZEILE>1</ZEILE>\n')  # Item number, using 1 as default
        buffer.write(f'      <DATUM>{formatted_delivery_date}</DATUM>\n')
        buffer.write('    </E1EDP02>\n')
        
        # E1EDP03: Item date segment - Customer RDD
        buffer.write('    <E1EDP03>\n')
        buffer.write('      <IDDAT>002</IDDAT>\n')
        buffer.write(f'      <DATUM>{formatted_delivery_date}</DATUM>\n')
        buffer.write('    </E1EDP03>\n')
        
        # E1EDPA1: Item partner info - End user
        buffer.write('    <E1EDPA1>\n')
        buffer.write('      <PARVW>EN</PARVW>\n')
        buffer.write(f'      <PARTN>{customer_number}</PARTN>\n')
        buffer.write('    </E1EDPA1>\n')
        
        # E1EDP19: Item Object Identification - Customer material
        buffer.write('    <E1EDP19>\n')
        buffer.write('      <QUALF>001</QUALF>\n')
        buffer.write(f'      <IDTNR>{customer_part_number}</IDTNR>\n')
        buffer.write('    </E1EDP19>\n')
        
        # End IDoc record
        buffer.write('  </IDOC>\n')
    
    # Close root element
    buffer.write('</ORDERS05>\n')
    
    # Get the complete XML data
    xml_data = buffer.getvalue()
    buffer.close()
    
    return xml_data

# Function to send IDoc-XML data to SAP endpoint
def send_idoc_xml_to_sap(xml_data, endpoint_url="http://localhost:8000/idoc"):
    """
    Send IDoc-XML data to SAP endpoint.
    
    Args:
        xml_data (str): IDoc-XML data to send
        endpoint_url (str): URL of the SAP endpoint
    
    Returns:
        dict: Response from the SAP endpoint
    """
    if not xml_data:
        return {"status": "error", "message": "No XML data to send"}
    
    try:
        # Set headers for XML content
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/json'
        }
        
        # Send POST request to SAP endpoint
        response = requests.post(
            endpoint_url,
            data=xml_data,
            headers=headers,
            timeout=30  # 30 seconds timeout
        )
        
        # Check if request was successful
        if response.status_code == 200:
            try:
                # Try to parse JSON response
                return response.json()
            except json.JSONDecodeError:
                # If response is not JSON, return text
                return {"status": "success", "message": response.text}
        else:
            # Return error if request failed
            return {
                "status": "error",
                "message": f"Request failed with status code {response.status_code}",
                "details": response.text
            }
    except requests.exceptions.ConnectionError:
        # Return error if connection failed
        return {
            "status": "error",
            "message": f"Failed to connect to SAP endpoint at {endpoint_url}",
            "details": "Make sure the SAP endpoint server is running"
        }
    except Exception as e:
        # Return error for any other exception
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "details": "Check logs for more information"
        }

# Function to generate ANSI X12 850 data for SAP integration
def generate_ansi_x12_850_data(df):
    """
    Generate ANSI X12 850 (Purchase Order) data for SAP integration in raw EDI format.
    
    Args:
        df (pandas.DataFrame): DataFrame containing purchase order data
    
    Returns:
        str: ANSI X12 850 data in raw EDI format
    """
    if df.empty:
        return None
    
    # Create a buffer to hold the data
    buffer = io.StringIO()
    
    # Process each row in the DataFrame as a separate EDI document
    for idx, row in df.iterrows():
        # Get required fields, with fallbacks for missing data
        po_number = row.get('Purchase Order Number', f'PO{10000+idx}')
        customer_number = row.get('Customer Number', '')
        ship_to_number = row.get('Ship To Number', '')
        delivery_date = row.get('Required Delivery Date', '')
        customer_part_number = row.get('Customer Part Number', '')
        order_quantity = row.get('Order Quantity', '1')
        
        # Format date if available (YYYYMMDD format)
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        formatted_delivery_date = current_date
        if delivery_date:
            try:
                # Try to parse the date and format it as YYYYMMDD for EDI
                date_obj = datetime.datetime.strptime(delivery_date, '%Y-%m-%d')
                formatted_delivery_date = date_obj.strftime('%Y%m%d')
            except ValueError:
                # If date parsing fails, use current date
                pass
        
        # Generate a unique control number for this document
        control_number = f"{1000 + idx:04d}"
        
        # Write EDI segments according to X12 850 format
        
        # ST - Transaction Set Header
        buffer.write(f"ST*850*{control_number}\n")
        
        # BEG - Beginning Segment for Purchase Order
        # BEG*00*SA*[PO Number]**[Current Date]
        buffer.write(f"BEG*00*SA*{po_number}**{current_date}\n")
        
        # N1 - Ship To
        if ship_to_number:
            buffer.write(f"N1*ST**92*{ship_to_number}\n")
        
        # N1 - Buyer/Customer
        if customer_number:
            buffer.write(f"N1*BY**92*{customer_number}\n")
        
        # DTM - Required Delivery Date
        buffer.write(f"DTM*002*{formatted_delivery_date}\n")
        
        # PO1 - Purchase Order Line Item
        # PO1*[Line Number]*[Quantity]*[Unit of Measure]***BP*[Part Number]
        buffer.write(f"PO1*1*{order_quantity}*KG***BP*{customer_part_number}\n")
        
        # CTT - Transaction Totals
        buffer.write(f"CTT*1\n")
        
        # SE - Transaction Set Trailer
        # Count the number of segments (ST, BEG, N1s, DTM, PO1, CTT, SE)
        segment_count = 5  # ST, BEG, DTM, PO1, CTT
        if ship_to_number:
            segment_count += 1  # N1 Ship To
        if customer_number:
            segment_count += 1  # N1 Buyer
        
        buffer.write(f"SE*{segment_count}*{control_number}\n\n")
    
    # Get the complete data
    ansi_data = buffer.getvalue()
    buffer.close()
    
    return ansi_data
