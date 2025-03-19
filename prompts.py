def get_system_message():
    return (
        "You are an AI extracting relevant content from a purchase order. "
        "Find the following details and return ONLY a valid JSON object with these fields:"
        "\n- Customer Name (Look for contetns in terms and condition, header, footer section, website link, )"
        "- Purchase Order Number"
        "\n- Required Delivery Date (convert to ISO format YYYY-MM-DD)" 
        "\n- Material Number (Extract from the line item section, ignore `material description`,usually in the same row as 'Order Qty' and 'UOM'),(it could have different naming convenstion such as `Our Ref`)"
        "\n- Order Quantity in kg (only the converted kg value, if the UOM is not specificied in kg or lb, consider it as kg, do not include pounds or extra text, round down to the nearest integer)"
        "\n- Delivery Address (extract ONLY the 'SHIP TO' address, includes distribution name if it is there, ignore all other addresses including 'Vendor', 'Invoice', 'Billing', and any address containing 'PO Box')"
        "\n\nIMPORTANT: "
        "- Return ONLY a valid JSON object. Do NOT include explanations, introductions, or Markdown formatting."
        "- Ensure 'Order Quantity in kg' is a clean number without thousand separators or extra text."
        "- Ensure 'Required Delivery Date' follows ISO 8601 format (YYYY-MM-DD)."
        "- Ensure 'Delivery Address' is the correct 'SHIP TO' address."
        "- Ignore addresses related to 'Vendor', 'Invoice', 'Billing', 'Remit To', 'PO Box', or 'Mailing Address'."
        "- Ignore Material Number related to 'Vendor', 'Invoice', 'Billing', 'Remit To', 'PO Box', or 'Mailing Ref','Your material number'."
        "- Ignore **Price per unit** label."
    )

def get_multi_line_prompt():
    return (
        "Analyze the purchase order details provided. If the item section contains more than one item number, this indicates there are multiple purchase order lines. "
        "In that case, extract and output each line separately as a JSON array, where each element represents a single purchase order line with all its details. "
        "If there's only one line, output it as a single JSON object. Ensure that no line is omitted."
        "\n\nIMPORTANT: Format the Delivery Address as a single line with spaces instead of line breaks."
    )

def create_prompts(pdf_text):
    system_message = get_system_message()
    user_prompt = f"Extract relevant details from the following purchase order:\n{pdf_text}"
    
    prompts = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt},
    ]
    
    # Add multi-line prompt
    prompts.append({
        "role": "system",
        "content": get_multi_line_prompt()
    })
    
    return prompts