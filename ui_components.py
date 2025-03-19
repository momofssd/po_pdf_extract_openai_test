import streamlit as st
import pandas as pd
import io
from session_state import reset_session_state
from data_processing import convert_to_dataframe

# Function to create sidebar components
def create_sidebar(openai_api_key_callback):
    with st.sidebar:
        st.header("🔑 API Key & Upload")

        # User enters OpenAI API key
        openai_api_key = st.text_input("Enter OpenAI API Key", type="password")

        if st.button("Validate API Key"):
            is_valid, message = openai_api_key_callback(openai_api_key)
            if is_valid:
                st.session_state.api_key_valid = True
                st.success(message)
            else:
                st.session_state.api_key_valid = False
                st.error(message)

        # File uploader with dynamic key (forces reset)
        uploaded_files = st.file_uploader(
            "📂 Upload Purchase Order PDFs", 
            type="pdf", 
            accept_multiple_files=True, 
            key=st.session_state.uploader_key  # Dynamic key to reset uploader
        )

        # Store uploaded files in session state
        if uploaded_files:
            st.session_state.uploaded_files_list = uploaded_files
            st.session_state.processed = False  # Ensure files aren't processed immediately
            st.success(f"📂 {len(uploaded_files)} files uploaded. Click 'Process' to extract data.")

        # Reset Button (Clears UI and uploaded files)
        if st.button("Reset Files"):
            reset_session_state()
            st.rerun()  # Force full UI refresh

        # Process Button (Only appears when API key is valid and files exist)
        process_clicked = False
        if st.session_state.api_key_valid and st.session_state.uploaded_files_list:
            if st.button("Process Files"):
                st.session_state.processed = True  # Set processing flag
                process_clicked = True
                
        return openai_api_key, process_clicked

# Function to display data and download options
def display_data_and_downloads():
    if st.session_state.get("extracted_data"):
        st.subheader("📥 Download Data")
        
        # Convert extracted data to DataFrame
        df = convert_to_dataframe(st.session_state.extracted_data)
        
        if not df.empty:
            # Display as editable table
            st.subheader(" Data Preview (Edit as needed)")
            
            # Create an editable dataframe
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=False,  # Show index for selection
                disabled=["filename"]  # Make filename column non-editable
            )
            
            # Update the session state with edited data
            st.session_state.edited_data = edited_df
            
            # Use edited data for downloads if available
            download_df = st.session_state.edited_data
            
            # Create CSV file in memory (more reliable than Excel in Streamlit)
            csv = download_df.to_csv(index=False)
            
            # Create download buttons
            col1, col2 = st.columns(2)
            with col1:
                # Create download button for CSV
                st.download_button(
                    label=" Download as CSV",
                    data=csv,
                    file_name="Purchase_Order_Data.csv",
                    mime="text/csv",
                )
            
            with col2:
                # Try to create Excel file if possible (with fallback)
                try:
                    output = io.BytesIO()
                    
                    # Try different Excel engines
                    try:
                        # Try using xlsxwriter first (often available in Streamlit)
                        download_df.to_excel(output, engine='xlsxwriter', index=False, sheet_name='Purchase Orders')
                        excel_available = True
                    except ImportError:
                        try:
                            # Try using openpyxl as fallback
                            download_df.to_excel(output, engine='openpyxl', index=False, sheet_name='Purchase Orders')
                            excel_available = True
                        except ImportError:
                            # If both fail, use basic Excel writer
                            download_df.to_excel(output, index=False, sheet_name='Purchase Orders')
                            excel_available = True
                    
                    # Create download button for Excel if available
                    if excel_available:
                        excel_data = output.getvalue()
                        st.download_button(
                            label=" Download as Excel",
                            data=excel_data,
                            file_name="Purchase_Order_Data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                except Exception as e:
                    st.info("Excel download not available. Please use CSV format.")
            
            return edited_df
        else:
            st.info("No data available to download. Process files to extract data.")
            return None
