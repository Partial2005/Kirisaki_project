# ============================================================
# Cell 2: 图谱存储与查询（NetworkX 方案，无需 Neo4j）
# 前置: pip install networkx  （大部分环境自带）
# 输入: triples_clean.json
# ============================================================
import json
import networkx as nx
from collections import defaultdict, Counter

# ---------- 1. 加载三元组 ----------
with open("triples_clean.json", "r", encoding="utf-8") as f:
    data = json.load(f)

triples = data["triples"]
print(f"加载了 {len(triples)} 条三元组")

# ---------- 2. 构建 NetworkX 有向图 ----------
G = nx.DiGraph()

for t in triples:
    h, r, tl = t["head"], t["relation"], t["tail"]

    # 添加节点（只添加一次，后续自动跳过）
    G.add_node(h, type="entity")
    G.add_node(tl, type="entity")

    # 添加边
    G.add_edge(h, tl, relation=r)

print(f"图谱: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")


# ---------- 3. 查询接口 ----------
class KnowledgeGraph:
    def __init__(self, graph):
        self.G = graph
        # 构建关系索引
        self._by_relation = defaultdict(list)
        for u, v, d in graph.edges(data=True):
            rel = d.get("relation", "")
            self._by_relation[rel].append((u, v))

    def get_neighbors(self, entity, direction="both", max_depth=1):
        """获取实体的邻居节点"""
        neighbors = set()
        queue = [(entity, 0)]
        visited = {entity}

        while queue:
            node, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            if direction in ("out", "both"):
                for _, nb in self.G.out_edges(node):
                    if nb not in visited:
                        visited.add(nb)
                        neighbors.add(nb)
                        queue.append((nb, depth + 1))

            if direction in ("in", "both"):
                for nb, _ in self.G.in_edges(node):
                    if nb not in visited:
                        visited.add(nb)
                        neighbors.add(nb)
                        queue.append((nb, depth + 1))

        return neighbors

    def get_triples(self, entity=None, relation=None):
        """按条件检索三元组"""
        results = []
        for u, v, d in self.G.edges(data=True):
            rel = d.get("relation", "")
            if entity and u != entity and v != entity:
                continue
            if relation and rel != relation:
                continue
            results.append((u, rel, v))
        return results

    def get_process_chain(self, start_entity, max_length=10):
        """获取工序链（沿前置工序走）"""
        chain = [start_entity]
        current = start_entity
        for _ in range(max_length):
            # 查当前节点的下一个工序
            next_nodes = [
                v
                for u, v, d in self.G.edges(data=True)
                if u == current and d.get("relation") == "前置工序"
            ]
            if not next_nodes:
                break
            # 取第一个（如果有多条，选出现次数最多的）
            current = next_nodes[0]
            if current in chain:  # 防止环
                break
            chain.append(current)
        return chain

    def get_tools(self, entity):
        """获取实体使用的工具"""
        return [
            v
            for u, v, d in self.G.edges(data=True)
            if u == entity and d.get("relation") == "使用工具"
        ]

    def get_materials(self, entity):
        """获取实体使用的材料"""
        return [
            v
            for u, v, d in self.G.edges(data=True)
            if u == entity and d.get("relation") == "使用材料"
        ]

    def get_params(self, entity):
        """获取实体的工艺参数"""
        return [
            v
            for u, v, d in self.G.edges(data=True)
            if u == entity and d.get("relation") == "工艺参数"
        ]

    def get_targets(self, entity):
        """获取实体的加工对象"""
        return [
            v
            for u, v, d in self.G.edges(data=True)
            if u == entity and d.get("relation") == "加工对象"
        ]

    def stats(self):
        """图谱统计"""
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "relations": dict(Counter(d.get("relation", "") for _, _, d in self.G.edges(data=True))),
            "top_entities": [
                (node, deg)
                for node, deg in sorted(self.G.degree(), key=lambda x: -x[1])[:10]
            ],
        }


kg = KnowledgeGraph(G)

# ---------- 4. 测试查询 ----------
print("\n" + "=" * 50)
print("图谱查询测试")
print("=" * 50)

# 测试1: 工序链
chain = kg.get_process_chain("放样")
print(f"\n工序链(放样): {' -> '.join(chain)}")

chain2 = kg.get_process_chain("切割")
print(f"工序链(切割): {' -> '.join(chain2)}")

# 测试2: 工具和材料
print(f"\n焊接使用的工具: {kg.get_tools('焊接')}")
print(f"焊接使用的材料: {kg.get_materials('焊接')}")
print(f"装配使用的工具: {kg.get_tools('装配')}")
print(f"装配使用的材料: {kg.get_materials('装配')}")

# 测试3: 工艺参数
print(f"\n焊接的工艺参数: {kg.get_params('焊接')}")
print(f"放样的工艺参数: {kg.get_params('放样')}")

# 测试4: 邻居节点
neighbors = kg.get_neighbors("焊接", max_depth=1)
print(f"\n焊接的1跳邻居: {neighbors}")

# 测试5: 全局统计
stats = kg.stats()
print(f"\n图谱统计:")
print(f"  节点数: {stats['nodes']}")
print(f"  边数: {stats['edges']}")
print(f"  关系分布: {dict(stats['relations'])}")
print(f"  核心实体: {stats['top_entities']}")

# ---------- 5. 持久化（可选） ----------
# NetworkX 图可以直接导出为 GraphML（标准格式，可被 Gephi 等工具打开）
nx.write_graphml(G, "shipbuilding_kg.graphml")
print(f"\n图谱已保存为 shipbuilding_kg.graphml")

# 也可以导出为 JSON 方便程序读取
graph_json = {
    "nodes": [{"id": n, "degree": G.degree(n)} for n in G.nodes()],
    "edges": [
        {"source": u, "target": v, "relation": d.get("relation", "")}
        for u, v, d in G.edges(data=True)
    ],
}
with open("kg_graph.json", "w", encoding="utf-8") as f:
    json.dump(graph_json, f, ensure_ascii=False, indent=2)
print(f"图谱已保存为 kg_graph.json")

print("\n=== 图谱存储完成，后续 RAG 系统直接使用 kg 对象 ===")
