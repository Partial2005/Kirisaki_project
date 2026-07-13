"""
知识图谱 + 向量融合 RAG 问答系统（PyCharm 本地版）
"""
import json
import argparse
import os
import sys

# ---- 必须在导入 sentence_transformers 之前设置 ----
# 优先用镜像加速；如果都连不上，设离线模式避免卡死重试
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import numpy as np

# 尝试导入，失败就降级
try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except ImportError:
    _HAS_ST = False
    print("[RAG] ⚠ sentence-transformers 未安装，向量召回不可用")

from graph_store import KnowledgeGraph

# ---- DeepSeek V4 Pro ----
LLM_CONFIG = {
    "api_key":  "sk-bd9e5775edb04418a0c09b8b30f45433",
    "base_url": "https://api.deepseek.com/v1",
    "model":    "deepseek-chat",
}

# 也支持用环境变量（优先级高于上面的配置）
LLM_CONFIG["api_key"]  = os.environ.get("LLM_API_KEY",  LLM_CONFIG["api_key"])
LLM_CONFIG["base_url"] = os.environ.get("LLM_BASE_URL", LLM_CONFIG["base_url"])
LLM_CONFIG["model"]    = os.environ.get("LLM_MODEL",    LLM_CONFIG["model"])

# RAG 系统
class RAGSystem:
    def __init__(self, clean_json="triples_clean.json",
                 embedding_model="all-MiniLM-L6-v2",
                 llm_backend="openai"):
        print(f"[RAG] 加载知识图谱...")
        self.kg = KnowledgeGraph(clean_json)

        # ---- 加载 embedding 模型（网络不通自动降级） ----
        self.encoder = None
        self.has_vector = False

        if not _HAS_ST:
            print(f"[RAG] ℹ sentence-transformers 不可用，纯图谱检索模式")
        else:
            print(f"[RAG] 加载 embedding 模型: {embedding_model}")
            try:
                # 先尝试离线加载（本地已有模型）
                self.encoder = SentenceTransformer(
                    embedding_model, local_files_only=True
                )
                self.has_vector = True
                print(f"[RAG] ✓ 离线加载成功")
            except Exception:
                try:
                    # 再试在线加载（设短超时避免死等）
                    self.encoder = SentenceTransformer(
                        embedding_model, local_files_only=False
                    )
                    self.has_vector = True
                    print(f"[RAG] ✓ 在线加载成功")
                except Exception as e:
                    print(f"[RAG] ⚠ embedding 模型加载失败: {e}")
                    print(f"[RAG] ℹ 将降级为纯图谱检索模式（无向量召回）")
                    print(f"[RAG] 💡 要启用向量召回，请手动下载模型:")
                    print(f"        pip install sentence-transformers")
                    print(f"        python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')\"")

        self.llm_backend = llm_backend
        self.llm_client = None
        self.ollama_model = "qwen2:7b"

        self._build_index()

    def _build_index(self):
        self.texts = []
        for i, (u, v, d) in enumerate(self.kg.G.edges(data=True)):
            rel = d.get("relation", "")
            self.texts.append(f"{u}的{rel}是{v}")

        if not self.has_vector:
            self.embeddings = None
            print(f"[RAG] 跳过向量化（无 encoder）")
            return

        print(f"[RAG] 向量化 {len(self.texts)} 条文本...")
        self.embeddings = self.encoder.encode(
            self.texts, show_progress_bar=True, normalize_embeddings=True
        )
        print(f"[RAG] 索引: {self.embeddings.shape}")

    # ============ 检索 ============

    def vector_search(self, query: str, top_k: int = 5) -> list:
        if not self.has_vector or self.embeddings is None:
            return []  # 降级模式，无向量召回
        q_emb = self.encoder.encode([query], normalize_embeddings=True)[0]
        scores = np.dot(self.embeddings, q_emb)
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [{"id": int(idx), "text": self.texts[idx], "score": float(scores[idx])}
                for idx in top_idx]

    def kg_search(self, query: str, top_k: int = 30) -> list:
        all_nodes = self.kg.get_all_entities()
        matched = [n for n in all_nodes if len(n) >= 2 and n in query]
        if not matched:
            return []
        return self.kg.bfs_triples(matched, max_depth=2, max_triples=top_k)

    def fusion_search(self, query: str) -> dict:
        return {
            "vector_results": self.vector_search(query, top_k=5),
            "kg_results": self.kg_search(query, top_k=30),
        }

    # ============ 答案生成 ============

    def _build_context(self, question: str, result: dict) -> str:
        parts = []

        if result["kg_results"]:
            parts.append("【知识图谱三元组】")
            for t in result["kg_results"][:25]:
                parts.append(f"- {t['head']} → [{t['relation']}] → {t['tail']}")
            parts.append("")

        if result["vector_results"]:
            parts.append("【语义相似文本】")
            for r in result["vector_results"]:
                parts.append(f"- (相似度:{r['score']:.3f}) {r['text']}")
            parts.append("")

        return "\n".join(parts)

    def _answer_template(self, question: str, result: dict) -> str:
        kgs = result["kg_results"]
        all_nodes = self.kg.get_all_entities()
        entities = [n for n in all_nodes if len(n) >= 2 and n in question]
        main = entities[0] if entities else None

        lines = [f"## {question}\n"]

        if main:
            lines.append(f"**核心实体**: {main}\n")
            for label, func in [
                ("前置工序", self.kg.get_prev_steps),
                ("后续工序", self.kg.get_next_steps),
                ("使用工具", self.kg.get_tools),
                ("使用材料", self.kg.get_materials),
                ("工艺参数", self.kg.get_params),
                ("质量标准", self.kg.get_standards),
                ("加工对象", self.kg.get_targets),
            ]:
                items = func(main)
                if items:
                    lines.append(f"- **{label}**: {', '.join(items[:8])}")
        else:
            lines.append("**未找到匹配实体，请查看以下相关内容:**")

        lines.append("\n**关联三元组**:")
        for t in kgs[:15]:
            lines.append(f"  - {t['head']} → [{t['relation']}] → {t['tail']}")
        return "\n".join(lines)

    def _answer_openai(self, question: str, result: dict) -> str:
        if self.llm_client is None:
            from openai import OpenAI
            self.llm_client = OpenAI(
                api_key=LLM_CONFIG["api_key"],
                base_url=LLM_CONFIG["base_url"],
            )
            print(f"[LLM] 已连接: {LLM_CONFIG['base_url']} (模型: {LLM_CONFIG['model']})")

        context = self._build_context(question, result)

        system_prompt = (
            "你是船舶装配工艺专家，精通《中级船体装配工工艺学》。"
            "根据提供的知识图谱三元组和文本参考来回答问题。"
            "用中文回答，简洁专业，必须引用具体的工艺知识。"
            "如果你不确定某个细节，诚实地说出来，但整体上要给出有用的回答。"
        )

        user_prompt = f"""请回答以下问题。下方是知识库中检索到的相关内容：

{context}

====

问题：{question}

请直接回答，引用具体工艺知识。"""

        resp = self.llm_client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        return resp.choices[0].message.content

    def _answer_ollama(self, question: str, result: dict) -> str:
        import ollama
        context = self._build_context(question, result)
        prompt = f"""你是船舶装配工艺专家。根据以下知识回答问题。用中文回答，简洁专业。

{context}

问题：{question}

请直接回答，引用具体工艺知识。"""
        resp = ollama.chat(
            model=self.ollama_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["message"]["content"]

    # ============ 对外接口 ============

    def ask(self, question: str, verbose: bool = True) -> str:
        result = self.fusion_search(question)

        if self.llm_backend == "openai":
            answer = self._answer_openai(question, result)
        elif self.llm_backend == "ollama":
            answer = self._answer_ollama(question, result)
        else:
            answer = self._answer_template(question, result)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Q: {question}")
            print(f"{'='*60}")
            if result["kg_results"]:
                print(f"[KG] 命中 {len(result['kg_results'])} 条三元组")
            if result["vector_results"]:
                print(f"[Vec] 命中 {len(result['vector_results'])} 条文本")
            print(answer)

        return answer


# ============ 交互入口 ============

def interactive(rag: RAGSystem):
    print("\n" + "=" * 60)
    print("船舶装配工艺 RAG 问答系统")
    print(f"答案后端: {rag.llm_backend}")
    if rag.llm_backend == "openai":
        print(f"API: {LLM_CONFIG['base_url']}")
        print(f"模型: {LLM_CONFIG['model']}")
    print(f"图谱: {rag.kg.G.number_of_nodes()} 节点, {rag.kg.G.number_of_edges()} 边")
    print(f"索引: {len(rag.texts)} 条")
    print("输入 quit 退出 | search 关键词 搜实体")
    print("=" * 60)

    while True:
        try:
            q = input("\n>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q"):
            print("再见!")
            break
        if q.lower().startswith("search "):
            kw = q[7:]
            matches = rag.kg.find_entity(kw)
            print(f"匹配实体 ({len(matches)}): {matches[:20]}")
            continue
        rag.ask(q)


def run_tests(rag: RAGSystem):
    questions = [
        "焊接需要什么工具和材料？",
        "装配的前置工序有哪些？",
        "除锈和涂装是什么关系？",
        "放样有什么工艺参数和质量标准？",
        "船体分段装配的流程是怎样的？",
    ]
    for q in questions:
        rag.ask(q)


# ============ main ============

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="船体装配工艺 RAG 问答")
    parser.add_argument("--backend", default="openai",
                        choices=["openai", "template", "ollama"],
                        help="答案生成后端 (default: openai)")
    parser.add_argument("--test", action="store_true",
                        help="运行预设测试问题后退出")
    parser.add_argument("--model", default="all-MiniLM-L6-v2",
                        help="Embedding 模型名")
    parser.add_argument("--data", default="triples_clean.json",
                        help="清洗后的三元组文件")
    args = parser.parse_args()

    rag = RAGSystem(
        clean_json=args.data,
        embedding_model=args.model,
        llm_backend=args.backend,
    )

    if args.test:
        run_tests(rag)
    else:
        interactive(rag)
