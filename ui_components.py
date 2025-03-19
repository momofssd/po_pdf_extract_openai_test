import streamlit as st
import pandas as pd
import io
import base64
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

# Function to display PDF selector and viewer
def display_pdf_viewer(dataframe):
    if dataframe is not None:
        # Create a selectbox to choose which PDF to view
        st.write("### Select PDF to View")
        
        # Get unique filenames
        unique_filenames = dataframe['filename'].unique().tolist()
        
        # Create a selectbox for PDF selection
        if unique_filenames:
            # Add a default "Select PDF" option
            options = ["Select PDF"] + unique_filenames
            selected_option = st.selectbox(
                "Choose a PDF to view:",
                options,
                index=0,
                key="pdf_selector"
            )
            
            # Update selected PDF when a real PDF is selected (not the default option)
            if selected_option != "Select PDF":
                if not st.session_state.selected_row or st.session_state.selected_row['filename'] != selected_option:
                    st.session_state.selected_row = {'filename': selected_option}
                    st.rerun()
            else:
                # Clear selection if "Select PDF" is chosen
                if st.session_state.selected_row:
                    st.session_state.selected_row = None
                    st.rerun()
        
        # Display the selected PDF if available
        if st.session_state.selected_row and st.session_state.selected_row['filename'] in st.session_state.pdf_contents:
            filename = st.session_state.selected_row['filename']
            pdf_bytes = st.session_state.pdf_contents[filename]
            
            # Create an expander for the PDF
            with st.expander(f"📄 PDF Preview: {filename}", expanded=True):
                # Display PDF using PDF.js
                # Create a temporary file to store the PDF
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    # Write PDF bytes to the temporary file
                    tmp_file.write(pdf_bytes)
                    tmp_file_path = tmp_file.name
                
                # Display the PDF using Streamlit
                with open(tmp_file_path, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF",
                        data=f,
                        file_name=filename,
                        mime="application/pdf"
                    )
                    
                # Use Streamlit's components.html for PDF display
                st.write(f"### Viewing: {filename}")
                
                # Create a simple message about PDF viewing limitations
                st.info("""
                Due to browser security restrictions, embedded PDF viewing is not available in Streamlit Cloud.
                Please use the download button above to view the PDF.
                """)
                
                # Add a second download button with a more prominent style
                st.markdown("""
                <div style="text-align: center; margin: 20px 0;">
                    <p style="font-size: 16px; margin-bottom: 10px;">Click the button below to view the PDF:</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add another download button
                with open(tmp_file_path, "rb") as f:
                    st.download_button(
                        label="👁️ View PDF",
                        data=f,
                        file_name=filename,
                        mime="application/pdf",
                        key="view_pdf_button"
                    )
                
                # Clean up the temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
