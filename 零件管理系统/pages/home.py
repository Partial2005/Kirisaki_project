"""首页 - 系统概览仪表盘"""

import streamlit as st
from sqlalchemy.orm import Session
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal, Part, BOM, CostItem, Currency, MaterialType


def show():
    # 页面标题
    st.markdown("""
    <div class="page-header">
        <div class="page-title">系统概览</div>
        <div class="page-subtitle">零件成本管理系统 · 数据资产全景视图</div>
    </div>
    """, unsafe_allow_html=True)

    db: Session = SessionLocal()
    try:
        # ===== 统计指标 =====
        total_parts = db.query(Part).count()
        active_parts = db.query(Part).filter(Part.status == "active").count()
        total_bom = db.query(BOM).count()
        total_cost_items = db.query(CostItem).count()

        from sqlalchemy import func
        total_cost_sum = db.query(func.sum(CostItem.total_cost)).scalar() or 0

        col1, col2, col3, col4, col5 = st.columns(5)

        metrics = [
            (col1, "🔩", str(total_parts), "零件总数"),
            (col2, "✅", str(active_parts), "活跃零件"),
            (col3, "📋", str(total_bom), "BOM记录"),
            (col4, "💰", str(total_cost_items), "成本记录"),
            (col5, "💴", f"¥{total_cost_sum:,.0f}", "总成本估值"),
        ]

        for col, icon, val, label in metrics:
            with col:
                st.markdown(f"""
                <div class="metric-card" style="text-align:center;">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ===== 两列布局 =====
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("""
            <div class="content-card">
                <h3 style="color:#0f172a;margin:0 0 16px 0;font-size:1rem;font-weight:700;">📊 零件状态分布</h3>
            """, unsafe_allow_html=True)

            import plotly.graph_objects as go

            status_counts = {}
            status_labels = {"active": "活跃", "inactive": "停用", "prototype": "原型", "obsolete": "淘汰"}
            status_colors = {"active": "#10b981", "inactive": "#94a3b8", "prototype": "#f59e0b", "obsolete": "#ef4444"}

            from sqlalchemy import func as sqlfunc
            results = db.query(Part.status, sqlfunc.count(Part.id)).group_by(Part.status).all()
            for status, count in results:
                status_counts[status] = count

            if status_counts:
                labels = [status_labels.get(k, k) for k in status_counts.keys()]
                values = list(status_counts.values())
                colors = [status_colors.get(k, "#94a3b8") for k in status_counts.keys()]

                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(colors=colors, line=dict(color='#ffffff', width=3)),
                    textinfo='label+percent',
                    textfont=dict(color='#1e293b', size=14, family='Microsoft YaHei'),
                    hovertemplate='%{label}: %{value}件<extra></extra>',
                    pull=[0.03] * len(labels),
                )])

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(
                        font=dict(color='#1e293b', size=12, family='Microsoft YaHei'),
                        bgcolor='rgba(0,0,0,0)',
                        orientation='h',
                        x=0.5, y=-0.05,
                        xanchor='center',
                        itemsizing='constant',
                    ),
                    margin=dict(t=10, b=40, l=10, r=10),
                    height=300,
                    annotations=[dict(
                        text=f'<b style="font-size:24px;color:#0f172a;">{total_parts}</b><br><span style="font-size:13px;color:#475569;">零件总数</span>',
                        x=0.5, y=0.5,
                        font=dict(size=14, family='Microsoft YaHei'),
                        showarrow=False
                    )]
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

            # 最近零件列表
            st.markdown("""
            <div class="content-card">
                <h3 style="color:#0f172a;margin:0 0 16px 0;font-size:1rem;font-weight:700;">🔩 最近零件</h3>
            """, unsafe_allow_html=True)

            recent_parts = db.query(Part).order_by(Part.created_at.desc()).limit(5).all()
            if recent_parts:
                for p in recent_parts:
                    status_map = {"active": ("活跃", "status-active"), "inactive": ("停用", "status-inactive"),
                                  "prototype": ("原型", "status-prototype"), "obsolete": ("淘汰", "status-obsolete")}
                    s_label, s_class = status_map.get(p.status, ("未知", "status-inactive"))
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 8px;border-bottom:1px solid #e2e8f0;">
                        <div style="min-width:0;">
                            <span style="color:#1d4ed8;font-weight:700;font-size:0.95rem;">{p.part_code}</span>
                            <span style="color:#1e293b;margin-left:8px;font-size:0.92rem;font-weight:600;">{p.name}</span>
                        </div>
                        <span class="status-badge {s_class}" style="flex-shrink:0;">{s_label}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#94a3b8;text-align:center;padding:20px 0;font-size:0.9rem;">暂无零件数据</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            # 物料类型分布
            st.markdown("""
            <div class="content-card">
                <h3 style="color:#0f172a;margin:0 0 16px 0;font-size:1rem;font-weight:700;">📦 物料类型分布</h3>
            """, unsafe_allow_html=True)

            type_results = (
                db.query(MaterialType.name, sqlfunc.count(Part.id))
                .outerjoin(Part, Part.material_type_id == MaterialType.id)
                .group_by(MaterialType.name)
                .all()
            )

            if type_results:
                type_labels = [r[0] for r in type_results]
                type_values = [r[1] for r in type_results]
                bar_colors = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']

                fig2 = go.Figure(go.Bar(
                    y=type_labels,
                    x=type_values,
                    orientation='h',
                    marker=dict(
                        color=bar_colors[:len(type_labels)],
                        line=dict(color='#ffffff', width=1),
                        cornerradius=4,
                    ),
                    text=type_values,
                    textposition='outside',
                    textfont=dict(color='#1e293b', size=13, family='Microsoft YaHei'),
                    hovertemplate='%{y}: %{x}件<extra></extra>'
                ))
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#94a3b8', tickfont=dict(size=10)),
                    yaxis=dict(color='#1e293b', tickfont=dict(size=13, family='Microsoft YaHei')),
                    margin=dict(t=10, b=40, l=10, r=30),
                    height=300,
                )
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

            # 系统模块介绍
            st.markdown("""
            <div class="content-card">
                <h3 style="color:#0f172a;margin:0 0 16px 0;font-size:1rem;font-weight:700;">🧭 系统模块</h3>
            """, unsafe_allow_html=True)

            modules = [
                ("⚙️", "基础配置管理", "货币、单位、区域、物料类型"),
                ("🔩", "零件主数据", "零件全生命周期管理"),
                ("📋", "BOM管理", "物料清单层级结构"),
                ("💰", "成本分析", "可视化成本构成分析"),
                ("🗺️", "数据地图", "元数据字典与数据架构"),
                ("🤖", "AI 助手", "智能问答与数据洞察"),
            ]
            for icon, name, desc in modules:
                st.markdown(f"""
                <div style="display:flex;align-items:flex-start;padding:12px 8px;border-bottom:1px solid #e2e8f0;">
                    <span style="font-size:1.25rem;margin-right:12px;margin-top:1px;">{icon}</span>
                    <div>
                        <div style="color:#0f172a;font-size:0.92rem;font-weight:700;">{name}</div>
                        <div style="color:#334155;font-size:0.85rem;margin-top:3px;font-weight:600;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ===== 数据治理原则说明 =====
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:28px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <h3 style="color:#0f172a;margin:0 0 20px 0;font-size:1.05rem;font-weight:700;">📐 数据治理设计原则</h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
                <div style="text-align:center;padding:20px;background:#eff6ff;border-radius:14px;border:1px solid #bfdbfe;">
                    <div style="font-size:1.5rem;margin-bottom:8px;">👔</div>
                    <div style="color:#1e40af;font-weight:700;font-size:0.88rem;margin-bottom:4px;">业务负责制</div>
                    <div style="color:#334155;font-size:0.8rem;font-weight:500;">每类数据明确责任主体，代码层面清晰体现</div>
                </div>
                <div style="text-align:center;padding:20px;background:#ecfdf5;border-radius:14px;border:1px solid #a7f3d0;">
                    <div style="font-size:1.5rem;margin-bottom:8px;">📖</div>
                    <div style="color:#047857;font-weight:700;font-size:0.88rem;margin-bottom:4px;">统一语言</div>
                    <div style="color:#334155;font-size:0.8rem;font-weight:500;">配置数据通过外键引用，禁止硬编码</div>
                </div>
                <div style="text-align:center;padding:20px;background:#fffbeb;border-radius:14px;border:1px solid #fde68a;">
                    <div style="font-size:1.5rem;margin-bottom:8px;">🎯</div>
                    <div style="color:#b45309;font-weight:700;font-size:0.88rem;margin-bottom:4px;">数据同源</div>
                    <div style="color:#334155;font-size:0.8rem;font-weight:500;">关键数据唯一权威来源，避免冗余</div>
                </div>
                <div style="text-align:center;padding:20px;background:#f5f3ff;border-radius:14px;border:1px solid #c4b5fd;">
                    <div style="font-size:1.5rem;margin-bottom:8px;">🗂️</div>
                    <div style="color:#6d28d9;font-weight:700;font-size:0.88rem;margin-bottom:4px;">元数据驱动</div>
                    <div style="color:#334155;font-size:0.8rem;font-weight:500;">数据地图让数据"找得到、读得懂"</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    finally:
        db.close()
