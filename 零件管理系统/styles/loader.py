"""
样式加载器 - 统一加载所有CSS文件
"""

import streamlit as st
import os

def load_styles():
    """加载所有CSS样式文件"""
    styles_dir = os.path.dirname(os.path.abspath(__file__))
    
    css_files = [
        'variables.css',  # CSS变量定义（必须先加载）
        'base.css',       # 基础样式
        'components.css', # 组件样式
        'overrides.css',  # 强制覆盖样式
    ]
    
    combined_css = []
    
    for filename in css_files:
        filepath = os.path.join(styles_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                combined_css.append(f.read())
    
    # 一次性注入所有CSS
    if combined_css:
        st.markdown(f"""
        <style>
        {''.join(combined_css)}
        </style>
        """, unsafe_allow_html=True)
