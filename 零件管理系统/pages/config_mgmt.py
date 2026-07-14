"""基础配置数据管理页面 - 货币/单位/区域/物料类型"""

import streamlit as st
from sqlalchemy.orm import Session
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal, Currency, Unit, Region, MaterialType, Part, BOM


def show():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">基础配置管理</div>
        <div class="page-subtitle">管理系统的统一语言 · 货币 / 单位 / 区域 / 物料类型</div>
    </div>
    <div class="info-box">
        💡 <strong>数据治理知识点：</strong>这些配置数据是系统的"统一语言"。任何引用它们的地方都必须通过外键关联，禁止硬编码，体现"基础数据变更管理"和"统一标准管控"思想。
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["💴 货币管理", "📏 单位管理", "🌍 区域管理", "📦 物料类型"])

    with tab1:
        _manage_currency()

    with tab2:
        _manage_unit()

    with tab3:
        _manage_region()

    with tab4:
        _manage_material_type()


def _manage_currency():
    db: Session = SessionLocal()
    try:
        col_list, col_form = st.columns([1.5, 1])

        with col_list:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">货币列表</h4>', unsafe_allow_html=True)
            currencies = db.query(Currency).all()
            if currencies:
                import pandas as pd
                data = []
                for c in currencies:
                    data.append({
                        "ID": c.id, "代码": c.code, "名称": c.name,
                        "符号": c.symbol, "描述": c.description or "",
                        "启用": "✅" if c.is_active else "❌"
                    })
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True,
                             column_config={"ID": st.column_config.NumberColumn(width="small")})
            else:
                st.info("暂无货币数据")

        with col_form:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">新增货币</h4>', unsafe_allow_html=True)
            with st.form("add_currency_form", clear_on_submit=True):
                code = st.text_input("货币代码 *", placeholder="如: CNY")
                name = st.text_input("货币名称 *", placeholder="如: 人民币")
                symbol = st.text_input("货币符号 *", placeholder="如: ¥")
                desc = st.text_area("备注说明", height=80)
                is_active = st.checkbox("启用", value=True)
                submitted = st.form_submit_button("➕ 新增货币", use_container_width=True)

                if submitted:
                    if not code or not name or not symbol:
                        st.error("请填写必填项（代码、名称、符号）")
                    else:
                        exists = db.query(Currency).filter_by(code=code.strip().upper()).first()
                        if exists:
                            st.error(f"货币代码 {code} 已存在")
                        else:
                            c = Currency(code=code.strip().upper(), name=name.strip(),
                                        symbol=symbol.strip(), description=desc, is_active=is_active)
                            db.add(c)
                            db.commit()
                            st.success(f"✅ 货币 {code} 创建成功！")
                            st.rerun()

            st.markdown('<h4 style="color:#1e293b;margin:20px 0 12px 0;">删除货币</h4>', unsafe_allow_html=True)
            currencies_reload = db.query(Currency).all()
            if currencies_reload:
                del_options = {f"{c.code} - {c.name}": c.id for c in currencies_reload}
                del_choice = st.selectbox("选择要删除的货币", options=list(del_options.keys()))
                if st.button("🗑️ 删除", key="del_currency", use_container_width=True):
                    cid = del_options[del_choice]
                    c = db.query(Currency).get(cid)
                    if c and len(c.cost_items) > 0:
                        st.error("该货币已被成本记录引用，不可删除！")
                    elif c:
                        db.delete(c)
                        db.commit()
                        st.success("✅ 删除成功！")
                        st.rerun()
    finally:
        db.close()


def _manage_unit():
    db: Session = SessionLocal()
    try:
        col_list, col_form = st.columns([1.5, 1])

        with col_list:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">单位列表</h4>', unsafe_allow_html=True)
            units = db.query(Unit).all()
            if units:
                import pandas as pd
                data = [{"ID": u.id, "代码": u.code, "名称": u.name,
                         "类别": u.category or "", "描述": u.description or "",
                         "启用": "✅" if u.is_active else "❌"} for u in units]
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无单位数据")

        with col_form:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">新增单位</h4>', unsafe_allow_html=True)
            with st.form("add_unit_form", clear_on_submit=True):
                code = st.text_input("单位代码 *", placeholder="如: kg")
                name = st.text_input("单位名称 *", placeholder="如: 千克")
                category = st.selectbox("单位类别", ["数量", "重量", "长度", "体积", "其他"])
                desc = st.text_area("备注说明", height=60)
                is_active = st.checkbox("启用", value=True)
                submitted = st.form_submit_button("➕ 新增单位", use_container_width=True)

                if submitted:
                    if not code or not name:
                        st.error("请填写必填项")
                    else:
                        exists = db.query(Unit).filter_by(code=code.strip()).first()
                        if exists:
                            st.error(f"单位代码 {code} 已存在")
                        else:
                            u = Unit(code=code.strip(), name=name.strip(), category=category,
                                    description=desc, is_active=is_active)
                            db.add(u)
                            db.commit()
                            st.success(f"✅ 单位 {code} 创建成功！")
                            st.rerun()

            st.markdown('<h4 style="color:#1e293b;margin:20px 0 12px 0;">删除单位</h4>', unsafe_allow_html=True)
            units_reload = db.query(Unit).all()
            if units_reload:
                del_opts = {f"{u.code} - {u.name}": u.id for u in units_reload}
                del_choice = st.selectbox("选择要删除的单位", options=list(del_opts.keys()), key="del_unit_sel")
                if st.button("🗑️ 删除", key="del_unit", use_container_width=True):
                    uid = del_opts[del_choice]
                    u = db.query(Unit).get(uid)
                    if u:
                        # 检查是否被零件引用（重量单位）
                        if len(u.parts) > 0:
                            st.error("该单位已被零件引用（重量单位），不可删除！")
                        else:
                            db.delete(u)
                            db.commit()
                            st.success("✅ 删除成功！")
                            st.rerun()
    finally:
        db.close()


def _manage_region():
    db: Session = SessionLocal()
    try:
        col_list, col_form = st.columns([1.5, 1])

        with col_list:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">区域列表</h4>', unsafe_allow_html=True)
            regions = db.query(Region).all()
            if regions:
                import pandas as pd
                data = [{"ID": r.id, "代码": r.code, "名称": r.name,
                         "国家": r.country or "", "描述": r.description or "",
                         "启用": "✅" if r.is_active else "❌"} for r in regions]
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无区域数据")

        with col_form:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">新增区域</h4>', unsafe_allow_html=True)
            with st.form("add_region_form", clear_on_submit=True):
                code = st.text_input("区域代码 *", placeholder="如: CN-EAST")
                name = st.text_input("区域名称 *", placeholder="如: 华东区")
                country = st.text_input("所属国家", placeholder="如: 中国")
                desc = st.text_area("备注说明", height=60)
                is_active = st.checkbox("启用", value=True)
                submitted = st.form_submit_button("➕ 新增区域", use_container_width=True)

                if submitted:
                    if not code or not name:
                        st.error("请填写必填项")
                    else:
                        exists = db.query(Region).filter_by(code=code.strip()).first()
                        if exists:
                            st.error(f"区域代码 {code} 已存在")
                        else:
                            r = Region(code=code.strip(), name=name.strip(), country=country,
                                      description=desc, is_active=is_active)
                            db.add(r)
                            db.commit()
                            st.success(f"✅ 区域 {code} 创建成功！")
                            st.rerun()

            st.markdown('<h4 style="color:#1e293b;margin:20px 0 12px 0;">删除区域</h4>', unsafe_allow_html=True)
            regions_reload = db.query(Region).all()
            if regions_reload:
                del_opts = {f"{r.code} - {r.name}": r.id for r in regions_reload}
                del_choice = st.selectbox("选择要删除的区域", options=list(del_opts.keys()), key="del_region_sel")
                if st.button("🗑️ 删除", key="del_region", use_container_width=True):
                    rid = del_opts[del_choice]
                    r = db.query(Region).get(rid)
                    if r:
                        if len(r.parts) > 0:
                            st.error("该区域已被零件引用，不可删除！")
                        else:
                            db.delete(r)
                            db.commit()
                            st.success("✅ 删除成功！")
                            st.rerun()
    finally:
        db.close()


def _manage_material_type():
    db: Session = SessionLocal()
    try:
        col_list, col_form = st.columns([1.5, 1])

        with col_list:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">物料类型列表</h4>', unsafe_allow_html=True)
            mts = db.query(MaterialType).all()
            if mts:
                import pandas as pd
                data = [{"ID": m.id, "代码": m.code, "名称": m.name,
                         "描述": m.description or "",
                         "启用": "✅" if m.is_active else "❌"} for m in mts]
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无物料类型数据")

        with col_form:
            st.markdown('<h4 style="color:#1e293b;margin-bottom:16px;">新增物料类型</h4>', unsafe_allow_html=True)
            with st.form("add_mt_form", clear_on_submit=True):
                code = st.text_input("类型代码 *", placeholder="如: RAW")
                name = st.text_input("类型名称 *", placeholder="如: 原材料")
                desc = st.text_area("类型描述", height=80)
                is_active = st.checkbox("启用", value=True)
                submitted = st.form_submit_button("➕ 新增类型", use_container_width=True)

                if submitted:
                    if not code or not name:
                        st.error("请填写必填项")
                    else:
                        exists = db.query(MaterialType).filter_by(code=code.strip().upper()).first()
                        if exists:
                            st.error(f"类型代码 {code} 已存在")
                        else:
                            mt = MaterialType(code=code.strip().upper(), name=name.strip(),
                                             description=desc, is_active=is_active)
                            db.add(mt)
                            db.commit()
                            st.success(f"✅ 物料类型 {code} 创建成功！")
                            st.rerun()

            st.markdown('<h4 style="color:#1e293b;margin:20px 0 12px 0;">删除物料类型</h4>', unsafe_allow_html=True)
            mts_reload = db.query(MaterialType).all()
            if mts_reload:
                del_opts = {f"{m.code} - {m.name}": m.id for m in mts_reload}
                del_choice = st.selectbox("选择要删除的物料类型", options=list(del_opts.keys()), key="del_mt_sel")
                if st.button("🗑️ 删除", key="del_mt", use_container_width=True):
                    mid = del_opts[del_choice]
                    m = db.query(MaterialType).get(mid)
                    if m and len(m.parts) > 0:
                        st.error("该物料类型已被零件引用，不可删除！")
                    elif m:
                        db.delete(m)
                        db.commit()
                        st.success("✅ 删除成功！")
                        st.rerun()
    finally:
        db.close()
