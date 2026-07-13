"""
步骤1：三元组清洗
输入: triples_final.json（放在本目录下）
输出: triples_clean.json + 统计报告
"""
import json
import re
from collections import Counter

INPUT_FILE = "triples_final.json"
OUTPUT_FILE = "triples_clean.json"

# ============ 过滤规则 ============
MAX_TAIL_LEN = 20

SENTENCE_FRAGMENT_KEYWORDS = [
    "也可用作", "由于", "习惯上", "从而导致",
    "停靠码头", "坞内涂装", "船舶停靠",
    "但未最后", "却也加大", "大型分段虽减少",
    "前后或左右相邻", "火工矫正及机械原因",
    "分段和船台上都已预先", "从底部分段上中心线",
    "悬线锤至", "用卷尺里得",
    "预合拢的犬分段",
    "分段大接缝的壳板",
    "小合拢阶段中合拢阶段",
]


def is_bad_tail(tail: str, relation: str) -> bool:
    if len(tail) > MAX_TAIL_LEN:
        return True
    if len(tail) <= 1:
        return True
    for kw in SENTENCE_FRAGMENT_KEYWORDS:
        if kw in tail:
            return True
    if relation == "加工对象":
        if re.search(r"[。，；！？、]", tail):
            return True
        if tail.startswith(("但", "却", "而", "且", "并", "或", "与", "及")):
            return True
        if tail.endswith(("的", "了", "而", "但", "却", "即")):
            return True
        if re.match(r"^第[一二三四五六七八九十\d]+节$", tail):
            return True
    if re.match(r"^[\s\W_]+$", tail):
        return True
    return False


def is_bad_head(head: str) -> bool:
    if len(head) > 15:
        return True
    if len(head) <= 1:
        return True
    if re.search(r"[。，；！？、]", head):
        return True
    return False


def clean():
    print(f"加载: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    triples = data["triples"]
    print(f"原始三元组: {len(triples)} 条")

    removed = Counter()
    clean_list = []

    for t in triples:
        h, r, tl = t["head"], t["relation"], t["tail"]
        if is_bad_head(h):
            removed["bad_head"] += 1
            continue
        if is_bad_tail(tl, r):
            removed["bad_tail"] += 1
            continue
        clean_list.append(t)

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

    print(f"\n=== 清洗结果 ===")
    print(f"过滤 bad_head:       {removed['bad_head']} 条")
    print(f"过滤 bad_tail:       {removed['bad_tail']} 条")
    print(f"去重删除:             {dup_count} 条")
    print(f"---")
    print(f"清洗后三元组:         {len(dedup)} 条")
    print(f"实体数:              {len(entities_set)}")
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
    print("=== 清洗完成 ===")


if __name__ == "__main__":
    clean()
