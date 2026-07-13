"""
步骤2：三元组深度精炼（在 step1_clean.py 基础上二次筛选）
输入: triples_clean.json
输出: triples_clean.json（覆盖原文件）
"""
import json
import re
from collections import Counter

INPUT_FILE = "triples_clean.json"
OUTPUT_FILE = "triples_clean.json"

# ========== 规则参数 ==========
MAX_HEAD_LEN = 12   # head 最大字数
MAX_TAIL_LEN = 15   # tail 最大字数（收紧，原来是20）

# tail 句子片段特征（说明 tail 是截断自然语言，不是知识点）
TAIL_FRAGMENT_PATTERNS = [
    r"^下面", r"^这是", r"^这里", r"^其中", r"^因此",
    r"^所以", r"^同时", r"^通过", r"^一般", r"^如果",
    r"^当[^时]", r"^为了", r"^由于", r"^此外", r"^对于",
    r"^在[^厂船]", r"^我国",
    r"阶段$", r"阶段[^工]",   # "装配阶段"这种概念短语也要过滤
    r"还.{0,5}考虑", r"指在", r"即可$", r"应该$",
    r"已预先", r"的方法代替", r"提供的施工依据",
    r"外壳板$", r"各厂均", r"代替样板",
    r"艇装阶段",
]

# head 句子片段特征
HEAD_FRAGMENT_PATTERNS = [
    r"[，。、；：！？（）【】]",
    r"^在", r"^这", r"^当", r"^如",
]

# tail 中文标点（排除"·"点号）
TAIL_PUNCT_PATTERN = re.compile(r"[，。、；：！？（）【】…—]")

# 领域停用词：作为独立节点毫无意义的短词
STOPWORDS = {
    "的", "了", "和", "与", "及", "等", "中",
    "之", "也", "且", "而", "或",
}


def is_bad_head(head: str) -> bool:
    if len(head) <= 1:
        return True
    if len(head) > MAX_HEAD_LEN:
        return True
    for p in HEAD_FRAGMENT_PATTERNS:
        if re.search(p, head):
            return True
    if head in STOPWORDS:
        return True
    return False


def is_bad_tail(tail: str) -> bool:
    if len(tail) <= 1:
        return True
    if len(tail) > MAX_TAIL_LEN:
        return True
    if TAIL_PUNCT_PATTERN.search(tail):
        return True
    if tail in STOPWORDS:
        return True
    if re.match(r"^\d+\.?\d*$", tail):   # 纯数字
        return True
    if re.search(r"\d{4,}", tail):        # 含4位以上数字串
        return True
    for p in TAIL_FRAGMENT_PATTERNS:
        if re.search(p, tail):
            return True
    return False


def refine():
    print(f"加载: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    triples = data["triples"]
    print(f"输入三元组: {len(triples)} 条")

    removed = Counter()
    clean_list = []

    for t in triples:
        h, r, tl = t["head"].strip(), t["relation"], t["tail"].strip()
        if is_bad_head(h):
            removed["bad_head"] += 1
            continue
        if is_bad_tail(tl):
            removed["bad_tail"] += 1
            continue
        clean_list.append({"head": h, "relation": r, "tail": tl})

    # 去重
    seen = set()
    dedup = []
    for t in clean_list:
        key = (t["head"], t["relation"], t["tail"])
        if key not in seen:
            seen.add(key)
            dedup.append(t)

    dup_count = len(clean_list) - len(dedup)

    # 统计
    entities_set = set()
    rel_counter = Counter()
    for t in dedup:
        entities_set.add(t["head"])
        entities_set.add(t["tail"])
        rel_counter[t["relation"]] += 1

    print(f"\n=== 精炼结果 ===")
    print(f"过滤 bad_head:   {removed['bad_head']} 条")
    print(f"过滤 bad_tail:   {removed['bad_tail']} 条")
    print(f"去重删除:         {dup_count} 条")
    print(f"---")
    print(f"精炼后三元组:     {len(dedup)} 条")
    print(f"实体数:          {len(entities_set)}")
    print(f"\n关系分布:")
    for rel, cnt in rel_counter.most_common():
        print(f"  {rel}: {cnt}")

    output = {
        "total": len(dedup),
        "entities": len(entities_set),
        "relation_distribution": dict(rel_counter),
        "triples": dedup,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n已保存: {OUTPUT_FILE}")
    print("=== 精炼完成 ===")


if __name__ == "__main__":
    refine()
