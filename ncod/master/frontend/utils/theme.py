"""
主题工具函数
"""

from typing import Any, Dict

import streamlit as st

from ..config import settings


def apply_theme() -> Dict[str, Any]:
    """应用主题设置"""
    theme = settings.THEME

    # 应用主题配置
    st.set_page_config(
        page_title="NCOD设备监控",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 应用自定义CSS
    st.markdown(
        f"""
        <style>
        :root {{
            --primary-color: {theme['primaryColor']};
            --background-color: {theme['backgroundColor']};
            --secondary-background-color: {theme['secondaryBackgroundColor']};
            --text-color: {theme['textColor']};
            --font: {theme['font']};
        }}
        
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: var(--font);
        }}
        
        .stButton>button {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .stProgress .st-bo {{
            background-color: var(--primary-color);
        }}
        
        .stSelectbox {{
            background-color: var(--secondary-background-color);
        }}
        
        .stTextInput>div>div>input {{
            background-color: var(--secondary-background-color);
            color: var(--text-color);
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )

    return theme
