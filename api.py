import streamlit as st
from openai import OpenAI

# Function to validate OpenAI API key
def validate_api_key(openai_api_key):
    try:
        client = OpenAI(api_key=openai_api_key)
        client.models.list()
        return True, "✅ API Key validated successfully!"
    except Exception as e:
        return False, "❌ Invalid API Key. Please try again."

# Function to call OpenAI API for extraction
def extract_data_from_text(pdf_text, openai_api_key, prompts):
    client = OpenAI(api_key=openai_api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompts,
            temperature=0,
            top_p=0
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"⚠ Error calling OpenAI API: {e}")
        return None
