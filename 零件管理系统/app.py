"""
零件成本管理系统 - 主应用入口
技术栈：Python + Streamlit + SQLAlchemy + Plotly
"""

import streamlit as st
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, seed_data
from styles import load_styles

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="零件成本管理系统",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 加载CSS样式 ====================
load_styles()

# ==================== 初始化数据库 ====================
@st.cache_resource
def initialize():
    init_db()
    seed_data()
    return True

initialize()


# ==================== 侧边栏导航 ====================
NAV_OPTIONS = [
    "🏠 系统首页",
    "⚙️ 基础配置管理",
    "🔩 零件主数据",
    "📋 BOM管理",
    "💰 成本分析",
    "🗺️ 数据地图",
    "🤖 AI 助手",
]

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div style="font-size: 2.2rem;">⚙️</div>
        <div class="sidebar-logo-title">零件成本管理系统</div>
        <div class="sidebar-logo-sub">Parts Cost Management v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#94a3b8; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.1em; margin:0 0 10px 12px;">系统导航</p>', unsafe_allow_html=True)

    page = st.radio(
        "导航",
        options=NAV_OPTIONS,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
    <div style="padding: 12px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
        <p style="color:#1e40af; font-size:0.78rem; font-weight:700; margin:0 0 6px 0;">数据治理原则</p>
        <p style="color:#475569; font-size:0.73rem; font-weight:500; margin:0; line-height:1.8;">
        ✅ 业务负责制<br>
        ✅ 统一语言<br>
        ✅ 数据同源<br>
        ✅ 元数据驱动
        </p>
    </div>
    """, unsafe_allow_html=True)


# ==================== 页面路由 ====================
if page == "🏠 系统首页":
    from pages.home import show
    show()
elif page == "⚙️ 基础配置管理":
    from pages.config_mgmt import show
    show()
elif page == "🔩 零件主数据":
    from pages.parts_mgmt import show
    show()
elif page == "📋 BOM管理":
    from pages.bom_mgmt import show
    show()
elif page == "💰 成本分析":
    from pages.cost_analysis import show
    show()
elif page == "🗺️ 数据地图":
    from pages.data_map import show
    show()
elif page == "🤖 AI 助手":
    from pages.ai_assistant import show
    show()
