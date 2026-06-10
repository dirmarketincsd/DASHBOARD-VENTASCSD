import base64
from pathlib import Path

import streamlit as st


def get_logo_base64():
    try:
        logo_path = Path(__file__).parent / "LOGO_DORADO.png"
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None


def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 500 !important; }
section[data-testid="stSidebar"] h3 { color: #c9a84c !important; font-size: 1.1rem !important; }
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d0d0d, #1a1500);
    border-radius: 14px; padding: 16px 20px;
    border: 1px solid #c9a84c;
    box-shadow: 0 4px 20px rgba(201,168,76,0.15);
}
div[data-testid="stMetric"] label { color: #c9a84c !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1.2px; }
div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.9rem !important; font-weight: 700 !important; }
div[data-testid="stMetricDelta"] { color: #f0d080 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #0a0a0a; padding: 8px; border-radius: 12px; border: 1px solid #2a2000; }
.stTabs [data-baseweb="tab"] { background: #111100; border-radius: 8px; color: #c9a84c; padding: 8px 20px; font-weight: 600; border: 1px solid #2a2000; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #c9a84c, #f0d080) !important; color: #000000 !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0a00, #111100) !important; border-right: 1px solid #c9a84c !important; }
hr { border-color: #c9a84c !important; opacity: 0.3; }
.resumen-fijo {
    background: linear-gradient(135deg, #0a0a00, #111100);
    border: 1.5px solid #c9a84c;
    border-radius: 18px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 6px 30px rgba(201,168,76,0.12);
}
.resumen-fijo-titulo {
    color: #c9a84c;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin-bottom: 2px;
    font-weight: 700;
}
.resumen-fijo-sub {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 14px;
    opacity: 0.85;
}
.grupo-label-usa {
    color: #7c6af7;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
.grupo-label-esp {
    color: #00d4aa;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)
