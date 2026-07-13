import re

# 读取原始文本
with open("/mnt/workspace/Taki/船体.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

# 1. 去噪：删除多余空行、页码、乱码
clean_text = re.sub(r'\n+', '\n', raw_text)  # 合并空行
clean_text = re.sub(r'第\d+页/\d+页', '', clean_text)  # 删除页码
clean_text = re.sub(r'[^\u4e00-\u9fa50-9a-zA-Z，。、；：？！（）《》\n]', '', clean_text)  # 保留中文/数字/字母/常用标点

# 2. 分段：按章节拆分，方便模型精准抽取
sections = re.split(r'第[一二三四五六七八九十]+章', clean_text)
processed_sections = [sec.strip() for sec in sections if sec.strip()]

# 3. 保存清洗后的文本
with open("/mnt/workspace/Taki/船体_清洗后.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(processed_sections))

print(f"✅ 语料预处理完成！原始长度：{len(raw_text)}，清洗后长度：{len(clean_text)}")
print(f"共拆分{len(processed_sections)}个章节，可用于分段抽取")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import json

model_path = "/opt/pangu/openPangu-Embedded-7B-V1.1"
def load_pangu_model():
    if not os.path.exists(model_path):
        print(f"模型路径不存在: {model_path}")
        return None, None

    print("正在加载tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )

    print("正在加载模型...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="npu",
        trust_remote_code=True
    )
    print("✅ 模型加载完成！")
    return model, tokenizer
model, tokenizer = load_pangu_model()

with open("/mnt/workspace/Taki/船体_清洗后.txt", "r", encoding="utf-8") as f:
    full_text = f.read()

print(f"✅ 全本语料加载完成！总长度：{len(full_text)} 字符")

def split_text(text, chunk_size=500, overlap=50):
    """将长文本切分成带重叠的小块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # 重叠避免截断实体
    return chunks

chunks = split_text(full_text, chunk_size=500, overlap=50)
print(f"✅ 文本分块完成！共 {len(chunks)} 个片段")