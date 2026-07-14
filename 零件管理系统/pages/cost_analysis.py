"""成本分析页面 - 成本计算、可视化分析"""

import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime
import sys, os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal, Part, CostItem, Currency, BOM


def calculate_cost(material_cost: float, manufacturing_cost: float, overhead_rate: float = 0.5) -> dict:
    overhead_cost = manufacturing_cost * overhead_rate
    total_cost = material_cost + manufacturing_cost + overhead_cost
    return {
        "material_cost": material_cost,
        "manufacturing_cost": manufacturing_cost,
        "overhead_cost": overhead_cost,
        "total_cost": total_cost,
        "overhead_rate": overhead_rate,
    }


def show():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">💰 零件成本计算与分析</div>
        <div class="page-subtitle">报告数据治理 · 精确计算成本构成 · 可视化分析</div>
    </div>
    <div class="info-box">
        💡 <strong>数据治理知识点：</strong>成本计算结果是典型的"报告数据"，用于支持定价和成本优化决策。
        计算逻辑和数据来源必须清晰、可追溯。总成本 = 材料成本 + 制造成本 + 间接费用（制造成本 × 间接费率）。
    </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_calc, tab_compare = st.tabs(["📊 成本概览", "🧮 成本录入/编辑", "📈 对比分析"])

    with tab_overview:
        _show_cost_overview()

    with tab_calc:
        _show_cost_calc()

    with tab_compare:
        _show_cost_compare()


def _show_cost_overview():
    db: Session = SessionLocal()
    try:
        # 强制刷新查询以获取最新数据
        cost_items = db.query(CostItem).order_by(CostItem.created_at.desc()).all()

        if not cost_items:
            st.info("暂无成本数据，请前往「成本录入/编辑」添加")
            return

        total_value = sum(c.total_cost for c in cost_items)
        avg_cost = total_value / len(cost_items)
        max_cost = max(c.total_cost for c in cost_items)
        min_cost = min(c.total_cost for c in cost_items)

        col1, col2, col3, col4 = st.columns(4)
        for col, icon, val, label, color in [
            (col1, "💴", f"¥{total_value:,.0f}", "总成本价值", "#7c3aed"),
            (col2, "📊", f"¥{avg_cost:,.0f}", "平均成本", "#2563eb"),
            (col3, "⬆️", f"¥{max_cost:,.0f}", "最高成本", "#dc2626"),
            (col4, "⬇️", f"¥{min_cost:,.0f}", "最低成本", "#059669"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card" style="text-align:center;">
                    <div class="metric-icon">{icon}</div>
                    <div style="font-size:1.5rem;font-weight:700;color:{color};">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        import plotly.graph_objects as go

        col_chart, col_table = st.columns([1.5, 1])

        with col_chart:
            st.markdown("""
            <div class="content-card">
                <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">📊 成本构成堆叠图</h4>
            """, unsafe_allow_html=True)

            part_names = []
            mat_costs = []
            mfg_costs = []
            ovh_costs = []

            for c in cost_items:
                part_names.append(f"{c.part.part_code}\n{c.part.name[:6]}")
                mat_costs.append(c.material_cost)
                mfg_costs.append(c.manufacturing_cost)
                ovh_costs.append(c.overhead_cost)

            fig = go.Figure()
            fig.add_trace(go.Bar(name='材料成本', x=part_names, y=mat_costs,
                                marker_color='#10b981', hovertemplate='%{x}<br>材料成本: ¥%{y:,.2f}<extra></extra>'))
            fig.add_trace(go.Bar(name='制造成本', x=part_names, y=mfg_costs,
                                marker_color='#3b82f6', hovertemplate='%{x}<br>制造成本: ¥%{y:,.2f}<extra></extra>'))
            fig.add_trace(go.Bar(name='间接费用', x=part_names, y=ovh_costs,
                                marker_color='#f59e0b', hovertemplate='%{x}<br>间接费用: ¥%{y:,.2f}<extra></extra>'))

            fig.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='#ffffff',
                xaxis=dict(tickfont=dict(color='#64748b', size=10), gridcolor='#f1f5f9'),
                yaxis=dict(tickfont=dict(color='#64748b', size=10), gridcolor='#f1f5f9', tickprefix='¥'),
                legend=dict(font=dict(color='#475569', size=11), bgcolor='rgba(0,0,0,0)',
                           orientation='h', y=-0.15),
                margin=dict(t=10, b=60, l=60, r=10),
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_table:
            st.markdown("""
            <div class="content-card">
                <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">📋 成本明细</h4>
            """, unsafe_allow_html=True)

            import pandas as pd
            data = []
            for c in cost_items:
                currency_symbol = c.currency.symbol if c.currency else "¥"
                data.append({
                    "零件编码": c.part.part_code if c.part else "-",
                    "名称": c.part.name[:8] if c.part else "-",
                    "材料": f"{currency_symbol}{c.material_cost:,.0f}",
                    "制造": f"{currency_symbol}{c.manufacturing_cost:,.0f}",
                    "间接": f"{currency_symbol}{c.overhead_cost:,.0f}",
                    "总成本": f"{currency_symbol}{c.total_cost:,.0f}",
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        total_mat = sum(c.material_cost for c in cost_items)
        total_mfg = sum(c.manufacturing_cost for c in cost_items)
        total_ovh = sum(c.overhead_cost for c in cost_items)

        st.markdown("""
        <div class="content-card">
            <h4 style="color:#1e293b;margin:0 0 20px 0;font-size:0.95rem;font-weight:600;">🥧 全局成本占比分析</h4>
        """, unsafe_allow_html=True)

        col_pie, col_stats = st.columns([1, 1.2])
        with col_pie:
            fig2 = go.Figure(data=[go.Pie(
                labels=['材料成本', '制造成本', '间接费用'],
                values=[total_mat, total_mfg, total_ovh],
                hole=0.5,
                marker=dict(colors=['#10b981', '#3b82f6', '#f59e0b'],
                           line=dict(color='#ffffff', width=2)),
                textinfo='percent',
                textfont=dict(color='#334155', size=12),
                hovertemplate='%{label}: ¥%{value:,.2f} (%{percent})<extra></extra>'
            )])
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(font=dict(color='#475569', size=11), bgcolor='rgba(0,0,0,0)'),
                margin=dict(t=10, b=10, l=10, r=10),
                height=220,
                annotations=[dict(
                    text=f'<b>¥{total_value:,.0f}</b>',
                    font=dict(color='#1e293b', size=12),
                    showarrow=False
                )]
            )
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        with col_stats:
            grand_total = total_mat + total_mfg + total_ovh or 1
            for label, val, color, icon in [
                ("材料成本", total_mat, "#10b981", "🌿"),
                ("制造成本", total_mfg, "#3b82f6", "🏭"),
                ("间接费用", total_ovh, "#f59e0b", "📎"),
            ]:
                pct = val / grand_total * 100
                st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#475569;font-size:0.85rem;">{icon} {label}</span>
                        <span style="color:{color};font-size:0.85rem;font-weight:600;">¥{val:,.0f} ({pct:.1f}%)</span>
                    </div>
                    <div style="background:#f1f5f9;border-radius:99px;height:6px;">
                        <div style="background:{color};border-radius:99px;height:6px;width:{pct}%;transition:width 0.3s;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    finally:
        db.close()


def _show_cost_calc():
    db: Session = SessionLocal()
    try:
        parts = db.query(Part).order_by(Part.part_code).all()
        currencies = db.query(Currency).filter_by(is_active=True).all()

        if not parts:
            st.info("请先添加零件")
            return

        part_opts = {f"{p.part_code} - {p.name}": p.id for p in parts}
        currency_opts = {f"{c.code} - {c.name}": c.id for c in currencies}

        col_form, col_preview = st.columns([1, 1.2])

        with col_form:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">🧮 成本录入 / 编辑</h4>', unsafe_allow_html=True)

            selected_part_key = st.selectbox("选择零件", options=list(part_opts.keys()))
            selected_part_id = part_opts[selected_part_key]
            selected_part = db.query(Part).get(selected_part_id)

            existing_cost = db.query(CostItem).filter_by(part_id=selected_part_id).first()

            with st.form("cost_form"):
                currency_key = st.selectbox("成本货币", options=list(currency_opts.keys()),
                                            index=0 if not existing_cost else
                                            next((i for i, (k, v) in enumerate(currency_opts.items())
                                                  if v == existing_cost.currency_id), 0))

                st.markdown('<p style="color:#64748b;font-size:0.85rem;margin:12px 0 4px 0;">💡 输入材料成本和制造成本，间接费用将自动计算</p>', unsafe_allow_html=True)

                mat_cost = st.number_input(
                    "材料成本 (元)",
                    min_value=0.0, format="%.2f",
                    value=float(existing_cost.material_cost) if existing_cost else 0.0
                )
                mfg_cost = st.number_input(
                    "制造成本 (元)",
                    min_value=0.0, format="%.2f",
                    value=float(existing_cost.manufacturing_cost) if existing_cost else 0.0
                )
                overhead_rate = st.slider(
                    "间接费率 (%)",
                    min_value=0, max_value=100, value=50,
                    help="间接费用 = 制造成本 × 间接费率"
                )

                cost_version = st.text_input(
                    "成本版本",
                    value=existing_cost.cost_version if existing_cost else "v1.0"
                )
                calc_basis = st.text_area(
                    "计算依据（便于追溯）",
                    value=existing_cost.calculation_basis if existing_cost else "",
                    height=80,
                    placeholder="例：材料采购单价×用量，工时×工时单价..."
                )
                notes = st.text_area("备注", height=60,
                                     value=existing_cost.notes if existing_cost else "")

                submitted = st.form_submit_button(
                    "💾 保存成本数据",
                    use_container_width=True
                )

                if submitted:
                    result = calculate_cost(mat_cost, mfg_cost, overhead_rate / 100.0)

                    if existing_cost:
                        existing_cost.currency_id = currency_opts[currency_key]
                        existing_cost.material_cost = result["material_cost"]
                        existing_cost.manufacturing_cost = result["manufacturing_cost"]
                        existing_cost.overhead_cost = result["overhead_cost"]
                        existing_cost.total_cost = result["total_cost"]
                        existing_cost.cost_version = cost_version
                        existing_cost.calculation_basis = calc_basis
                        existing_cost.notes = notes
                        existing_cost.updated_at = datetime.utcnow()
                        action = "更新"
                    else:
                        new_cost = CostItem(
                            part_id=selected_part_id,
                            currency_id=currency_opts[currency_key],
                            material_cost=result["material_cost"],
                            manufacturing_cost=result["manufacturing_cost"],
                            overhead_cost=result["overhead_cost"],
                            total_cost=result["total_cost"],
                            cost_version=cost_version,
                            calculation_basis=calc_basis,
                            notes=notes,
                        )
                        db.add(new_cost)
                        action = "创建"

                    db.commit()
                    st.success(f"✅ 成本数据{action}成功！总成本：¥{result['total_cost']:,.2f}")
                    st.rerun()

        with col_preview:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">📊 成本预览</h4>', unsafe_allow_html=True)
            cost_data = db.query(CostItem).filter_by(part_id=selected_part_id).first()

            if cost_data:
                import plotly.graph_objects as go
                labels = ['材料成本', '制造成本', '间接费用']
                values = [cost_data.material_cost, cost_data.manufacturing_cost, cost_data.overhead_cost]
                colors = ['#10b981', '#3b82f6', '#f59e0b']
                symbol = cost_data.currency.symbol if cost_data.currency else "¥"

                fig = go.Figure(data=[go.Pie(
                    labels=labels, values=values, hole=0.55,
                    marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
                    textinfo='label+percent',
                    textfont=dict(color='#334155', size=12),
                    hovertemplate=f'%{{label}}: {symbol}%{{value:.2f}}<extra></extra>'
                )])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(font=dict(color='#475569', size=11), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=280,
                    annotations=[dict(
                        text=f'<b>{symbol}{cost_data.total_cost:,.0f}</b><br>总成本',
                        font=dict(color='#1e293b', size=13),
                        showarrow=False
                    )]
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                st.markdown(f"""
                <div style="background:#ffffff;border-radius:12px;padding:16px;border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                        <div style="color:#64748b;font-size:0.85rem;">零件编码</div>
                        <div style="color:#2563eb;font-weight:600;font-size:0.85rem;">{selected_part.part_code}</div>
                        <div style="color:#64748b;font-size:0.85rem;">材料成本</div>
                        <div style="color:#059669;font-size:0.85rem;">{symbol}{cost_data.material_cost:,.2f}</div>
                        <div style="color:#64748b;font-size:0.85rem;">制造成本</div>
                        <div style="color:#2563eb;font-size:0.85rem;">{symbol}{cost_data.manufacturing_cost:,.2f}</div>
                        <div style="color:#64748b;font-size:0.85rem;">间接费用</div>
                        <div style="color:#d97706;font-size:0.85rem;">{symbol}{cost_data.overhead_cost:,.2f}</div>
                        <div style="color:#475569;font-size:0.9rem;font-weight:600;">总成本</div>
                        <div style="color:#1e293b;font-size:1rem;font-weight:700;">{symbol}{cost_data.total_cost:,.2f}</div>
                        <div style="color:#64748b;font-size:0.85rem;">成本版本</div>
                        <div style="color:#475569;font-size:0.85rem;">{cost_data.cost_version or '-'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if cost_data.calculation_basis:
                    st.markdown(f"""
                    <div style="margin-top:10px;padding:10px 14px;background:#eff6ff;
                                border-left:3px solid #2563eb;border-radius:0 8px 8px 0;">
                        <span style="color:#2563eb;font-size:0.8rem;font-weight:600;">计算依据：</span>
                        <span style="color:#475569;font-size:0.8rem;">{cost_data.calculation_basis}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align:center;padding:60px 20px;color:#64748b;background:#ffffff;border-radius:12px;border:1px solid #e2e8f0;">
                    <div style="font-size:2.5rem;margin-bottom:12px;">📊</div>
                    <div>该零件尚未录入成本数据</div>
                    <div style="font-size:0.85rem;margin-top:8px;">填写左侧表单后保存</div>
                </div>
                """, unsafe_allow_html=True)

    finally:
        db.close()


def _show_cost_compare():
    db: Session = SessionLocal()
    try:
        # 强制刷新查询以获取最新数据
        cost_items = db.query(CostItem).order_by(CostItem.created_at.desc()).all()

        if len(cost_items) < 2:
            st.info("至少需要2个零件的成本数据才能进行对比分析")
            return

        import plotly.graph_objects as go
        import pandas as pd

        # 图表类型选择
        chart_type = st.radio(
            "选择图表类型",
            ["📊 堆叠柱状图（适合多零件）", "🕸️ 雷达图（最多5个零件）", "📈 成本趋势图", "🥧 成本占比饼图"],
            horizontal=True
        )

        if chart_type == "🕸️ 雷达图（最多5个零件）":
            _show_radar_chart(cost_items)
        elif chart_type == "📊 堆叠柱状图（适合多零件）":
            _show_stacked_bar_chart(cost_items)
        elif chart_type == "📈 成本趋势图":
            _show_trend_chart(cost_items)
        else:
            _show_pie_chart(cost_items)

        # 成本明细对比表（带分页）
        _show_cost_table(cost_items)

    finally:
        db.close()


def _show_radar_chart(cost_items):
    """雷达图 - 适合少量零件对比（最多5个）"""
    import plotly.graph_objects as go

    st.markdown("""
    <div class="content-card">
        <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">🕸️ 零件成本结构对比（雷达图）</h4>
        <p style="color:#64748b;font-size:0.85rem;margin-bottom:12px;">选择最多5个零件进行成本结构对比分析</p>
    """, unsafe_allow_html=True)

    # 准备零件选择列表
    part_options = {}
    for c in cost_items:
        part_label = f"{c.part.part_code} - {c.part.name}" if c.part else f"零件{c.id}"
        part_options[part_label] = c

    # 零件选择器
    selected_labels = st.multiselect(
        "选择要对比的零件（最多5个）",
        options=list(part_options.keys()),
        default=list(part_options.keys())[:min(5, len(part_options))],
        max_selections=5,
        help="请选择2-5个零件进行对比分析"
    )

    if len(selected_labels) < 2:
        st.info("请至少选择2个零件进行对比分析")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # 获取选中的成本项
    selected_cost_items = [part_options[label] for label in selected_labels]

    colors_list = ['#2563eb', '#059669', '#d97706', '#7c3aed', '#dc2626']
    fig_radar = go.Figure()

    for i, c in enumerate(selected_cost_items):
        total = max(c.total_cost, 1)
        part_name = c.part.part_code if c.part else f"零件{c.id}"
        fig_radar.add_trace(go.Scatterpolar(
            r=[c.material_cost / total * 100,
               c.manufacturing_cost / total * 100,
               c.overhead_cost / total * 100,
               c.total_cost / max(max(ci.total_cost for ci in selected_cost_items), 1) * 100],
            theta=['材料成本%', '制造成本%', '间接费用%', '总成本占比'],
            fill='toself',
            name=part_name,
            fillcolor=f"rgba({','.join(str(int(v, 16)) for v in [colors_list[i][1:3], colors_list[i][3:5], colors_list[i][5:7]])}, 0.1)",
            line=dict(color=colors_list[i], width=2),
            marker=dict(color=colors_list[i], size=6),
        ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor='#f8fafc',
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(color='#64748b', size=9), gridcolor='#e2e8f0'),
            angularaxis=dict(tickfont=dict(color='#334155', size=11))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(font=dict(color='#475569', size=11), bgcolor='rgba(0,0,0,0)'),
        margin=dict(t=20, b=20, l=60, r=60),
        height=400,
    )
    st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})

    # 显示选中零件的简要信息
    st.markdown("<p style='color:#64748b;font-size:0.85rem;margin-top:12px;'><strong>已选零件：</strong></p>", unsafe_allow_html=True)
    cols = st.columns(len(selected_cost_items))
    for i, (col, c) in enumerate(zip(cols, selected_cost_items)):
        with col:
            part_name = c.part.name if c.part else f"零件{c.id}"
            st.markdown(f"""
            <div style="text-align:center;padding:8px;background:#f8fafc;border-radius:8px;border-left:4px solid {colors_list[i]};">
                <div style="font-size:0.8rem;color:#475569;font-weight:600;">{c.part.part_code if c.part else '-'}</div>
                <div style="font-size:0.75rem;color:#64748b;">¥{c.total_cost:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _show_stacked_bar_chart(cost_items):
    """堆叠柱状图 - 适合多零件展示"""
    import plotly.graph_objects as go

    st.markdown("""
    <div class="content-card">
        <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">📊 零件成本构成对比（堆叠柱状图）</h4>
        <p style="color:#64748b;font-size:0.85rem;margin-bottom:12px;">横向对比所有零件的材料、制造、间接费用构成</p>
    """, unsafe_allow_html=True)

    # 准备数据
    part_names = []
    mat_costs = []
    mfg_costs = []
    ovh_costs = []

    for c in cost_items:
        part_name = f"{c.part.part_code}" if c.part else f"零件{c.id}"
        part_names.append(part_name)
        mat_costs.append(c.material_cost)
        mfg_costs.append(c.manufacturing_cost)
        ovh_costs.append(c.overhead_cost)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='材料成本',
        x=part_names,
        y=mat_costs,
        marker_color='#10b981',
        hovertemplate='%{x}<br>材料成本: ¥%{y:,.2f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        name='制造成本',
        x=part_names,
        y=mfg_costs,
        marker_color='#3b82f6',
        hovertemplate='%{x}<br>制造成本: ¥%{y:,.2f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        name='间接费用',
        x=part_names,
        y=ovh_costs,
        marker_color='#f59e0b',
        hovertemplate='%{x}<br>间接费用: ¥%{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        xaxis=dict(
            tickfont=dict(color='#64748b', size=10),
            gridcolor='#f1f5f9',
            tickangle=45
        ),
        yaxis=dict(
            tickfont=dict(color='#64748b', size=10),
            gridcolor='#f1f5f9',
            tickprefix='¥'
        ),
        legend=dict(
            font=dict(color='#475569', size=11),
            bgcolor='rgba(0,0,0,0)',
            orientation='h',
            y=-0.2
        ),
        margin=dict(t=20, b=80, l=60, r=20),
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)


def _show_trend_chart(cost_items):
    """成本趋势图 - 按总成本排序展示"""
    import plotly.graph_objects as go

    st.markdown("""
    <div class="content-card">
        <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">📈 零件总成本排序图</h4>
        <p style="color:#64748b;font-size:0.85rem;margin-bottom:12px;">按总成本从高到低排序展示</p>
    """, unsafe_allow_html=True)

    # 按总成本排序
    sorted_items = sorted(cost_items, key=lambda x: x.total_cost, reverse=True)

    part_names = []
    total_costs = []
    colors = []

    color_palette = ['#dc2626', '#ea580c', '#d97706', '#ca8a04', '#65a30d',
                     '#16a34a', '#059669', '#0891b2', '#2563eb', '#4f46e5',
                     '#7c3aed', '#9333ea', '#c026d3', '#db2777', '#e11d48']

    for i, c in enumerate(sorted_items):
        part_name = f"{c.part.part_code}" if c.part else f"零件{c.id}"
        part_names.append(part_name)
        total_costs.append(c.total_cost)
        colors.append(color_palette[i % len(color_palette)])

    fig = go.Figure(data=[go.Bar(
        x=part_names,
        y=total_costs,
        marker_color=colors,
        text=[f'¥{v:,.0f}' for v in total_costs],
        textposition='outside',
        textfont=dict(size=9, color='#475569'),
        hovertemplate='%{x}<br>总成本: ¥%{y:,.2f}<extra></extra>'
    )])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        xaxis=dict(
            tickfont=dict(color='#64748b', size=10),
            gridcolor='#f1f5f9',
            tickangle=45
        ),
        yaxis=dict(
            tickfont=dict(color='#64748b', size=10),
            gridcolor='#f1f5f9',
            tickprefix='¥'
        ),
        margin=dict(t=30, b=80, l=60, r=20),
        height=450,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)


def _show_pie_chart(cost_items):
    """饼图 - 展示各零件成本占总成本的比例"""
    import plotly.graph_objects as go

    st.markdown("""
    <div class="content-card">
        <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">🥧 零件成本占比分布</h4>
        <p style="color:#64748b;font-size:0.85rem;margin-bottom:12px;">展示各零件成本在总成本中的占比（最多显示前10个，其余合并为"其他"）</p>
    """, unsafe_allow_html=True)

    # 按总成本排序，取前10个，其余合并
    sorted_items = sorted(cost_items, key=lambda x: x.total_cost, reverse=True)

    labels = []
    values = []

    for i, c in enumerate(sorted_items[:10]):
        part_name = f"{c.part.part_code}" if c.part else f"零件{c.id}"
        labels.append(part_name)
        values.append(c.total_cost)

    # 如果有超过10个，合并剩余部分
    if len(sorted_items) > 10:
        other_total = sum(c.total_cost for c in sorted_items[10:])
        labels.append("其他")
        values.append(other_total)

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo='label+percent',
        textfont=dict(size=10, color='#334155'),
        hovertemplate='%{label}<br>成本: ¥%{value:,.2f}<br>占比: %{percent}<extra></extra>',
        marker=dict(
            colors=['#2563eb', '#059669', '#d97706', '#7c3aed', '#dc2626',
                    '#0891b2', '#ea580c', '#65a30d', '#db2777', '#4f46e5', '#94a3b8']
        )
    )])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            font=dict(color='#475569', size=10),
            bgcolor='rgba(0,0,0,0)',
            orientation='v'
        ),
        margin=dict(t=20, b=20, l=20, r=20),
        height=450,
        annotations=[dict(
            text=f'<b>¥{sum(values):,.0f}</b><br>总成本',
            font=dict(color='#1e293b', size=12),
            showarrow=False
        )]
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)


def _show_cost_table(cost_items):
    """成本明细对比表（带分页）"""
    import pandas as pd

    st.markdown("""
    <div class="content-card">
        <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">📋 成本明细对比表</h4>
    """, unsafe_allow_html=True)

    # 分页设置
    items_per_page = 10
    total_items = len(cost_items)
    total_pages = math.ceil(total_items / items_per_page)

    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"页码 (共 {total_items} 条记录)",
                options=list(range(1, total_pages + 1)),
                format_func=lambda x: f"第 {x} 页 / 共 {total_pages} 页"
            )
    else:
        page = 1

    # 计算当前页的数据范围
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_page_items = cost_items[start_idx:end_idx]

    data = []
    for c in current_page_items:
        total = c.total_cost or 1
        symbol = c.currency.symbol if c.currency else "¥"
        data.append({
            "零件编码": c.part.part_code if c.part else "-",
            "零件名称": c.part.name if c.part else "-",
            "材料成本": f"{symbol}{c.material_cost:,.2f}",
            "材料占比": f"{c.material_cost/total*100:.1f}%",
            "制造成本": f"{symbol}{c.manufacturing_cost:,.2f}",
            "制造占比": f"{c.manufacturing_cost/total*100:.1f}%",
            "间接费用": f"{symbol}{c.overhead_cost:,.2f}",
            "间接占比": f"{c.overhead_cost/total*100:.1f}%",
            "总成本": f"{symbol}{c.total_cost:,.2f}",
            "成本版本": c.cost_version or "-",
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if total_pages > 1:
        st.markdown(f"<p style='color:#64748b;font-size:0.8rem;text-align:center;'>显示第 {start_idx+1} - {end_idx} 条，共 {total_items} 条</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
