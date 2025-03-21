import streamlit as st
from openai import AzureOpenAI

# Azure OpenAI Configuration
AZURE_ENDPOINT = "https://momofssd1.openai.azure.com/"  # Your Azure OpenAI endpoint
AZURE_DEPLOYMENT = "gpt-4o"  # Replace with your actual deployment name
AZURE_API_VERSION = "2024-02-01"

# Function to validate OpenAI API key
def validate_api_key(openai_api_key):
    try:
        client = AzureOpenAI(
            api_key=openai_api_key,
            api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_ENDPOINT
        )
        client.models.list()
        return True, "✅ API Key validated successfully!"
    except Exception as e:
        return False, "❌ Invalid API Key. Please try again."

# Function to call OpenAI API for extraction
def extract_data_from_text(pdf_text, openai_api_key, prompts):
    client = AzureOpenAI(
        api_key=openai_api_key,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT
    )
    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=prompts,
            temperature=0,
            top_p=0
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"⚠ Error calling OpenAI API: {e}")
        return None
