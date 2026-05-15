import streamlit as st

def apply_judicial_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Lato:wght@400;600&family=Merriweather:ital@0;1&display=swap');
    
    * {
        font-family: 'Lato', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #F5F5F5 0%, #FEFBEA 100%);
    }
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #1F3A5E;
        letter-spacing: 1px;
    }
    
    .stButton > button {
        background-color: #FEFBEA !important;
        color: #1F3A5E !important;
        border: 2px solid #1F3A5E !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #D4AF37 !important;
        border-color: #1F3A5E !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4) !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #FEFBEA !important;
        color: #1F3A5E !important;
        border: 2px solid #1F3A5E !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > div > input {
        background-color: #FEFBEA !important;
        color: #1F3A5E !important;
    }
    
    .stSlider > div > div {
        background-color: #D4AF37 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #FEFBEA !important;
        color: #1F3A5E !important;
        border-bottom: 3px solid #1F3A5E !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #D4AF37 !important;
        border-bottom: 3px solid #1F3A5E !important;
    }
    
    .stExpander {
        background-color: #FEFBEA !important;
        border: 2px solid #1F3A5E !important;
    }
    
    .stMetric {
        background-color: #FEFBEA !important;
        border: 2px solid #1F3A5E !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    .stInfo, .stSuccess, .stWarning, .stError {
        background-color: #FEFBEA !important;
        color: #1F3A5E !important;
        border: 2px solid #1F3A5E !important;
        border-radius: 8px !important;
    }
    
    .sidebar .stButton > button {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

def success_banner(title, message):
    st.success(f"**{title}**\n{message}")

def error_banner(title, message):
    st.error(f"**{title}**\n{message}")

def info_banner(title, message):
    st.info(f"**{title}**\n{message}")

def info_card(title, content, icon=""):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #FEFBEA 0%, #FFFEF5 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #D4AF37;
        box-shadow: 0 4px 12px rgba(31, 58, 94, 0.1);
        margin: 1rem 0;
    ">
        <h4 style="color: #1F3A5E; margin: 0 0 0.5rem 0; font-family: 'Playfair Display', serif;">
            {icon} {title}
        </h4>
        <p style="color: #1F3A5E; margin: 0; font-size: 0.95rem;">
            {content}
        </p>
    </div>
    """, unsafe_allow_html=True)

def professional_celebration():
    st.balloons()
    st.success("✨ Document processed successfully!")
