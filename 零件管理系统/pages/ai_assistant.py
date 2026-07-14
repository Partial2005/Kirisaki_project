"""AI 助手页面 - 基于LLM的智能问答"""

import streamlit as st
from sqlalchemy.orm import Session
import sys, os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import SessionLocal, Part, BOM, CostItem, Currency, MaterialType, Unit, Region


def get_system_data_summary():
    db: Session = SessionLocal()
    try:
        parts = db.query(Part).all()
        cost_items = db.query(CostItem).all()
        boms = db.query(BOM).all()

        parts_info = []
        for p in parts:
            cost = db.query(CostItem).filter_by(part_id=p.id).first()
            parts_info.append({
                "编码": p.part_code,
                "名称": p.name,
                "物料类型": p.material_type.name if p.material_type else "-",
                "状态": p.status,
                "重量": f"{p.weight}{p.weight_unit.code if p.weight_unit else ''}" if p.weight else "-",
                "总成本": f"¥{cost.total_cost:,.2f}" if cost else "未录入",
                "供应商": p.supplier or "-",
            })

        bom_summary = []
        for b in boms:
            bom_summary.append({
                "父零件": b.parent_part.part_code if b.parent_part else "-",
                "子零件": b.child_part.part_code if b.child_part else "-",
                "子零件名": b.child_part.name if b.child_part else "-",
                "用量": b.quantity,
            })

        cost_summary = []
        for c in cost_items:
            cost_summary.append({
                "零件": c.part.part_code if c.part else "-",
                "名称": c.part.name if c.part else "-",
                "材料成本": c.material_cost,
                "制造成本": c.manufacturing_cost,
                "间接费用": c.overhead_cost,
                "总成本": c.total_cost,
                "货币": c.currency.code if c.currency else "CNY",
            })

        return {
            "零件列表": parts_info,
            "BOM数据": bom_summary,
            "成本数据": cost_summary,
        }
    finally:
        db.close()


def get_ai_response(user_message: str, chat_history: list, system_data: dict) -> str:
    try:
        import openai
        import os

        system_prompt = f"""你是零件成本管理系统的智能助手。你的任务是帮助用户理解和分析零件成本数据。

当前系统数据摘要：
{json.dumps(system_data, ensure_ascii=False, indent=2)}

你可以回答关于以下方面的问题：
1. 零件信息查询（哪个零件成本最高、某零件的物料构成等）
2. BOM结构分析（某零件包含哪些子件、层级关系）
3. 成本分析与优化建议（成本构成分析、降本建议）
4. 数据治理知识（解释主数据、事务数据、元数据等概念）
5. 系统使用帮助

请用简洁专业的中文回答，适当使用数字和百分比来支持你的分析。
如果问题需要计算，请展示计算过程。"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        client = openai.OpenAI(
            base_url=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "sk-placeholder")
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return _rule_based_response(user_message, system_data)


def _rule_based_response(user_message: str, system_data: dict) -> str:
    msg_lower = user_message.lower()
    parts = system_data.get("零件列表", [])
    costs = system_data.get("成本数据", [])
    boms = system_data.get("BOM数据", [])

    if "最高" in user_message and "成本" in user_message:
        if costs:
            max_cost = max(costs, key=lambda x: x["总成本"])
            return f"""📊 **成本最高的零件**

零件编码：**{max_cost['零件']}**
零件名称：{max_cost['名称']}
总成本：**¥{max_cost['总成本']:,.2f}**

成本构成：
- 材料成本：¥{max_cost['材料成本']:,.2f}（占比 {max_cost['材料成本']/max_cost['总成本']*100:.1f}%）
- 制造成本：¥{max_cost['制造成本']:,.2f}（占比 {max_cost['制造成本']/max_cost['总成本']*100:.1f}%）  
- 间接费用：¥{max_cost['间接费用']:,.2f}（占比 {max_cost['间接费用']/max_cost['总成本']*100:.1f}%）

💡 **降本建议**：该零件成本较高，建议重点优化材料采购成本，可考虑引入备选供应商或通过批量采购降低单价。"""

    if "总成本" in user_message or "成本统计" in user_message or "成本汇总" in user_message:
        if costs:
            total = sum(c["总成本"] for c in costs)
            avg = total / len(costs)
            response = f"📊 **全局成本统计**\n\n"
            response += f"- 零件总数（有成本数据）：{len(costs)} 件\n"
            response += f"- 成本价值总计：¥{total:,.2f}\n"
            response += f"- 平均零件成本：¥{avg:,.2f}\n\n"
            response += "**各零件成本明细：**\n"
            for c in sorted(costs, key=lambda x: x["总成本"], reverse=True):
                response += f"- {c['零件']} ({c['名称']})：¥{c['总成本']:,.2f}\n"
            return response

    if "bom" in msg_lower or "子件" in user_message or "物料清单" in user_message:
        if boms:
            from collections import defaultdict
            parent_map = defaultdict(list)
            for b in boms:
                parent_map[b["父零件"]].append(b)

            response = "📋 **BOM物料清单汇总**\n\n"
            for parent, children in parent_map.items():
                response += f"**{parent}** 包含 {len(children)} 个子件：\n"
                for c in children:
                    response += f"  - {c['子零件']} ({c['子零件名']}) × {c['用量']}\n"
                response += "\n"
            return response

    if "零件" in user_message and ("列表" in user_message or "有哪些" in user_message or "所有" in user_message):
        response = f"🔩 **系统零件列表**（共 {len(parts)} 件）\n\n"
        for p in parts:
            response += f"- **{p['编码']}** {p['名称']} | {p['物料类型']} | {p['总成本']}\n"
        return response

    if "主数据" in user_message:
        return """📚 **主数据（Master Data）**

主数据是指企业中描述核心业务实体的数据，具有以下特征：

✅ **高价值性**：对业务运作具有基础性、全局性的支撑作用
✅ **相对稳定性**：变更频率低，生命周期长
✅ **唯一权威性**：有且仅有一个数据源（即"数据同源"原则）
✅ **广泛共享性**：被多个业务系统、多个流程共同使用

本系统中，**零件（Part）** 就是核心主数据：
- 零件编码是唯一业务标识
- 所有BOM和成本记录都以零件为基础
- 零件信息变更需要严格的版本管理

💡 这体现了数据治理中"主数据治理"的核心原则。"""

    if "元数据" in user_message:
        return """📚 **元数据（Metadata）**

元数据是"描述数据的数据"，帮助我们理解数据的含义、来源和结构。

本系统的元数据字典（数据地图）包含：
- **表级元数据**：表名、描述、数据分类、业务负责人、更新频率
- **字段级元数据**：字段名、显示名、数据类型、是否主/外键、字段描述
- **关系元数据**：表间关联关系、关联字段、关联类型

华为提出的"数据地图"就是一套企业级元数据管理系统，帮助员工：
1. **找得到**：快速定位所需数据在哪里
2. **读得懂**：理解数据字段的业务含义
3. **用得好**：了解数据质量和可信度

您可以访问「数据地图」页面查看本系统的完整元数据字典。"""

    if "降本" in user_message or "优化" in user_message or "建议" in user_message:
        if costs:
            high_mat = [c for c in costs if c["材料成本"] > 0 and c["材料成本"] / max(c["总成本"], 1) > 0.6]
            high_mfg = [c for c in costs if c["制造成本"] > 0 and c["制造成本"] / max(c["总成本"], 1) > 0.3]

            response = "💡 **成本优化建议**\n\n"

            if high_mat:
                response += f"**材料成本占比较高的零件（>60%）：**\n"
                for c in high_mat:
                    pct = c["材料成本"] / c["总成本"] * 100
                    response += f"- {c['零件']}（{c['名称']}）：材料占 {pct:.1f}%，建议优化供应链\n"
                response += "\n"

            if high_mfg:
                response += f"**制造成本占比较高的零件（>30%）：**\n"
                for c in high_mfg:
                    pct = c["制造成本"] / c["总成本"] * 100
                    response += f"- {c['零件']}（{c['名称']}）：制造占 {pct:.1f}%，建议优化工艺\n"
                response += "\n"

            response += "**通用降本策略：**\n"
            response += "1. 🏭 工艺优化：减少加工工序，提高设备利用率\n"
            response += "2. 🤝 供应商管理：引入备选供应商，增加议价能力\n"
            response += "3. 📦 标准化设计：提高零件通用性，扩大批量采购规模\n"
            response += "4. ♻️ 循环利用：对报废零件进行材料回收降低成本\n"
            return response

    return f"""我是零件成本管理系统的智能助手 🤖

我可以帮您解答：

📊 **数据查询**：零件信息、成本数据、BOM结构
💰 **成本分析**：成本构成、最高/最低成本、优化建议
📚 **知识解答**：主数据、元数据、BOM、数据治理概念
🔍 **系统帮助**：如何使用系统各功能模块

当前系统有 **{len(parts)}** 个零件，**{len(boms)}** 条BOM记录，**{len(costs)}** 条成本数据。

请问您想了解什么？例如：
- "哪个零件成本最高？"
- "传动轴组件的BOM结构是什么？"
- "给我一些成本优化建议"
- "什么是主数据？"
"""


def show():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🤖 AI 智能助手</div>
        <div class="page-subtitle">基于 LLM 的数据洞察与智能问答</div>
    </div>
    """, unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "system_data" not in st.session_state:
        st.session_state.system_data = get_system_data_summary()

    # 处理推荐问题触发
    if "pending_question" in st.session_state and st.session_state.pending_question:
        pending_q = st.session_state.pending_question
        st.session_state.pending_question = None
        st.session_state.chat_history.append({"role": "user", "content": pending_q})
        st.rerun()

    # ===== 聊天输入框（内置发送按钮，简约美观）=====
    user_input = st.chat_input("请输入您的问题，如：哪个零件成本最高？")

    # 处理用户输入
    if user_input and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})

    # ===== 聊天区域 =====
    col_chat, col_info = st.columns([2, 1])

    with col_chat:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center;padding:60px 20px;background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:3rem;margin-bottom:16px;">🤖</div>
                <div style="color:#0f172a;font-size:1.05rem;font-weight:700;margin-bottom:8px;">AI 智能助手</div>
                <div style="color:#475569;font-size:0.9rem;line-height:1.8;font-weight:500;">
                    我是零件成本管理系统的智能助手<br>
                    我可以帮您分析成本数据、查询零件信息、解答数据治理问题<br>
                    请在上方输入您的问题开始对话
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 渲染历史消息
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 检查最后一条消息是否是用户消息且还没有AI回复 → 调用AI
    if (st.session_state.chat_history
            and st.session_state.chat_history[-1]["role"] == "user"):
        last_msg = st.session_state.chat_history[-1]["content"]
        # 在聊天区域显示AI思考中
        with col_chat:
            with st.chat_message("assistant"):
                with st.spinner("AI 思考中..."):
                    response = get_ai_response(last_msg, st.session_state.chat_history[:-1], st.session_state.system_data)
                st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    with col_info:
        system_data = st.session_state.system_data
        parts_count = len(system_data.get("零件列表", []))
        bom_count = len(system_data.get("BOM数据", []))
        cost_count = len(system_data.get("成本数据", []))
        costs = system_data.get("成本数据", [])
        total_cost = sum(c["总成本"] for c in costs)

        st.markdown(f"""
        <div class="content-card" style="margin-bottom:16px;">
            <h4 style="color:#0f172a;margin:0 0 16px 0;font-size:0.9rem;font-weight:700;">📊 数据快速摘要</h4>
            <div style="display:flex;flex-direction:column;gap:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#334155;font-size:0.85rem;font-weight:500;">🔩 零件总数</span>
                    <span style="color:#2563eb;font-weight:700;">{parts_count}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#334155;font-size:0.85rem;font-weight:500;">📋 BOM记录</span>
                    <span style="color:#d97706;font-weight:700;">{bom_count}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#334155;font-size:0.85rem;font-weight:500;">💰 成本数据</span>
                    <span style="color:#059669;font-weight:700;">{cost_count}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid #e2e8f0;padding-top:12px;margin-top:4px;">
                    <span style="color:#1e293b;font-size:0.85rem;font-weight:600;">成本总值</span>
                    <span style="color:#7c3aed;font-weight:700;">¥{total_cost:,.0f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="content-card">
            <h4 style="color:#0f172a;margin:0 0 12px 0;font-size:0.9rem;font-weight:700;">💡 推荐问题</h4>
        """, unsafe_allow_html=True)

        recommend_qs = [
            "哪个零件成本最高？",
            "分析成本优化方向",
            "传动轴组件包含哪些子件？",
            "什么是数据同源原则？",
            "成本计算规则是什么？",
        ]

        for q in recommend_qs:
            if st.button(f"💬 {q}", key=f"rec_{q}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
