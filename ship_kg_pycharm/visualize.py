"""
知识图谱可视化（Pyvis 交互式 HTML）
白色背景 · 蓝色节点/连线 · 黑色字体
"""
import json
import argparse
import networkx as nx
from pyvis.network import Network
from collections import Counter
import os

# 全局强制Python IO 使用UTF-8，根治GBK编码错误
os.environ["PYTHONUTF8"] = "1"

# ========== 颜色方案（白底蓝调） ==========
BG_COLOR       = "#ffffff"   # 背景：纯白
FONT_COLOR     = "#000000"   # 全局字体：纯黑
NODE_DEFAULT   = "#4a90d9"   # 节点默认：蓝色
NODE_HIGH_OUT  = "#1a6db5"   # 出度>入度：深蓝（活跃节点/源头）
NODE_HIGH_IN   = "#74b9e8"   # 入度>出度：浅蓝（汇聚节点）
NODE_BORDER    = "#1a5fa8"   # 节点边框
EDGE_DEFAULT   = "#4a90d9"   # 边默认颜色：蓝色

# 关系颜色（蓝色系渐变，保证和白背景对比度）
REL_COLORS = {
    "加工对象": "#2176ae",   # 深蓝
    "前置工序": "#e07b39",   # 橙（对比色，突出流程关系）
    "使用工具": "#1a9e6e",   # 深绿（工具）
    "使用材料": "#7b52ab",   # 紫（材料）
    "工艺参数": "#c0392b",   # 红（参数）
    "质量标准": "#0f7a6e",   # 深青（标准）
}


def build_graph(clean_json: str) -> nx.DiGraph:
    with open(clean_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    G = nx.DiGraph()
    for t in data["triples"]:
        G.add_edge(t["head"], t["tail"], relation=t["relation"])
    return G


def top_subgraph(G: nx.DiGraph, top_n: int = 100) -> nx.DiGraph:
    degrees = dict(G.degree())
    top_nodes = set([n for n, _ in Counter(degrees).most_common(top_n)])
    return G.subgraph(top_nodes).copy()


def key_subgraph(G: nx.DiGraph) -> nx.DiGraph:
    edges_to_keep = []
    for u, v, d in G.edges(data=True):
        if d.get("relation") in ("前置工序", "使用工具", "使用材料"):
            edges_to_keep.append((u, v, d))
    H = nx.DiGraph()
    for u, v, d in edges_to_keep:
        H.add_edge(u, v, relation=d["relation"])
    return H


def create_vis(G: nx.DiGraph, title: str, physics_config: dict = None) -> Network:
    net = Network(
        height="850px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor=BG_COLOR,
        font_color=FONT_COLOR,
        cdn_resources="remote"
    )

    in_deg  = dict(G.in_degree())
    out_deg = dict(G.out_degree())
    total_deg = dict(G.degree())

    # 添加节点
    for node in G.nodes():
        deg  = total_deg.get(node, 0)
        size = max(6, min(35, 4 + deg * 0.6))

        if out_deg.get(node, 0) > in_deg.get(node, 0):
            color = NODE_HIGH_OUT
        elif in_deg.get(node, 0) > out_deg.get(node, 0):
            color = NODE_HIGH_IN
        else:
            color = NODE_DEFAULT

        net.add_node(
            node,
            label=node,
            title=f"{node}\n入度:{in_deg.get(node,0)} 出度:{out_deg.get(node,0)}",
            size=size,
            color={
                "background": color,
                "border": NODE_BORDER,
                "highlight": {"background": "#f39c12", "border": "#e67e22"},
                "hover":     {"background": "#f0c040", "border": "#e67e22"},
            },
            font={"color": "#000000", "size": 13, "strokeWidth": 2, "strokeColor": "#ffffff"},
            borderWidth=1.5,
            borderWidthSelected=3,
        )

    # 添加边
    for u, v, d in G.edges(data=True):
        rel   = d.get("relation", "")
        color = REL_COLORS.get(rel, EDGE_DEFAULT)
        net.add_edge(
            u, v,
            title=rel,
            label=rel,
            color={"color": color, "highlight": "#e67e22", "hover": "#e67e22"},
            width=1.5,
            arrows={"to": {"enabled": True, "scaleFactor": 0.55}},
            smooth={"type": "curvedCW", "roundness": 0.15},
            font={"color": "#333333", "size": 9, "strokeWidth": 0, "background": "rgba(255,255,255,0.7)"},
        )

    # 物理布局
    if physics_config is None:
        physics_config = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -120,
                    "centralGravity": 0.005,
                    "springLength": 200,
                    "springConstant": 0.02,
                },
                "solver": "forceAtlas2Based",
                "stabilization": {"iterations": 300},
            },
            "edges": {
                "font": {
                    "size": 9,
                    "color": "#333333",
                    "strokeWidth": 0,
                    "background": "rgba(255,255,255,0.7)",
                },
            },
            "nodes": {
                "font": {
                    "size": 13,
                    "color": "#000000",
                    "strokeWidth": 2,
                    "strokeColor": "#ffffff",
                },
            },
            "interaction": {
                "hover": True,
                "tooltipDelay": 100,
                "navigationButtons": True,
                "keyboard": True,
            },
        }

    net.set_options(json.dumps(physics_config, ensure_ascii=False))
    return net


def save_html(net: Network, path: str):
    """直接调用 generate_html() 获取 HTML 字符串，UTF-8 写入，绕过 pyvis 的 GBK 编码问题"""
    html = net.generate_html()
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  已保存: {path}")


def main():
    parser = argparse.ArgumentParser(description="Pyvis 知识图谱可视化")
    parser.add_argument("--data", default="triples_clean.json")
    parser.add_argument("--top",  type=int, default=100)
    args = parser.parse_args()

    print(f"加载: {args.data}")
    G = build_graph(args.data)
    print(f"全图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")

    # ---- 第一张图：Top-N 子图 ----
    print(f"\n[1/2] 构建 Top-{args.top} 子图...")
    G_top = top_subgraph(G, top_n=args.top)
    print(f"  子图: {G_top.number_of_nodes()} 节点, {G_top.number_of_edges()} 边")
    net1 = create_vis(G_top, "船舶装配工艺知识图谱（Top节点）")
    save_html(net1, "kg_viz.html")

    # ---- 第二张图：工序流程子图 ----
    print(f"\n[2/2] 构建工序流程图...")
    G_key = key_subgraph(G)
    print(f"  子图: {G_key.number_of_nodes()} 节点, {G_key.number_of_edges()} 边")
    net2 = create_vis(G_key, "船舶装配工序流程图")
    save_html(net2, "kg_flow.html")

    print("\n=== 可视化完成 ===")
    print("请用浏览器打开 kg_viz.html / kg_flow.html")


if __name__ == "__main__":
    main()
