import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.api import get_documents, retrieve_clauses
from utils.styles import apply_judicial_theme, info_card

st.set_page_config(page_title="Search - Legal Document Intelligence", page_icon="🔍", layout="wide")
apply_judicial_theme()

st.markdown("<h1 style='text-align: center; color: #1F3A5E;'>🔍 SEMANTIC SEARCH</h1>", unsafe_allow_html=True)
st.markdown("---")

if "query" not in st.session_state:
    st.session_state.query = ""

docs = get_documents()
if docs.get("total", 0) == 0:
    st.warning("📌 No documents indexed yet. Please upload documents first.")
    st.stop()

indices = [d["index_name"] for d in docs["documents"]]
selected_index = st.selectbox("Select document index:", indices)

st.markdown("<h3 style='color: #1F3A5E;'>Search Query</h3>", unsafe_allow_html=True)

examples = ["Termination", "Notice Period", "Penalty", "Confidentiality"]
cols = st.columns(4)
for i, ex in enumerate(examples):
    with cols[i]:
        if st.button(ex, use_container_width=True, key=f"ex_{i}"):
            st.session_state.query = ex

query = st.text_input(
    "Enter your search query:",
    value=st.session_state.query,
    placeholder="Search for clauses, terms, conditions..."
)
st.session_state.query = query

top_k = st.slider("Number of results:", 1, 10, 5)

if st.button("🔎 Search", use_container_width=True):
    if not query.strip():
        st.error("Please enter a search query.")
    else:
        with st.spinner("Searching..."):
            result = retrieve_clauses(selected_index, query, top_k)
            
            # Debug: Show what we got back
            # st.write("DEBUG:", result)
            
            # Check for errors first
            if result.get("status") == "error" or result.get("error"):
                error_msg = result.get("error") or result.get("message", "Unknown error")
                st.error(f"Search failed: {error_msg}")
                st.info("💡 Possible fixes:\n- Ensure the document is properly indexed\n- Try a different search query\n- Check that backend is running")
            else:
                # Try to get clauses from either "clauses" or "results" key
                clauses = result.get("clauses", result.get("results", []))
                
                if clauses and len(clauses) > 0:
                    st.success(f"Found {len(clauses)} relevant clauses")
                    
                    # Show statistics if available
                    if result.get("stats"):
                        col1, col2, col3 = st.columns(3)
                        stats = result["stats"]
                        with col1:
                            st.metric("Max Score", f"{stats.get('max_score', 0):.4f}")
                        with col2:
                            st.metric("Avg Score", f"{stats.get('avg_score', 0):.4f}")
                        with col3:
                            st.metric("Min Score", f"{stats.get('min_score', 0):.4f}")
                        st.markdown("---")
                    
                    # Display clauses
                    for i, clause in enumerate(clauses, 1):
                        with st.expander(f"📄 Result {i} - {clause.get('source', 'Unknown')}", expanded=i==1):
                            # Show content
                            content = clause.get("content", "No content")
                            st.markdown(content)
                            
                            # Show metadata
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                relevance = clause.get('relevance_score', 0)
                                st.metric("Relevance Score", f"{relevance:.4f}")
                            with col2:
                                st.metric("Word Count", clause.get('word_count', 0))
                            with col3:
                                source = clause.get('source', 'N/A')
                                st.metric("Source", source.split('/')[-1] if '/' in source else source)
                            
                            # Show special markers
                            markers = []
                            if clause.get('has_dates'):
                                markers.append("📅 Contains Dates")
                            if clause.get('has_monetary_amounts'):
                                markers.append("💰 Contains Monetary Amounts")
                            if markers:
                                st.info(" | ".join(markers))
                else:
                    st.info("No clauses found matching your query. Try a different search term.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>💡 Search across all indexed documents for relevant clauses and terms</p>", unsafe_allow_html=True)
