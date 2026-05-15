import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.api import get_documents, get_clauses, get_risk, get_compliance, get_summary, get_structured
from utils.styles import apply_judicial_theme

st.set_page_config(page_title="Analysis - Legal Document Intelligence", page_icon="📊", layout="wide")
apply_judicial_theme()

st.markdown("<h1 style='text-align: center; color: #1F3A5E;'>📊 DOCUMENT ANALYSIS</h1>", unsafe_allow_html=True)
st.markdown("---")

docs = get_documents()
if docs.get("total", 0) == 0:
    st.warning("📌 No documents indexed yet. Please upload documents first.")
    st.stop()

indices = [d["index_name"] for d in docs["documents"]]
selected_index = st.selectbox("Select document index:", indices)

top_k = st.slider("Number of items to retrieve:", 1, 10, 5)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Clauses", "Risk", "Compliance", "Summary", "Structured"])

with tab1:
    st.markdown("<h3 style='color: #1F3A5E;'>📋 Key Clauses</h3>", unsafe_allow_html=True)
    if st.button("📖 Retrieve Clauses", use_container_width=True, key="btn_clauses"):
        with st.spinner("Retrieving clauses..."):
            result = get_clauses(selected_index, top_k)
            if result.get("error"):
                st.error(f"Failed to retrieve clauses: {result['error']}")
            else:
                clauses = result.get("clauses", [])
                if clauses:
                    st.success(f"Found {len(clauses)} key clauses")
                    for i, clause in enumerate(clauses, 1):
                        with st.expander(f"Clause {i}"):
                            st.markdown(clause.get("content", clause.get("text", "")))
                else:
                    st.info("No clauses found.")

with tab2:
    st.markdown("<h3 style='color: #1F3A5E;'>⚠️ Risk Analysis</h3>", unsafe_allow_html=True)
    if st.button("🔍 Analyze Risks", use_container_width=True, key="btn_risk"):
        with st.spinner("Analyzing risks..."):
            result = get_risk(selected_index, top_k)
            if result.get("error"):
                st.error(f"Failed to analyze risks: {result['error']}")
            else:
                risks = result.get("risks", [])
                if risks:
                    severity = result.get("severity", "unknown").upper()
                    avg_score = result.get("avg_score", 0)
                    
                    # Color code by severity
                    if severity == "HIGH":
                        st.error(f"⚠️ **HIGH RISK** - Average Score: {avg_score}")
                    elif severity == "MEDIUM":
                        st.warning(f"⚠️ **MEDIUM RISK** - Average Score: {avg_score}")
                    else:
                        st.info(f"✅ **LOW RISK** - Average Score: {avg_score}")
                    
                    for i, risk in enumerate(risks, 1):
                        score = risk.get("score", 0)
                        keywords = risk.get("matched_keywords", [])
                        with st.expander(f"Risk {i} (Score: {score})", expanded=False):
                            st.markdown(risk.get("content", ""))
                            if keywords:
                                st.caption(f"🔴 Risk Keywords: {', '.join(keywords)}")
                else:
                    st.info("No risk analysis available.")

with tab3:
    st.markdown("<h3 style='color: #1F3A5E;'>✅ Compliance Review</h3>", unsafe_allow_html=True)
    st.info("� Compliance check requires document upload. Use the Upload page to run compliance checks.")
    if st.button("📋 Check Compliance", use_container_width=True, key="btn_compliance", disabled=True):
        pass

with tab4:
    st.markdown("<h3 style='color: #1F3A5E;'>📄 Document Summary</h3>", unsafe_allow_html=True)
    if st.button("📊 Generate Summary", use_container_width=True, key="btn_summary"):
        with st.spinner("Generating summary..."):
            result = get_summary(selected_index, top_k)
            if result.get("error"):
                st.error(f"Failed to generate summary: {result['error']}")
            else:
                summary_text = result.get("summary", "No summary available.")
                if summary_text and summary_text != "No content available to summarize.":
                    st.success("✅ Summary generated")
                    # Display the summary with better formatting
                    st.markdown(summary_text)
                else:
                    st.warning("📝 Unable to generate a detailed summary. The document may not have enough structured information.")

with tab5:
    st.markdown("<h3 style='color: #1F3A5E;'>🗂️ Structured Extraction</h3>", unsafe_allow_html=True)
    if st.button("📑 Extract Structured Data", use_container_width=True, key="btn_structured"):
        with st.spinner("Extracting structured data..."):
            result = get_structured(selected_index, top_k)
            if result.get("error"):
                st.error(f"Failed to extract data: {result['error']}")
            else:
                structured_data = result.get("structured", {})
                if structured_data:
                    st.success("Structured data extracted")
                    st.json(structured_data)
                else:
                    st.info("No structured data available.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>💡 Perform comprehensive analysis on your indexed documents</p>", unsafe_allow_html=True)
