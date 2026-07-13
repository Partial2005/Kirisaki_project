# ============================================================
# Cell 1: 三元组清洗脚本
# 输入: triples_final.json
# 输出: triples_clean.json + 统计报告
# ============================================================
import json
import re
from collections import Counter

# 加载原始三元组
with open("triples_final.json", "r", encoding="utf-8") as f:
    data = json.load(f)

triples = data["triples"]
print(f"原始三元组数量: {len(triples)}")

# ---------- 过滤规则 ----------
# 1. 尾实体过长 (>20字) —— 基本是书名字符串或完整句子
MAX_TAIL_LEN = 20

# 2. 尾实体包含这些词的 → 是句子碎片，删除
SENTENCE_FRAGMENT_KEYWORDS = [
    "也可用作", "由于", "习惯上", "从而导致", "从而导致",
    "停靠码头", "坞内涂装", "船舶停靠", "喷涂底",
    "但未最后", "却也加大", "大型分段虽减少",
    "前后或左右相邻", "火工矫正及机械原因",
    "分段和船台上都已预先", "从底部分段上中心线",
    "悬线锤至", "用卷尺里得",
    "预合拢的犬分段",  # OCR 错误
    "分段大接缝的壳板",
    "小合拢阶段中合拢阶段",  # 拼接错误
]


def is_bad_tail(tail, relation):
    """判断尾实体是否应该过滤"""
    # 过长
    if len(tail) > MAX_TAIL_LEN:
        return True

    # 包含句子碎片关键词
    for kw in SENTENCE_FRAGMENT_KEYWORDS:
        if kw in tail:
            return True

    # 尾实体只有1个字（噪声）
    if len(tail) <= 1:
        return True

    # 针对"加工对象"的额外过滤
    if relation == "加工对象":
        # 包含句末标点 → 句子碎片
        if re.search(r"[。，；！？、]", tail):
            return True
        # 以虚词开头/结尾
        if tail.startswith(("但", "却", "而", "且", "并", "或", "与", "及")):
            return True
        if tail.endswith(("的", "了", "而", "但", "却", "即")):
            return True
        # 纯"第X节"无实际内容
        if re.match(r"^第[一二三四五六七八九十\d]+节$", tail):
            return True

    # 纯标点或空白
    if re.match(r"^[\s\W_]+$", tail):
        return True

    return False


def is_bad_head(head):
    """判断头实体是否应该过滤"""
    if len(head) > 15:
        return True
    if len(head) <= 1:
        return True
    if re.search(r"[。，；！？、]", head):
        return True
    return False


# ---------- 执行过滤 ----------
clean_triples = []
removed_reasons = Counter()

for t in triples:
    head, rel, tail = t["head"], t["relation"], t["tail"]

    if is_bad_head(head):
        removed_reasons["bad_head"] += 1
        continue

    if is_bad_tail(tail, rel):
        removed_reasons["bad_tail"] += 1
        continue

    clean_triples.append(t)

# 去重
seen = set()
dedup_triples = []
for t in clean_triples:
    key = (t["head"], t["relation"], t["tail"])
    if key not in seen:
        seen.add(key)
        dedup_triples.append(t)

dup_count = len(clean_triples) - len(dedup_triples)

# ---------- 统计 ----------
entities_set = set()
rel_counter = Counter()
for t in dedup_triples:
    entities_set.add(t["head"])
    entities_set.add(t["tail"])
    rel_counter[t["relation"]] += 1

print(f"\n=== 清洗结果 ===")
print(f"清洗前: {len(triples)} 条三元组")
print(f"过滤 bad_head: {removed_reasons['bad_head']} 条")
print(f"过滤 bad_tail: {removed_reasons['bad_tail']} 条")
print(f"去重删除: {dup_count} 条")
print(f"清洗后: {len(dedup_triples)} 条三元组")
print(f"实体数: {len(entities_set)}")
print(f"\n关系分布:")
for rel, cnt in rel_counter.most_common():
    print(f"  {rel}: {cnt}")

# ---------- 保存 ----------
output = {
    "total": len(dedup_triples),
    "entities": len(entities_set),
    "relation_distribution": dict(rel_counter),
    "triples": dedup_triples,
}

with open("triples_clean.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 triples_clean.json")
print("=== 清洗完成 ===")
