"""
图谱存储层——纯 NetworkX，零外部依赖
支持三种输入格式：
  1. triples_clean.json   — {"triples": [{"head":..., "relation":..., "tail":...}]}
  2. kg_graph.json        — {"edges": [{"source":..., "target":..., "relation":...}]}
  3. shipbuilding_kg.graphml — GraphML 格式
"""
import json
import networkx as nx
from pathlib import Path


class KnowledgeGraph:
    def __init__(self, source: str = None):
        """
        source 可以是文件路径，也可以是已构建好的 nx.DiGraph
        如果不传，按优先级自动检测: triples_clean.json > kg_graph.json > shipbuilding_kg.graphml
        """
        if isinstance(source, nx.DiGraph):
            self.G = source
            print(f"[图谱] 使用传入图: {self.G.number_of_nodes()} 节点, {self.G.number_of_edges()} 边")
        elif source and Path(source).exists():
            self.G = nx.DiGraph()
            self._load(source)
        else:
            self.G = nx.DiGraph()
            self._auto_load()

    def _auto_load(self):
        """按优先级自动检测并加载"""
        candidates = [
            ("triples_clean.json",       self._load_from_triples),
            ("kg_graph.json",            self._load_from_kg_json),
            ("shipbuilding_kg.graphml",  self._load_from_graphml),
        ]
        for filename, loader in candidates:
            if Path(filename).exists():
                loader(filename)
                return
        raise FileNotFoundError(
            "找不到数据文件。请将 triples_clean.json / kg_graph.json / shipbuilding_kg.graphml 放到当前目录"
        )

    def _load(self, path: str):
        p = Path(path)
        if p.suffix == ".graphml":
            self._load_from_graphml(path)
        else:
            # JSON 格式 —— 自动判断
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "triples" in data:
                self._load_triples(data["triples"])
            elif "edges" in data:
                self._load_edges(data["edges"])
            else:
                raise ValueError(f"无法识别的 JSON 格式: {path}")

    def _load_from_triples(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._load_triples(data["triples"])

    def _load_from_kg_json(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._load_edges(data.get("edges", []))

    def _load_from_graphml(self, path: str):
        self.G = nx.read_graphml(path)
        print(f"[图谱] GraphML: {self.G.number_of_nodes()} 节点, {self.G.number_of_edges()} 边")

    def _load_triples(self, triples: list):
        for t in triples:
            self.G.add_edge(t["head"], t["tail"], relation=t["relation"])
        print(f"[图谱] triples: {self.G.number_of_nodes()} 节点, {self.G.number_of_edges()} 边")

    def _load_edges(self, edges: list):
        for e in edges:
            self.G.add_edge(e["source"], e["target"], relation=e["relation"])
        print(f"[图谱] edges: {self.G.number_of_nodes()} 节点, {self.G.number_of_edges()} 边")

    # ---- 基础查询 ----

    def get_triples(self, entity=None, relation=None, limit=50):
        results = []
        for u, v, d in self.G.edges(data=True):
            rel = d.get("relation", "")
            if entity and u != entity and v != entity:
                continue
            if relation and rel != relation:
                continue
            results.append({"head": u, "relation": rel, "tail": v})
        return results[:limit]

    def get_neighbors(self, entity: str, depth: int = 1) -> list:
        visited = {entity}
        queue = [(entity, 0)]
        neighbors = []
        while queue:
            node, d = queue.pop(0)
            if d >= depth:
                continue
            for _, nb in self.G.out_edges(node):
                if nb not in visited:
                    visited.add(nb)
                    neighbors.append(nb)
                    queue.append((nb, d + 1))
            for nb, _ in self.G.in_edges(node):
                if nb not in visited:
                    visited.add(nb)
                    neighbors.append(nb)
                    queue.append((nb, d + 1))
        return neighbors

    # ---- 语义查询 ----

    def get_tools(self, entity: str) -> list:
        return [v for u, v, d in self.G.edges(data=True)
                if u == entity and d.get("relation") == "使用工具"]

    def get_materials(self, entity: str) -> list:
        return [v for u, v, d in self.G.edges(data=True)
                if u == entity and d.get("relation") == "使用材料"]

    def get_params(self, entity: str) -> list:
        return [v for u, v, d in self.G.edges(data=True)
                if u == entity and d.get("relation") == "工艺参数"]

    def get_standards(self, entity: str) -> list:
        return [v for u, v, d in self.G.edges(data=True)
                if u == entity and d.get("relation") == "质量标准"]

    def get_targets(self, entity: str) -> list:
        return [v for u, v, d in self.G.edges(data=True)
                if u == entity and d.get("relation") == "加工对象"]

    def get_prev_steps(self, entity: str) -> list:
        return [h for h, t, d in self.G.edges(data=True)
                if t == entity and d.get("relation") == "前置工序"]

    def get_next_steps(self, entity: str) -> list:
        return [t for h, t, d in self.G.edges(data=True)
                if h == entity and d.get("relation") == "前置工序"]

    def bfs_triples(self, entities: list, max_depth: int = 2, max_triples: int = 50) -> list:
        visited_triples = set()
        visited_nodes = set()
        queue = [(e, 0) for e in entities]

        while queue and len(visited_triples) < max_triples:
            node, depth = queue.pop(0)
            if node in visited_nodes or depth > max_depth:
                continue
            visited_nodes.add(node)

            for _, tail, d in self.G.out_edges(node, data=True):
                key = (node, d.get("relation", ""), tail)
                if key not in visited_triples:
                    visited_triples.add(key)
                    if depth < max_depth:
                        queue.append((tail, depth + 1))

            for head, _, d in self.G.in_edges(node, data=True):
                key = (head, d.get("relation", ""), node)
                if key not in visited_triples:
                    visited_triples.add(key)
                    if depth < max_depth:
                        queue.append((head, depth + 1))

        return [{"head": h, "relation": r, "tail": t} for h, r, t in visited_triples]

    def find_entity(self, keyword: str) -> list:
        return [n for n in self.G.nodes() if keyword in n]

    def get_all_entities(self) -> list:
        return list(self.G.nodes())

    def get_all_relations(self) -> list:
        return list({d.get("relation", "") for _, _, d in self.G.edges(data=True)})

    def export_json(self, path: str = "kg_graph.json"):
        edges = [{"source": u, "relation": d.get("relation", ""), "target": v}
                 for u, v, d in self.G.edges(data=True)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(edges, f, ensure_ascii=False, indent=2)
        print(f"[图谱] 已导出 {len(edges)} 条边到 {path}")

    def export_graphml(self, path: str = "shipbuilding_kg.graphml"):
        nx.write_graphml(self.G, path)
        print(f"[图谱] 已导出 GraphML 到 {path}")


# ============ 测试 ============
if __name__ == "__main__":
    kg = KnowledgeGraph()  # 自动检测数据文件
    print(f"\n节点数: {kg.G.number_of_nodes()}")
    print(f"边数:   {kg.G.number_of_edges()}")
    print(f"关系类型: {kg.get_all_relations()}")
    print(f"\n--- 测试查询 ---")
    print("焊接工具:", kg.get_tools("焊接"))
    print("焊接材料:", kg.get_materials("焊接"))
    print("焊接前序:", kg.get_prev_steps("焊接"))
    print("焊接后序:", kg.get_next_steps("焊接"))
    print("搜索'船体':", kg.find_entity("船体")[:10])
