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
            
            if result.get("error"):
                st.error(f"Search failed: {result['error']}")
            else:
                clauses = result.get("results", [])
                if clauses:
                    st.success(f"Found {len(clauses)} relevant clauses")
                    for i, clause in enumerate(clauses, 1):
                        with st.expander(f"📄 Result {i}", expanded=i==1):
                            st.markdown(clause.get("content", ""))
                            relevance = clause.get('relevance_score', 0)
                            st.markdown(f"**Relevance Score:** {relevance:.2f} | **Source:** {clause.get('source', 'N/A')}")
                else:
                    st.info("No clauses found matching your query.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>💡 Search across all indexed documents for relevant clauses and terms</p>", unsafe_allow_html=True)
