"""BOM（物料清单）管理页面"""

import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal, Part, BOM, Unit


def show():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">📋 BOM 物料清单管理</div>
        <div class="page-subtitle">事务数据治理 · 零件层级结构管理</div>
    </div>
    <div class="info-box">
        💡 <strong>数据治理知识点：</strong>BOM是典型的"事务数据"，通过调用Part主数据建立零件间的层级关系。
        体现了"管理好事务数据对主数据的调用"的治理思想。每个BOM记录都必须引用已存在的父零件和子零件。
    </div>
    """, unsafe_allow_html=True)

    db: Session = SessionLocal()
    try:
        preselected_part_id = st.session_state.get("bom_part_id", None)

        tab_view, tab_add = st.tabs(["📋 BOM 查看", "➕ 新增 BOM"])

        with tab_view:
            _show_bom_view(db, preselected_part_id)

        with tab_add:
            _show_bom_add(db)

    finally:
        db.close()
        if "bom_part_id" in st.session_state:
            del st.session_state["bom_part_id"]


def _show_bom_view(db, preselected_part_id=None):
    parts = db.query(Part).order_by(Part.part_code).all()

    if not parts:
        st.info("暂无零件数据")
        return

    part_opts = {f"{p.part_code} - {p.name}": p.id for p in parts}
    part_keys = list(part_opts.keys())

    default_idx = 0
    if preselected_part_id:
        for i, (k, v) in enumerate(part_opts.items()):
            if v == preselected_part_id:
                default_idx = i
                break

    selected_key = st.selectbox(
        "选择父零件查看其BOM",
        options=part_keys,
        index=default_idx,
        label_visibility="collapsed"
    )

    if not selected_key:
        return

    parent_id = part_opts[selected_key]
    parent_part = db.query(Part).get(parent_id)
    bom_items = db.query(BOM).filter_by(parent_part_id=parent_id).all()

    st.markdown(f"""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:20px 24px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,0.04);position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#2563eb,#3b82f6);"></div>
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
            <span style="font-size:1.5rem;">🔩</span>
            <div>
                <span style="color:#2563eb;font-size:1.1rem;font-weight:700;">{parent_part.part_code}</span>
                <span style="color:#1e293b;font-size:1rem;margin-left:10px;">{parent_part.name}</span>
            </div>
        </div>
        <div style="display:flex;gap:24px;">
            <span style="color:#64748b;font-size:0.85rem;">BOM子件数量：<span style="color:#2563eb;font-weight:600;">{len(bom_items)}</span></span>
            <span style="color:#64748b;font-size:0.85rem;">物料类型：<span style="color:#475569;">{parent_part.material_type.name if parent_part.material_type else '-'}</span></span>
            <span style="color:#64748b;font-size:0.85rem;">供应商：<span style="color:#475569;">{parent_part.supplier or '-'}</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not bom_items:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#64748b;">
            <div style="font-size:2rem;margin-bottom:8px;">📭</div>
            <div>该零件暂无BOM子件，请在"新增BOM"页签添加</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # 统一的列宽比例（表头和数据行用同一个 list，st.columns 天然对齐）
    COL_WIDTHS = [5, 11, 19, 8, 7, 11, 10, 29]

    # 外层卡片容器
    st.markdown("""<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;
        overflow:hidden;margin-top:8px;padding:0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">""",
        unsafe_allow_html=True)

    # ── 表头（st.columns，和数据行同一套渲染引擎）──
    hdr = st.columns(COL_WIDTHS, gap="small")
    headers = ["层级", "子件编码", "子件名称", "用量", "单位", "生效日期", "状态", "操作"]
    for col, name in zip(hdr, headers):
        with col:
            st.markdown(f'<span style="color:#2563eb;font-size:0.78rem;font-weight:600;">{name}</span>',
                        unsafe_allow_html=True)
    st.markdown('<hr style="margin:4px 0;border-color:#e2e8f0;">', unsafe_allow_html=True)

    # ── 数据行 ──
    for item in bom_items:
        child = item.child_part
        unit_code = item.unit.code if item.unit else ""
        effective = item.effective_date.strftime("%Y-%m-%d") if item.effective_date else "-"
        is_expired = item.expiry_date and item.expiry_date < datetime.utcnow()
        status_color = "#dc2626" if is_expired else "#059669"
        status_text = "已过期" if is_expired else "有效"

        row = st.columns(COL_WIDTHS, gap="small")

        with row[0]:
            st.markdown(f'<span style="color:#d97706;font-size:0.85rem;font-weight:600;">L{item.bom_level}</span>',
                        unsafe_allow_html=True)
        with row[1]:
            st.markdown(f'<span style="color:#2563eb;font-size:0.85rem;">{child.part_code}</span>',
                        unsafe_allow_html=True)
        with row[2]:
            st.markdown(f'<span style="color:#1e293b;font-size:0.85rem;">{child.name}</span>',
                        unsafe_allow_html=True)
        with row[3]:
            st.markdown(f'<span style="color:#475569;font-size:0.85rem;">{item.quantity}</span>',
                        unsafe_allow_html=True)
        with row[4]:
            st.markdown(f'<span style="color:#475569;font-size:0.85rem;">{unit_code}</span>',
                        unsafe_allow_html=True)
        with row[5]:
            st.markdown(f'<span style="color:#64748b;font-size:0.85rem;">{effective}</span>',
                        unsafe_allow_html=True)
        with row[6]:
            st.markdown(f'<span style="color:{status_color};font-size:0.85rem;font-weight:600;">{status_text}</span>',
                        unsafe_allow_html=True)
        with row[7]:
            c_note, c_btn = st.columns([5, 2], gap="small")
            with c_note:
                st.markdown(f'<span style="color:#64748b;font-size:0.82rem;">{item.notes or ""}</span>',
                            unsafe_allow_html=True)
            with c_btn:
                if st.button("🗑️", key=f"del_bom_{item.id}", help="删除此BOM记录"):
                    db.delete(item)
                    db.commit()
                    st.success("BOM记录已删除")
                    st.rerun()

        st.markdown('<hr style="margin:2px 0;border-color:#f1f5f9;">', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _show_bom_tree(parent_part, bom_items, db)


def _show_bom_tree(parent_part, bom_items, db):
    import plotly.graph_objects as go

    st.markdown("""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:20px 24px;margin-top:8px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <h4 style="color:#1e293b;margin:0 0 16px 0;font-size:0.95rem;font-weight:600;">🌲 BOM层级树状图</h4>
    """, unsafe_allow_html=True)

    if not bom_items:
        st.info("暂无子件数据")
    else:
        labels = [f"{parent_part.part_code}\n{parent_part.name}"]
        parents = [""]
        values = [100]
        hover_texts = [f"父零件: {parent_part.part_code}"]

        for item in bom_items:
            child = item.child_part
            labels.append(f"{child.part_code}\n{child.name}\n×{item.quantity}")
            parents.append(f"{parent_part.part_code}\n{parent_part.name}")
            values.append(max(10, int(item.quantity * 20)))
            hover_texts.append(f"子件: {child.part_code}<br>用量: {item.quantity}<br>名称: {child.name}")

        fig = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            hovertext=hover_texts,
            hoverinfo="text",
            textfont=dict(size=11, color="#1e293b"),
            marker=dict(
                colors=["#2563eb"] + ["#059669", "#d97706", "#7c3aed", "#b45309", "#0d9488"][:len(bom_items)],
                line=dict(width=2, color="#ffffff")
            ),
            pathbar=dict(visible=True)
        ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("</div>", unsafe_allow_html=True)


def _show_bom_add(db):
    parts = db.query(Part).order_by(Part.part_code).all()
    units = db.query(Unit).filter_by(is_active=True).all()

    if not parts:
        st.info("请先在零件主数据页面添加零件")
        return

    part_opts = {f"{p.part_code} - {p.name}": p.id for p in parts}
    unit_opts = {f"{u.code} - {u.name}": u.id for u in units}

    st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">新增BOM记录</h4>', unsafe_allow_html=True)

    with st.form("add_bom_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            parent_choice = st.selectbox("父零件 *", options=list(part_opts.keys()))
            quantity = st.number_input("用量 *", min_value=0.001, value=1.0, format="%.3f")
        with col2:
            child_choice = st.selectbox("子零件 *", options=list(part_opts.keys()))
            unit_choice = st.selectbox("用量单位", options=list(unit_opts.keys()))

        bom_level = st.number_input("BOM层级", min_value=1, max_value=99, value=1)
        notes = st.text_area("备注", height=60)

        submitted = st.form_submit_button("✅ 添加BOM记录", use_container_width=True)

        if submitted:
            parent_id = part_opts[parent_choice]
            child_id = part_opts[child_choice]

            if parent_id == child_id:
                st.error("父零件和子零件不能是同一个！")
            else:
                existing = db.query(BOM).filter_by(
                    parent_part_id=parent_id, child_part_id=child_id
                ).first()

                if existing:
                    st.warning(f"BOM记录已存在！当前用量：{existing.quantity}，如需修改请先删除再重新添加。")
                else:
                    bom = BOM(
                        parent_part_id=parent_id,
                        child_part_id=child_id,
                        quantity=quantity,
                        unit_id=unit_opts[unit_choice],
                        bom_level=bom_level,
                        notes=notes,
                    )
                    db.add(bom)
                    db.commit()
                    st.success(f"✅ BOM记录添加成功！")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<h4 style="color:#1e293b;margin-bottom:12px;">所有BOM记录汇总</h4>', unsafe_allow_html=True)

    all_boms = db.query(BOM).all()
    if all_boms:
        import pandas as pd
        data = []
        for b in all_boms:
            data.append({
                "ID": b.id,
                "父零件编码": b.parent_part.part_code if b.parent_part else "-",
                "父零件名称": b.parent_part.name if b.parent_part else "-",
                "子零件编码": b.child_part.part_code if b.child_part else "-",
                "子零件名称": b.child_part.name if b.child_part else "-",
                "用量": b.quantity,
                "单位": b.unit.code if b.unit else "",
                "BOM层级": b.bom_level,
                "备注": b.notes or "",
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True,
                    column_config={"ID": st.column_config.NumberColumn(width="small")})
    else:
        st.info("暂无BOM数据")
