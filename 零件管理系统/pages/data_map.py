"""数据地图页面 - 元数据字典与数据架构"""

import streamlit as st
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def show():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🗺️ 数据地图 · 元数据字典</div>
        <div class="page-subtitle">元数据驱动管理 · 让数据"找得到、读得懂"</div>
    </div>
    <div class="info-box">
        💡 <strong>数据治理知识点：</strong>这是系统的"元数据字典"，对标华为"数据地图"的核心价值。
        每张数据表都有完整的表描述、字段说明、数据类型、主外键关系，帮助用户理解数据的含义、来源和结构。
    </div>
    """, unsafe_allow_html=True)

    meta_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata_dict.json")
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        st.error(f"元数据字典加载失败: {e}")
        return

    tab_arch, tab_tables, tab_lineage = st.tabs(["🏗️ 数据架构", "📖 元数据字典", "🔗 数据血缘"])

    with tab_arch:
        _show_architecture(metadata)

    with tab_tables:
        _show_metadata_dict(metadata)

    with tab_lineage:
        _show_data_lineage(metadata)


def _show_architecture(metadata):

    st.markdown("""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <h3 style="color:#1e293b;font-size:1rem;font-weight:600;margin:0 0 20px 0;">🏗️ 系统数据架构（信息架构图）</h3>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:8px;">
        <span style="background:#eff6ff;border:1px solid #bfdbfe;color:#2563eb;
                     font-size:0.78rem;font-weight:600;padding:4px 16px;border-radius:20px;letter-spacing:0.05em;">
            LAYER 1 · 基础配置数据（参考数据）
        </span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:4px;">
    """, unsafe_allow_html=True)

    layer1_tables = [
        ("💴", "currencies", "货币配置表", "货币代码、名称、符号"),
        ("📏", "units", "单位配置表", "重量/数量/长度单位"),
        ("🌍", "regions", "区域配置表", "生产区域、国家"),
        ("📦", "material_types", "物料类型表", "原材料/半成品/成品"),
    ]
    for icon, tname, tdisplay, tdesc in layer1_tables:
        st.markdown(f"""
        <div class="data-map-node">
            <div style="font-size:1.5rem;margin-bottom:8px;">{icon}</div>
            <div style="color:#2563eb;font-weight:600;font-size:0.85rem;margin-bottom:4px;">{tdisplay}</div>
            <div style="color:#64748b;font-size:0.75rem;">{tname}</div>
            <div style="color:#475569;font-size:0.73rem;margin-top:4px;">{tdesc}</div>
        </div>
        """.replace("{tname}", tname), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;color:#2563eb;font-size:1.2rem;margin:8px 0;">↓ 被引用（外键关联）↓</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:8px;">
        <span style="background:#ecfdf5;border:1px solid #a7f3d0;color:#059669;
                     font-size:0.78rem;font-weight:600;padding:4px 16px;border-radius:20px;letter-spacing:0.05em;">
            LAYER 2 · 主数据（核心业务对象）
        </span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:12px;margin:0 25%;margin-bottom:4px;">
        <div class="data-map-node" style="border-color:#a7f3d0;">
            <div style="font-size:1.5rem;margin-bottom:8px;">🔩</div>
            <div style="color:#059669;font-weight:600;font-size:0.9rem;margin-bottom:4px;">零件主数据表 (parts)</div>
            <div style="color:#64748b;font-size:0.75rem;">零件编码、名称、描述、版本、状态、物料类型、重量单位、来源区域</div>
            <div style="margin-top:8px;font-size:0.73rem;color:#059669;">■ 核心业务对象 ■ 唯一权威数据源</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;color:#059669;font-size:1.2rem;margin:8px 0;">↓ 被事务数据引用 ↓</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:8px;">
        <span style="background:#fffbeb;border:1px solid #fde68a;color:#d97706;
                     font-size:0.78rem;font-weight:600;padding:4px 16px;border-radius:20px;letter-spacing:0.05em;">
            LAYER 3 · 事务数据 & 报告数据
        </span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:0 10%;">
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="data-map-node" style="border-color:#fde68a;">
            <div style="font-size:1.5rem;margin-bottom:8px;">📋</div>
            <div style="color:#d97706;font-weight:600;font-size:0.85rem;margin-bottom:4px;">BOM物料清单 (boms)</div>
            <div style="color:#64748b;font-size:0.75rem;">父零件、子零件、用量、层级、生效期</div>
            <div style="margin-top:8px;font-size:0.73rem;color:#d97706;">■ 事务数据 ■ 零件层级关系</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="data-map-node" style="border-color:#c4b5fd;">
            <div style="font-size:1.5rem;margin-bottom:8px;">💰</div>
            <div style="color:#7c3aed;font-weight:600;font-size:0.85rem;margin-bottom:4px;">成本项表 (cost_items)</div>
            <div style="color:#64748b;font-size:0.75rem;">材料成本、制造成本、间接费用、总成本、版本</div>
            <div style="margin-top:8px;font-size:0.73rem;color:#7c3aed;">■ 报告数据 ■ 决策支持</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:20px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;
                padding:16px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;">
        <div style="text-align:center;">
            <div style="color:#2563eb;font-size:1.2rem;font-weight:700;">{len(metadata.get('tables', []))}</div>
            <div style="color:#64748b;font-size:0.78rem;">数据表总数</div>
        </div>
        <div style="text-align:center;">
            <div style="color:#059669;font-size:1.2rem;font-weight:700;">{sum(len(t.get('fields',[])) for t in metadata.get('tables',[]))}</div>
            <div style="color:#64748b;font-size:0.78rem;">字段总数</div>
        </div>
        <div style="text-align:center;">
            <div style="color:#d97706;font-size:1.2rem;font-weight:700;">{len(metadata.get('relationships', []))}</div>
            <div style="color:#64748b;font-size:0.78rem;">关联关系数</div>
        </div>
        <div style="text-align:center;">
            <div style="color:#7c3aed;font-size:1.2rem;font-weight:700;">4</div>
            <div style="color:#64748b;font-size:0.78rem;">数据分层</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _show_metadata_dict(metadata):
    tables = metadata.get("tables", [])

    category_colors = {
        "基础配置数据": ("#2563eb", "#eff6ff"),
        "主数据": ("#059669", "#ecfdf5"),
        "事务数据": ("#d97706", "#fffbeb"),
        "报告数据": ("#7c3aed", "#f5f3ff"),
    }

    table_opts = {f"{t['display_name']} ({t['table_name']})": i for i, t in enumerate(tables)}
    selected_table_key = st.selectbox("选择要查看的数据表", options=list(table_opts.keys()))
    selected_idx = table_opts[selected_table_key]
    table = tables[selected_idx]

    cat = table.get("data_category", "")
    color, bg = category_colors.get(cat, ("#475569", "#f8fafc"))

    st.markdown(f"""
    <div style="background:{bg};border:1px solid {color};border-radius:16px;padding:20px 24px;margin:16px 0;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;">
            <div>
                <h3 style="color:#1e293b;margin:0;font-size:1.1rem;">{table['display_name']}</h3>
                <code style="color:{color};font-size:0.9rem;background:#ffffff;padding:2px 8px;border-radius:4px;margin-top:6px;display:inline-block;border:1px solid #e2e8f0;">{table['table_name']}</code>
            </div>
            <span style="background:{bg};border:1px solid {color};color:{color};font-size:0.78rem;padding:4px 12px;border-radius:20px;font-weight:600;">{cat}</span>
        </div>
        <p style="color:#475569;margin:12px 0 0 0;font-size:0.88rem;line-height:1.7;">{table['description']}</p>
        <div style="display:flex;gap:24px;margin-top:12px;">
            <span style="color:#64748b;font-size:0.82rem;">🏢 业务负责人：<span style="color:#1e293b;">{table.get('business_owner', '-')}</span></span>
            <span style="color:#64748b;font-size:0.82rem;">🔄 更新频率：<span style="color:#1e293b;">{table.get('update_frequency', '-')}</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<h4 style="color:#1e293b;margin:16px 0 12px 0;font-size:0.95rem;font-weight:600;">📋 字段定义</h4>', unsafe_allow_html=True)

    fields = table.get("fields", [])

    cols = st.columns([2, 2, 2, 1, 1, 1, 4])
    headers = ["字段名称", "显示名称", "数据类型", "主键", "外键", "可空", "字段说明"]
    for col, header in zip(cols, headers):
        with col:
            st.markdown(f'<span style="color:#2563eb;font-size:0.78rem;font-weight:600;">{header}</span>', unsafe_allow_html=True)

    st.markdown('<hr style="margin:4px 0 8px 0;">', unsafe_allow_html=True)

    for field in fields:
        cols = st.columns([2, 2, 2, 1, 1, 1, 4])
        is_pk = field.get("is_pk", False)
        is_fk = field.get("is_fk", False)
        nullable = field.get("nullable", True)

        row_data = [
            (f'`{field["name"]}`', "#2563eb" if is_pk else "#475569"),
            (field.get("display_name", ""), "#1e293b"),
            (f'`{field.get("data_type", "")}`', "#059669"),
            ("🔑 PK" if is_pk else "—", "#d97706" if is_pk else "#94a3b8"),
            ("🔗 FK" if is_fk else "—", "#7c3aed" if is_fk else "#94a3b8"),
            ("✅" if nullable else "❌", "#059669" if nullable else "#dc2626"),
            (field.get("description", ""), "#64748b"),
        ]
        for col, (val, color) in zip(cols, row_data):
            with col:
                st.markdown(f'<span style="color:{color};font-size:0.82rem;">{val}</span>', unsafe_allow_html=True)


def _show_data_lineage(metadata):
    relationships = metadata.get("relationships", [])

    st.markdown("""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <h4 style="color:#1e293b;margin:0 0 20px 0;font-size:0.95rem;font-weight:600;">🔗 数据关联关系（血缘图）</h4>
    """, unsafe_allow_html=True)

    import plotly.graph_objects as go

    node_positions = {
        "currencies": (0.1, 0.1),
        "units": (0.1, 0.4),
        "regions": (0.1, 0.7),
        "material_types": (0.1, 0.95),
        "parts": (0.5, 0.5),
        "boms": (0.9, 0.3),
        "cost_items": (0.9, 0.7),
    }

    node_colors = {
        "currencies": "#2563eb",
        "units": "#2563eb",
        "regions": "#2563eb",
        "material_types": "#2563eb",
        "parts": "#059669",
        "boms": "#d97706",
        "cost_items": "#7c3aed",
    }

    node_labels = {
        "currencies": "货币配置<br>currencies",
        "units": "单位配置<br>units",
        "regions": "区域配置<br>regions",
        "material_types": "物料类型<br>material_types",
        "parts": "零件主数据<br>parts",
        "boms": "BOM物料清单<br>boms",
        "cost_items": "成本项<br>cost_items",
    }

    fig = go.Figure()

    for rel in relationships:
        from_table = rel["from_table"]
        to_table = rel["to_table"]
        if from_table in node_positions and to_table in node_positions:
            x0, y0 = node_positions[from_table]
            x1, y1 = node_positions[to_table]
            fig.add_trace(go.Scatter(
                x=[x0, x1, None], y=[y0, y1, None],
                mode='lines',
                line=dict(width=1.5, color='#94a3b8', dash='dot'),
                hoverinfo='none',
                showlegend=False,
            ))

    for table, (x, y) in node_positions.items():
        color = node_colors.get(table, "#64748b")
        label = node_labels.get(table, table)
        size = 40 if table == "parts" else 25

        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=size, color=f"rgba({','.join(str(int(v, 16)) for v in [color[1:3], color[3:5], color[5:7]])}, 0.85)",
                       line=dict(width=2, color=color)),
            text=[label],
            textposition='middle right' if x < 0.5 else ('middle left' if x > 0.5 else 'middle center'),
            textfont=dict(color='#1e293b', size=10),
            hovertemplate=f'<b>{table}</b><extra></extra>',
            showlegend=False,
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#f8fafc',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.1, 1.5]),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.1, 1.1]),
        margin=dict(t=10, b=10, l=10, r=200),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<h4 style="color:#1e293b;margin:16px 0 12px 0;font-size:0.95rem;font-weight:600;">📋 关联关系说明</h4>', unsafe_allow_html=True)

    for rel in relationships:
        rel_type = "多对一" if rel["relationship"] == "many-to-one" else rel["relationship"]
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;margin-bottom:6px;
                    background:#ffffff;border-radius:10px;border:1px solid #e2e8f0;">
            <code style="color:#2563eb;font-size:0.82rem;min-width:120px;">{rel['from_table']}</code>
            <span style="color:#64748b;font-size:0.82rem;">.{rel['from_field']}</span>
            <span style="color:#2563eb;font-size:1rem;">→</span>
            <code style="color:#059669;font-size:0.82rem;min-width:120px;">{rel['to_table']}</code>
            <span style="color:#64748b;font-size:0.82rem;">.{rel['to_field']}</span>
            <span style="background:#eff6ff;color:#2563eb;font-size:0.75rem;padding:2px 8px;border-radius:10px;margin-left:8px;">{rel_type}</span>
            <span style="color:#475569;font-size:0.82rem;margin-left:8px;">{rel['description']}</span>
        </div>
        """, unsafe_allow_html=True)
