import sys
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).parent))
from utils.api import health_check, get_documents, get_files
from utils.styles import apply_judicial_theme, success_banner, error_banner

st.set_page_config(
    page_title="Legal Document Intelligence System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_judicial_theme()

st.markdown("""
<style>
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        color: #1F3A5E;
        text-align: center;
        letter-spacing: 2px;
        margin-bottom: 0.5rem;
    }
    .main-subtitle {
        font-family: 'Lato', sans-serif;
        font-size: 1.3rem;
        color: #8B4513;
        text-align: center;
        font-style: italic;
        margin-bottom: 2rem;
    }
</style>
<h1 class="main-title">⚖️ LEGAL DOCUMENT INTELLIGENCE SYSTEM</h1>
<p class="main-subtitle">⚡ AI-Powered Analysis | 🏛️ Judicial Excellence | 📊 Intelligent Insights</p>
""", unsafe_allow_html=True)

st.markdown("---")

health = health_check()

if health:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🟢 Server Status", "ONLINE", delta="Connected")
    with col2:
        st.metric("📦 Version", health.get("version", "N/A"))
    with col3:
        st.metric("📚 Documents Indexed", health.get("total_documents_indexed", 0))
    with col4:
        vs = "✅ Ready" if health.get("vectorstore_exists") else "❌ Empty"
        st.metric("🗂️ Vector Store", vs)
    
    success_banner("✨ System Status", "All systems operational and ready for document analysis")
else:
    error_banner("🔴 Connection Error", "Cannot connect to backend! Ensure FastAPI is running on port 8000.")
    st.code("python -m uvicorn app:app --reload --port 8000", language="bash")
    st.stop()

st.markdown("---")

st.markdown("""
<h2 style="text-align: center; color: #1F3A5E; margin-top: 2rem;">📋 DOCUMENT OVERVIEW</h2>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(31, 58, 94, 0.05) 0%, rgba(212, 175, 55, 0.05) 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 5px solid #D4AF37;
    ">
        <h3 style="color: #1F3A5E; font-family: 'Playfair Display', serif; margin-top: 0;">📁 Uploaded Files</h3>
    </div>
    """, unsafe_allow_html=True)
    files = get_files()
    if files.get("total", 0) > 0:
        for f in files["files"]:
            icon = "📄" if f["file_type"] == "pdf" else "📝"
            st.markdown(f"**{icon} {f['filename']}** - {f['size_kb']} KB")
    else:
        st.info("📌 No files uploaded yet. Head to the Upload page to get started!")

with col2:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(31, 58, 94, 0.05) 0%, rgba(212, 175, 55, 0.05) 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 5px solid #D4AF37;
    ">
        <h3 style="color: #1F3A5E; font-family: 'Playfair Display', serif; margin-top: 0;">🗂️ Indexed Documents</h3>
    </div>
    """, unsafe_allow_html=True)
    docs = get_documents()
    if docs.get("total", 0) > 0:
        for d in docs["documents"]:
            st.markdown(f"✅ **{d['index_name']}**")
    else:
        st.info("📌 No documents indexed yet. Upload a document to create an index.")

st.markdown("---")

st.markdown("""
<h2 style="text-align: center; color: #1F3A5E;">🚀 HOW TO USE</h2>
""", unsafe_allow_html=True)

steps = [
    ("📤 UPLOAD", "Upload your legal PDF or DOCX file to the system"),
    ("🔍 SEARCH", "Search for specific clauses using semantic search"),
    ("📊 ANALYZE", "Risk analysis, compliance, and summarization"),
    ("🤖 AI INSIGHTS", "Groq AI powered intelligent analysis"),
]

cols = st.columns(4)
for i, (title, desc) in enumerate(steps):
    with cols[i]:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FEFBEA 0%, #FFFEF5 100%);
            color: #1F3A5E;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #1F3A5E;
            border-top: 4px solid #1F3A5E;
        ">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 2rem; font-family: 'Playfair Display', serif; color: #1F3A5E;">
                Step {i+1}
            </h3>
            <h4 style="margin: 0.5rem 0; font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #1F3A5E;">
                {title}
            </h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; font-family: 'Lato', sans-serif; color: #1F3A5E;">
                {desc}
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
<h2 style="text-align: center; color: #1F3A5E;">🛠️ TECHNOLOGY STACK</h2>
""", unsafe_allow_html=True)

tech_stack = [
    ("⚡ FastAPI", "High-performance backend framework"),
    ("🔗 LangChain", "RAG pipeline orchestration"),
    ("🗄️ FAISS", "Vector database for embeddings"),
    ("🧠 MiniLM", "Sentence embeddings"),
    ("🤖 Groq LLM", "AI-powered analysis engine"),
]

cols = st.columns(5)
for i, (tech, desc) in enumerate(tech_stack):
    with cols[i]:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FEFBEA 0%, #FFFEF5 100%);
            color: #1F3A5E;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #1F3A5E;
        ">
            <h4 style="margin: 0 0 0.5rem 0; font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1F3A5E;">
                {tech}
            </h4>
            <p style="margin: 0; font-family: 'Lato', sans-serif; font-size: 0.9rem; color: #1F3A5E;">
                {desc}
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<p style="text-align: center; font-family: 'Merriweather', serif; color: #555; font-size: 0.95rem; margin-top: 2rem;">
    👨-⚖️ <strong>Owner:</strong> Thupakula Pavithra | 📜 <strong>System:</strong> Legal Document Intelligence System v2.0
</p>
""", unsafe_allow_html=True)
