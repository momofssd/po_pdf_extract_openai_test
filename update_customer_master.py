import pandas as pd
import json

# Load the Excel file (update 'your_file.xlsx' with the actual file path)
file_path = "customer master.xlsx"
df = pd.read_excel(file_path)

# Normalize 'Customer Number' (strip spaces and convert to uppercase)
df["Customer Number"] = df["Customer Number"].astype(str).str.strip().str.upper()

# Fill empty 'Customer Name' downward to ensure each row has a name
df["Customer Name"] = df["Customer Name"].fillna(method="ffill")

# Convert DataFrame to JSON-like dictionary
customer_dict = {}

for _, row in df.iterrows():
    cust_num = row["Customer Number"]
    cust_name = row["Customer Name"]
    ship_to_num = row["Ship-To Number"]
    ship_to_addr = row["Ship-To Address"]

    if cust_num not in customer_dict:
        customer_dict[cust_num] = {
            "customer_names": set(),  # Using a set to handle multiple names
            "ship_to": {}
        }

    customer_dict[cust_num]["customer_names"].add(cust_name)

    if pd.notna(ship_to_num) and pd.notna(ship_to_addr):
        customer_dict[cust_num]["ship_to"][ship_to_num] = ship_to_addr

# Convert sets to lists for JSON serialization
for cust_num in customer_dict:
    customer_dict[cust_num]["customer_names"] = list(customer_dict[cust_num]["customer_names"])

# Convert dictionary to JSON
json_output = json.dumps(customer_dict, indent=4)

# Save JSON to a file
output_file = "customer_master_data.json"
with open(output_file, "w") as json_file:
    json_file.write(json_output)

# Print confirmation message
print(f"JSON file '{output_file}' has been successfully created!")
