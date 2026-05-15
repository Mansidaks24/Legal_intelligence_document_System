import streamlit as st
import sys
from pathlib import Path
import time
from urllib.parse import quote

sys.path.append(str(Path(__file__).parent.parent))
from utils.api import delete_index, get_documents, upload_document
from utils.styles import apply_judicial_theme, success_banner, error_banner, professional_celebration

st.set_page_config(page_title="Upload - Legal Document Intelligence", page_icon="📤", layout="wide")
apply_judicial_theme()

# Initialize session state
if "deletion_in_progress" not in st.session_state:
    st.session_state.deletion_in_progress = False
if "show_delete_confirmation" not in st.session_state:
    st.session_state.show_delete_confirmation = False
if "selected_for_deletion" not in st.session_state:
    st.session_state.selected_for_deletion = None
if "last_uploaded_index" not in st.session_state:
    st.session_state.last_uploaded_index = None

st.markdown("<h1 style='text-align: center; color: #1F3A5E;'>📤 UPLOAD DOCUMENTS</h1>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)

# ==================== UPLOAD SECTION ====================
with col1:
    st.markdown("<h3 style='color: #1F3A5E;'>📁 Upload New Document</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        st.write(f"Selected file: **{uploaded_file.name}**")
        st.write(f"File size: **{uploaded_file.size / 1024:.2f} KB**")
        
        if st.button("⬆️ Upload Document", use_container_width=True, key="upload_btn"):
            with st.spinner("Processing document..."):
                mime_types = {
                    "pdf": "application/pdf",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
                file_ext = uploaded_file.name.split(".")[-1].lower()
                mime_type = mime_types.get(file_ext, "application/octet-stream")
                
                try:
                    result = upload_document(
                        uploaded_file.read(),
                        uploaded_file.name,
                        mime_type
                    )
                    
                    if result and isinstance(result, dict):
                        if result.get("status") == "success":
                            # Extract index_name - try multiple field names
                            index_name = (
                                result.get('index_name') or 
                                result.get('document_id') or 
                                result.get('id') or 
                                uploaded_file.name
                            )
                            
                            # Store for reference
                            st.session_state.last_uploaded_index = index_name
                            
                            professional_celebration()
                            st.success(f"✅ Document uploaded successfully! Index: **{index_name}**")
                            
                            # Show the exact name to use for deletion
                            st.info(f"📝 Use this exact name for deletion: `{index_name}`")
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            error_msg = result.get('message', 'Unknown error occurred')
                            st.error(f"❌ Upload failed: {error_msg}")
                    else:
                        st.error("❌ Invalid response from server")
                        
                except Exception as e:
                    st.error(f"❌ Upload error: {str(e)}")

# ==================== DELETE SECTION ====================
with col2:
    st.markdown("<h3 style='color: #1F3A5E;'>🗑️ Delete Index</h3>", unsafe_allow_html=True)
    
    try:
        docs = get_documents()
        
        if docs and isinstance(docs, dict) and docs.get("total", 0) > 0:
            documents = docs.get("documents", [])
            
            if documents:
                # Extract exact index names from backend
                indices_data = []
                for doc in documents:
                    # Try different field names that backends might use
                    index_name = (
                        doc.get("index_name") or 
                        doc.get("name") or 
                        doc.get("id") or 
                        doc.get("document_id") or
                        str(doc.get("filename", "unknown"))
                    )
                    indices_data.append({
                        "name": index_name,
                        "full_data": doc
                    })
                
                # Get just the names for dropdown
                indices = [d["name"] for d in indices_data]
                
                st.write(f"**Found {len(indices)} document(s)**")
                
                selected_index = st.selectbox(
                    "Select an index to delete",
                    indices,
                    key="index_selector"
                )
                
                # Show metadata of selected index
                selected_data = next((d for d in indices_data if d["name"] == selected_index), None)
                if selected_data and len(str(selected_data["full_data"])) < 500:
                    with st.expander("📋 Index Details"):
                        st.json(selected_data["full_data"])
                
                col_del_1, col_del_2 = st.columns(2)
                
                with col_del_1:
                    if st.button("🗑️ Delete Index", use_container_width=True, key="delete_btn"):
                        st.session_state.show_delete_confirmation = True
                        st.session_state.selected_for_deletion = selected_index
                        st.rerun()
                
                with col_del_2:
                    if st.session_state.show_delete_confirmation and st.session_state.selected_for_deletion == selected_index:
                        if st.button("✅ Confirm Delete", use_container_width=True, key="confirm_delete_btn"):
                            st.session_state.deletion_in_progress = True
                            st.rerun()
                
                # Perform deletion if confirmed
                if st.session_state.deletion_in_progress and st.session_state.selected_for_deletion == selected_index:
                    with st.spinner(f"Deleting index '{selected_index}'..."):
                        try:
                            st.info(f"🔄 Attempting to delete: `{selected_index}`")
                            result = delete_index(selected_index)
                            
                            if result and isinstance(result, dict):
                                status = result.get("status", "").lower()
                                message = result.get("message", "")
                                
                                # Check for success
                                success_indicators = ["success", "deleted", "deleted successfully"]
                                is_success = any(
                                    indicator in str(status).lower() or 
                                    indicator in message.lower() 
                                    for indicator in success_indicators
                                )
                                
                                if is_success:
                                    st.session_state.deletion_in_progress = False
                                    st.session_state.show_delete_confirmation = False
                                    st.session_state.selected_for_deletion = None
                                    
                                    if hasattr(st, 'success_banner'):
                                        success_banner()
                                    st.success(f"✅ Index **{selected_index}** deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                
                                elif "not found" in message.lower() or status == "not_found":
                                    st.session_state.deletion_in_progress = False
                                    st.session_state.show_delete_confirmation = False
                                    
                                    st.warning(f"⚠️ Index **{selected_index}** not found.")
                                    st.write("**Possible causes:**")
                                    st.write("- Index name doesn't match what's stored in backend")
                                    st.write("- Index was already deleted")
                                    st.write("- Different naming convention (case-sensitive?)")
                                    st.write("\n**Run diagnostic:** `python check_indices.py`")
                                
                                else:
                                    st.session_state.deletion_in_progress = False
                                    st.session_state.show_delete_confirmation = False
                                    error_msg = message if message else f"Status: {status}"
                                    st.error(f"❌ Delete failed: {error_msg}")
                            else:
                                st.session_state.deletion_in_progress = False
                                st.session_state.show_delete_confirmation = False
                                st.error("❌ Invalid response from server")
                                
                        except Exception as e:
                            st.session_state.deletion_in_progress = False
                            st.session_state.show_delete_confirmation = False
                            st.error(f"❌ Delete error: {str(e)}")
                
                # Cancel button
                if st.session_state.show_delete_confirmation:
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_delete_btn"):
                        st.session_state.show_delete_confirmation = False
                        st.session_state.selected_for_deletion = None
                        st.rerun()
            else:
                st.info("ℹ️ No indices found to delete.")
        else:
            st.info("ℹ️ No indices available to delete.")
            
    except Exception as e:
        st.error(f"❌ Error loading indices: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>💡 Upload PDF or DOCX files to create searchable indices</p>", unsafe_allow_html=True)