import streamlit as st
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))
from utils.api import get_documents, get_llm_summary, get_llm_risk, get_llm_structured
from utils.styles import apply_judicial_theme

st.set_page_config(page_title="LLM Insights - Legal Document Intelligence", page_icon="🤖", layout="wide")
apply_judicial_theme()

st.markdown("<h1 style='text-align: center; color: #1F3A5E;'>🤖 AI INSIGHTS (POWERED BY GROQ)</h1>", unsafe_allow_html=True)
st.markdown("---")

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.warning("⚠️ GROQ_API_KEY not configured. Please set it in the .env file.")
    st.stop()

docs = get_documents()
if docs.get("total", 0) == 0:
    st.warning("📌 No documents indexed yet. Please upload documents first.")
    st.stop()

indices = [d["index_name"] for d in docs["documents"]]
selected_index = st.selectbox("Select document index:", indices)

tab1, tab2, tab3 = st.tabs(["AI Summary", "AI Risk Analysis", "AI Structured"])

with tab1:
    st.markdown("<h3 style='color: #1F3A5E;'>📝 AI-Generated Summary</h3>", unsafe_allow_html=True)
    if st.button("✨ Generate AI Summary", use_container_width=True, key="btn_llm_summary"):
        with st.spinner("Generating AI summary with Groq..."):
            result = get_llm_summary(selected_index)
            if result.get("error"):
                st.error(f"Failed to generate summary: {result['error']}")
            else:
                st.markdown(result.get("summary", "No summary available."))

with tab2:
    st.markdown("<h3 style='color: #1F3A5E;'>⚠️ AI Risk Analysis</h3>", unsafe_allow_html=True)
    if st.button("🔍 Analyze with AI", use_container_width=True, key="btn_llm_risk"):
        with st.spinner("Analyzing risks with Groq AI..."):
            result = get_llm_risk(selected_index)
            if result.get("error"):
                st.error(f"Failed to analyze risks: {result['error']}")
            else:
                st.markdown(result.get("risk_analysis", "No analysis available."))

with tab3:
    st.markdown("<h3 style='color: #1F3A5E;'>🗂️ AI Structured Extraction</h3>", unsafe_allow_html=True)
    if st.button("📑 Extract with AI", use_container_width=True, key="btn_llm_structured"):
        with st.spinner("Extracting structured data with Groq..."):
            result = get_llm_structured(selected_index)
            if result.get("error"):
                st.error(f"Failed to extract data: {result['error']}")
            else:
                st.json(result.get("structured", {}))

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>💡 Powered by Groq (llama-3.3-70b-versatile)</p>", unsafe_allow_html=True)
