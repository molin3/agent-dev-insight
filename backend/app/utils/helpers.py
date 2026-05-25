"""通用工具函数"""

import json
import re
import uuid
from typing import Any


def gen_uuid() -> str:
    """生成 UUID4 字符串"""
    return str(uuid.uuid4())


def parse_json_from_text(text: str) -> dict[str, Any]:
    """从文本中提取 JSON 对象

    处理三种情况：直接JSON / markdown代码块 / 裸花括号代码
    """
    # 1. 先检查 markdown 代码块 ```json ... ```
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if md_match:
        candidate = md_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 2. 查找裸花括号
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def safe_truncate(text: str, max_len: int = 5000) -> str:
    """安全截断文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
