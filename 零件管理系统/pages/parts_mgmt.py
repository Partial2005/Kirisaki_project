"""零件主数据管理页面"""

import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal, Part, MaterialType, Unit, Region, BOM, CostItem


STATUS_OPTIONS = {
    "active": "✅ 活跃",
    "inactive": "⏸️ 停用",
    "prototype": "🔬 原型",
    "obsolete": "🚫 淘汰"
}

STATUS_COLORS = {
    "active": "status-active",
    "inactive": "status-inactive",
    "prototype": "status-prototype",
    "obsolete": "status-obsolete"
}

STATUS_ZH = {"active": "活跃", "inactive": "停用", "prototype": "原型", "obsolete": "淘汰"}


def show():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🔩 零件主数据管理</div>
        <div class="page-subtitle">核心业务对象 · 零件全生命周期信息管理</div>
    </div>
    <div class="info-box">
        💡 <strong>数据治理知识点：</strong>Part（零件）是系统的核心"业务对象"，是所有BOM和成本数据的单一数据源。
        其设计围绕业务需求展开，支持状态、版本等生命周期管理。所有关联数据（BOM、成本）均以零件编码为基础。
    </div>
    """, unsafe_allow_html=True)

    if "selected_part_id" in st.session_state and st.session_state.selected_part_id:
        _show_part_detail(st.session_state.selected_part_id)
        return

    col_search, col_filter, col_new = st.columns([2, 1, 1])

    with col_search:
        search_text = st.text_input("🔍 搜索零件", placeholder="输入零件编码或名称...", label_visibility="collapsed")

    with col_filter:
        filter_status = st.selectbox("状态筛选", ["全部"] + list(STATUS_ZH.values()), label_visibility="collapsed")

    with col_new:
        if st.button("➕ 新增零件", use_container_width=True):
            st.session_state.show_add_part = True

    if st.session_state.get("show_add_part", False):
        _add_part_form()

    _show_parts_list(search_text, filter_status)


def _add_part_form():
    db: Session = SessionLocal()
    try:
        st.markdown("""
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <h3 style="color:#1e293b;margin:0 0 20px 0;">➕ 新增零件</h3>
        """, unsafe_allow_html=True)

        mts = db.query(MaterialType).filter_by(is_active=True).all()
        units = db.query(Unit).filter_by(is_active=True).all()
        regions = db.query(Region).filter_by(is_active=True).all()

        with st.form("add_part_form"):
            col1, col2 = st.columns(2)
            with col1:
                part_code = st.text_input("零件编码 *", placeholder="如: P-001")
                name = st.text_input("零件名称 *", placeholder="如: 主传动轴")
                version = st.text_input("版本号", value="1.0")
                status = st.selectbox("状态", options=list(STATUS_OPTIONS.keys()),
                                     format_func=lambda x: STATUS_OPTIONS[x])
            with col2:
                mt_opts = {f"{m.code} - {m.name}": m.id for m in mts}
                mt_choice = st.selectbox("物料类型 *", options=list(mt_opts.keys()))
                unit_opts = {f"{u.code} - {u.name}": u.id for u in units}
                unit_choice = st.selectbox("重量单位", options=list(unit_opts.keys()))
                region_opts = {f"{r.code} - {r.name}": r.id for r in regions}
                region_choice = st.selectbox("来源区域", options=list(region_opts.keys()))
                weight = st.number_input("重量", min_value=0.0, format="%.3f")

            description = st.text_area("零件描述", height=80)

            col_a, col_b = st.columns(2)
            with col_a:
                drawing_number = st.text_input("图纸编号", placeholder="如: DWG-2023-001")
            with col_b:
                supplier = st.text_input("供应商", placeholder="如: 华东精密机械")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("✅ 确认创建", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("❌ 取消", use_container_width=True)

            if submitted:
                if not part_code or not name:
                    st.error("请填写必填项（编码、名称、物料类型）")
                else:
                    exists = db.query(Part).filter_by(part_code=part_code.strip()).first()
                    if exists:
                        st.error(f"零件编码 {part_code} 已存在！")
                    else:
                        p = Part(
                            part_code=part_code.strip(),
                            name=name.strip(),
                            description=description,
                            version=version,
                            status=status,
                            material_type_id=mt_opts[mt_choice],
                            weight_unit_id=unit_opts[unit_choice],
                            origin_region_id=region_opts[region_choice],
                            weight=weight,
                            drawing_number=drawing_number,
                            supplier=supplier,
                        )
                        db.add(p)
                        db.commit()
                        st.success(f"✅ 零件 {part_code} 创建成功！")
                        st.session_state.show_add_part = False
                        st.rerun()

            if cancelled:
                st.session_state.show_add_part = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    finally:
        db.close()


def _show_parts_list(search_text, filter_status):
    db: Session = SessionLocal()
    try:
        query = db.query(Part)

        if search_text:
            query = query.filter(
                (Part.part_code.ilike(f"%{search_text}%")) |
                (Part.name.ilike(f"%{search_text}%"))
            )

        status_reverse = {v: k for k, v in STATUS_ZH.items()}
        if filter_status != "全部":
            query = query.filter(Part.status == status_reverse.get(filter_status, filter_status))

        parts = query.order_by(Part.created_at.desc()).all()

        total = query.count()
        st.markdown(f'<p style="color:#475569;font-size:0.85rem;margin:12px 0;">共找到 <span style="color:#2563eb;font-weight:600;">{total}</span> 条零件记录</p>', unsafe_allow_html=True)

        # 表格头 - 使用 st.columns 与数据行保持一致
        header_cols = st.columns([90, 80, 160, 120, 90, 90, 80, 110, 110])
        headers = ["零件编码", "版本", "名称", "物料类型", "重量", "来源区域", "状态", "操作", "BOM"]
        for col, header in zip(header_cols, headers):
            with col:
                st.markdown(f'<span style="color:#2563eb;font-size:0.8rem;font-weight:600;">{header}</span>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px;background:#e2e8f0;margin:4px 0;"></div>', unsafe_allow_html=True)

        for p in parts:
            s_class = STATUS_COLORS.get(p.status, "status-inactive")
            s_label = STATUS_ZH.get(p.status, p.status)
            mt_name = p.material_type.name if p.material_type else "-"
            unit_code = p.weight_unit.code if p.weight_unit else ""
            weight_str = f"{p.weight} {unit_code}" if p.weight else "-"
            region_name = p.origin_region.name if p.origin_region else "-"

            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([90, 80, 160, 120, 90, 90, 80, 110, 110])

            with col1:
                st.markdown(f'<span style="color:#2563eb;font-weight:600;font-size:0.88rem;">{p.part_code}</span>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<span style="color:#64748b;font-size:0.85rem;">v{p.version}</span>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<span style="color:#1e293b;font-size:0.88rem;">{p.name}</span>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<span style="color:#475569;font-size:0.85rem;">{mt_name}</span>', unsafe_allow_html=True)
            with col5:
                st.markdown(f'<span style="color:#475569;font-size:0.85rem;">{weight_str}</span>', unsafe_allow_html=True)
            with col6:
                st.markdown(f'<span style="color:#475569;font-size:0.85rem;">{region_name}</span>', unsafe_allow_html=True)
            with col7:
                st.markdown(f'<span class="status-badge {s_class}">{s_label}</span>', unsafe_allow_html=True)
            with col8:
                if st.button("✏️ 编辑", key=f"edit_{p.id}", use_container_width=True):
                    st.session_state.selected_part_id = p.id
                    st.rerun()
            with col9:
                if st.button("📋 BOM", key=f"bom_{p.id}", use_container_width=True):
                    st.session_state.bom_preview_part_id = p.id
                    st.rerun()

        # BOM预览弹窗
        if st.session_state.get("bom_preview_part_id"):
            _show_bom_preview_popup(st.session_state.bom_preview_part_id)

        st.markdown('<div style="height:1px;background:#e2e8f0;margin:4px 0 20px 0;"></div>', unsafe_allow_html=True)

    finally:
        db.close()


def _show_part_detail(part_id):
    db: Session = SessionLocal()
    try:
        part = db.query(Part).get(part_id)
        if not part:
            st.error("零件不存在")
            st.session_state.selected_part_id = None
            return

        col_back, col_del, col_empty = st.columns([1, 1, 2])
        with col_back:
            if st.button("← 返回零件列表", use_container_width=True):
                st.session_state.selected_part_id = None
                st.rerun()
        with col_del:
            if st.button("🗑️ 删除零件", use_container_width=True, type="secondary"):
                st.session_state.show_delete_confirm = True

        if st.session_state.get("show_delete_confirm", False):
            st.warning(f"⚠️ 确定要删除零件 {part.part_code} {part.name} 吗？删除后不可恢复，关联的BOM和成本数据也将一并删除。")
            col_confirm, col_cancel_del = st.columns(2)
            with col_confirm:
                if st.button("✅ 确认删除", use_container_width=True, type="primary"):
                    db.delete(part)
                    db.commit()
                    st.session_state.selected_part_id = None
                    st.session_state.show_delete_confirm = False
                    st.success(f"✅ 零件 {part.part_code} 已删除！")
                    st.rerun()
            with col_cancel_del:
                if st.button("❌ 取消", use_container_width=True):
                    st.session_state.show_delete_confirm = False
                    st.rerun()

        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:20px;padding:28px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,0.04);position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#2563eb,#3b82f6,#60a5fa);"></div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                <div>
                    <span style="color:#2563eb;font-size:1.4rem;font-weight:700;">{part.part_code}</span>
                    <span style="color:#1e293b;font-size:1.2rem;margin-left:12px;font-weight:600;">{part.name}</span>
                </div>
                <span class="status-badge {STATUS_COLORS.get(part.status,'status-inactive')}">{STATUS_ZH.get(part.status, part.status)}</span>
            </div>
            <p style="color:#64748b;margin:8px 0 0 0;font-size:0.9rem;">{part.description or '无描述'}</p>
        </div>
        """, unsafe_allow_html=True)

        tab_edit, tab_cost, tab_bom_detail = st.tabs(["✏️ 编辑信息", "💰 成本信息", "📋 BOM子件"])

        with tab_edit:
            _edit_part_form(part, db)

        with tab_cost:
            _show_part_cost(part, db)

        with tab_bom_detail:
            _show_part_bom(part, db)

    finally:
        db.close()


def _edit_part_form(part, db):
    mts = db.query(MaterialType).filter_by(is_active=True).all()
    units = db.query(Unit).filter_by(is_active=True).all()
    regions = db.query(Region).filter_by(is_active=True).all()

    with st.form(f"edit_part_{part.id}"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("零件名称 *", value=part.name)
            new_version = st.text_input("版本号", value=part.version or "")
            new_status = st.selectbox("状态", options=list(STATUS_OPTIONS.keys()),
                                     format_func=lambda x: STATUS_OPTIONS[x],
                                     index=list(STATUS_OPTIONS.keys()).index(part.status) if part.status in STATUS_OPTIONS else 0)
        with col2:
            mt_opts = {f"{m.code} - {m.name}": m.id for m in mts}
            mt_keys = list(mt_opts.keys())
            mt_default = next((k for k, v in mt_opts.items() if v == part.material_type_id), mt_keys[0] if mt_keys else None)
            mt_choice = st.selectbox("物料类型", options=mt_keys,
                                    index=mt_keys.index(mt_default) if mt_default in mt_keys else 0)

            unit_opts = {f"{u.code} - {u.name}": u.id for u in units}
            unit_keys = list(unit_opts.keys())
            unit_default = next((k for k, v in unit_opts.items() if v == part.weight_unit_id), unit_keys[0] if unit_keys else None)
            unit_choice = st.selectbox("重量单位", options=unit_keys,
                                      index=unit_keys.index(unit_default) if unit_default in unit_keys else 0)

            region_opts = {f"{r.code} - {r.name}": r.id for r in regions}
            region_keys = list(region_opts.keys())
            region_default = next((k for k, v in region_opts.items() if v == part.origin_region_id), region_keys[0] if region_keys else None)
            region_choice = st.selectbox("来源区域", options=region_keys,
                                        index=region_keys.index(region_default) if region_default in region_keys else 0)
            new_weight = st.number_input("重量", value=float(part.weight or 0), min_value=0.0, format="%.3f")

        new_desc = st.text_area("零件描述", value=part.description or "", height=80)
        col_a, col_b = st.columns(2)
        with col_a:
            new_drawing = st.text_input("图纸编号", value=part.drawing_number or "")
        with col_b:
            new_supplier = st.text_input("供应商", value=part.supplier or "")

        if st.form_submit_button("💾 保存修改", use_container_width=True):
            part.name = new_name
            part.version = new_version
            part.status = new_status
            part.material_type_id = mt_opts[mt_choice]
            part.weight_unit_id = unit_opts[unit_choice]
            part.origin_region_id = region_opts[region_choice]
            part.weight = new_weight
            part.description = new_desc
            part.drawing_number = new_drawing
            part.supplier = new_supplier
            part.updated_at = datetime.utcnow()
            db.commit()
            st.success("✅ 零件信息已保存！")
            st.rerun()


def _show_part_cost(part, db):
    cost_item = db.query(CostItem).filter_by(part_id=part.id).first()

    if cost_item:
        currency = cost_item.currency
        symbol = currency.symbol if currency else "¥"

        col1, col2, col3, col4 = st.columns(4)
        for col, label, val, color in [
            (col1, "材料成本", cost_item.material_cost, "#059669"),
            (col2, "制造成本", cost_item.manufacturing_cost, "#2563eb"),
            (col3, "间接费用", cost_item.overhead_cost, "#d97706"),
            (col4, "总成本", cost_item.total_cost, "#7c3aed"),
        ]:
            with col:
                st.markdown(f"""
                <div style="text-align:center;padding:16px;background:#ffffff;border-radius:12px;border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="color:{color};font-size:1.4rem;font-weight:700;">{symbol}{val:,.2f}</div>
                    <div style="color:#64748b;font-size:0.8rem;margin-top:4px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#eff6ff;border-radius:10px;padding:12px 16px;border-left:3px solid #2563eb;">
            <span style="color:#2563eb;font-size:0.85rem;font-weight:600;">计算依据（可追溯）：</span>
            <span style="color:#475569;font-size:0.85rem;">{cost_item.calculation_basis or '暂无'}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        import plotly.graph_objects as go
        labels = ['材料成本', '制造成本', '间接费用']
        values = [cost_item.material_cost, cost_item.manufacturing_cost, cost_item.overhead_cost]
        colors = ['#10b981', '#3b82f6', '#f59e0b']

        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.5,
            marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
            textinfo='label+percent+value',
            texttemplate='%{label}<br>%{value:.1f}<br>(%{percent})',
            textfont=dict(color='#334155', size=12),
            hovertemplate='%{label}: %{value:.2f}<extra></extra>'
        )])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(text=f"成本构成分析 - {part.part_code}", font=dict(color='#1e293b', size=14), x=0.5),
            showlegend=True,
            legend=dict(font=dict(color='#475569'), bgcolor='rgba(0,0,0,0)'),
            margin=dict(t=50, b=20, l=20, r=20),
            height=350,
            annotations=[dict(
                text=f'<b>{symbol}{cost_item.total_cost:,.0f}</b><br>总成本',
                font=dict(color='#1e293b', size=13),
                showarrow=False
            )]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    else:
        st.info("该零件暂无成本数据，可在成本分析页面添加")


def _show_part_bom(part, db):
    bom_items = db.query(BOM).filter_by(parent_part_id=part.id).all()

    if bom_items:
        st.markdown(f'<p style="color:#475569;margin-bottom:12px;">该零件包含 <span style="color:#2563eb;font-weight:600;">{len(bom_items)}</span> 个子件</p>', unsafe_allow_html=True)

        total_sub_cost = 0
        for item in bom_items:
            child_cost = db.query(CostItem).filter_by(part_id=item.child_part_id).first()
            if child_cost:
                total_sub_cost += child_cost.total_cost * item.quantity

        col_no, col_code, col_name, col_qty, col_unit, col_cost, col_subtotal = st.columns([40, 90, 160, 70, 60, 90, 100])

        headers = ["序号", "子件编码", "子件名称", "用量", "单位", "单件成本", "小计"]
        cols = [col_no, col_code, col_name, col_qty, col_unit, col_cost, col_subtotal]
        for col, header in zip(cols, headers):
            with col:
                st.markdown(f'<span style="color:#2563eb;font-size:0.8rem;font-weight:600;">{header}</span>', unsafe_allow_html=True)

        for idx, item in enumerate(bom_items, 1):
            child = item.child_part
            child_cost = db.query(CostItem).filter_by(part_id=child.id).first()
            unit_code = item.unit.code if item.unit else ""
            unit_cost_str = f"¥{child_cost.total_cost:,.2f}" if child_cost else "-"
            subtotal = (child_cost.total_cost * item.quantity) if child_cost else 0
            subtotal_str = f"¥{subtotal:,.2f}" if child_cost else "-"

            cols_row = st.columns([40, 90, 160, 70, 60, 90, 100])
            row_data = [str(idx), child.part_code, child.name,
                       str(item.quantity), unit_code, unit_cost_str, subtotal_str]
            row_colors = ["#475569", "#2563eb", "#1e293b", "#475569", "#475569", "#059669", "#d97706"]

            for col, val, color in zip(cols_row, row_data, row_colors):
                with col:
                    st.markdown(f'<span style="color:{color};font-size:0.85rem;">{val}</span>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:16px;padding:12px 16px;background:#f5f3ff;border-radius:10px;border:1px solid #c4b5fd;">
            <span style="color:#7c3aed;font-weight:600;">子件成本合计：</span>
            <span style="color:#1e293b;font-size:1.1rem;font-weight:700;">¥{total_sub_cost:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("该零件暂无BOM子件记录，可在BOM管理页面添加")


def _show_bom_preview_popup(part_id):
    """显示BOM预览弹窗"""
    db: Session = SessionLocal()
    try:
        part = db.query(Part).get(part_id)
        if not part:
            st.session_state.bom_preview_part_id = None
            return

        bom_items = db.query(BOM).filter_by(parent_part_id=part_id).all()

        # 弹窗遮罩层样式
        st.markdown("""
        <style>
        .bom-popup-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 9998;
        }
        </style>
        """, unsafe_allow_html=True)

        # 使用expander模拟弹窗效果
        with st.container():
            st.markdown("""
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin:16px 0;box-shadow:0 20px 60px rgba(0,0,0,0.15);">
            """, unsafe_allow_html=True)

            # 标题栏
            col_title, col_close = st.columns([5, 1])
            with col_title:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:1.5rem;">📋</span>
                    <div>
                        <div style="font-size:1.1rem;font-weight:700;color:#1e293b;">{part.part_code} {part.name}</div>
                        <div style="font-size:0.85rem;color:#64748b;">BOM快速预览 · 共 {len(bom_items)} 个子件</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_close:
                if st.button("✕ 关闭", key="close_bom_preview", use_container_width=True, type="secondary"):
                    st.session_state.bom_preview_part_id = None
                    st.rerun()

            st.markdown("<hr style='margin:16px 0;border:none;border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

            if bom_items:
                # BOM表格
                col_no, col_code, col_name, col_qty, col_unit, col_cost, col_subtotal = st.columns([40, 100, 180, 70, 70, 100, 100])
                headers = ["序号", "子件编码", "子件名称", "用量", "单位", "单件成本", "小计"]
                cols = [col_no, col_code, col_name, col_qty, col_unit, col_cost, col_subtotal]
                for col, header in zip(cols, headers):
                    with col:
                        st.markdown(f'<span style="color:#2563eb;font-size:0.8rem;font-weight:600;">{header}</span>', unsafe_allow_html=True)

                total_sub_cost = 0
                for idx, item in enumerate(bom_items, 1):
                    child = item.child_part
                    child_cost = db.query(CostItem).filter_by(part_id=child.id).first()
                    unit_code = item.unit.code if item.unit else ""
                    unit_cost = child_cost.total_cost if child_cost else 0
                    subtotal = unit_cost * item.quantity
                    total_sub_cost += subtotal

                    cols_row = st.columns([40, 100, 180, 70, 70, 100, 100])
                    row_data = [
                        (str(idx), "#475569"),
                        (child.part_code, "#2563eb"),
                        (child.name, "#1e293b"),
                        (str(item.quantity), "#475569"),
                        (unit_code, "#475569"),
                        (f"¥{unit_cost:,.2f}" if child_cost else "-", "#059669"),
                        (f"¥{subtotal:,.2f}" if child_cost else "-", "#d97706")
                    ]

                    for col, (val, color) in zip(cols_row, row_data):
                        with col:
                            st.markdown(f'<span style="color:{color};font-size:0.85rem;">{val}</span>', unsafe_allow_html=True)

                # 合计
                st.markdown(f"""
                <div style="margin-top:16px;padding:12px 16px;background:#f5f3ff;border-radius:10px;border:1px solid #c4b5fd;display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#7c3aed;font-weight:600;">子件成本合计</span>
                    <span style="color:#1e293b;font-size:1.2rem;font-weight:700;">¥{total_sub_cost:,.2f}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("该零件暂无BOM子件记录")

            # 底部按钮
            col_goto, col_space, col_close2 = st.columns([1, 2, 1])
            with col_goto:
                if st.button("🔗 前往BOM管理", key="goto_bom_mgmt", use_container_width=True):
                    st.session_state.bom_part_id = part_id
                    st.session_state.bom_preview_part_id = None
                    st.session_state.page = "📋 BOM管理"
                    st.rerun()
            with col_close2:
                if st.button("关闭", key="close_bom_preview2", use_container_width=True, type="secondary"):
                    st.session_state.bom_preview_part_id = None
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    finally:
        db.close()
