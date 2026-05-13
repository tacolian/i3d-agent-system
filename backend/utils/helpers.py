"""
辅助工具函数
"""
import re
import string
import secrets
from typing import Optional


def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    生成随机ID

    Args:
        prefix: ID前缀
        length: 随机部分长度

    Returns:
        生成的ID
    """
    random_part = secrets.token_hex(length)
    return f"{prefix}_{random_part}" if prefix else random_part


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    清理用户输入

    Args:
        text: 输入文本
        max_length: 最大长度

    Returns:
        清理后的文本
    """
    # 移除控制字符
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    # 截断
    text = truncate_text(text, max_length, "")

    # 去除首尾空白
    text = text.strip()

    return text


def extract_keywords(text: str, min_length: int = 2) -> list[str]:
    """
    提取关键词

    Args:
        text: 输入文本
        min_length: 最小关键词长度

    Returns:
        关键词列表
    """
    # 移除标点符号
    text = text.translate(str.maketrans("", "", string.punctuation))

    # 分词
    words = text.lower().split()

    # 过滤短词和常见停用词
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
    keywords = [
        w for w in words
        if len(w) >= min_length and w not in stopwords
    ]

    return keywords


def format_duration(ms: float) -> str:
    """
    格式化时间 duration

    Args:
        ms: 毫秒数

    Returns:
        格式化的字符串
    """
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        minutes = int(ms // 60000)
        seconds = int((ms % 60000) // 1000)
        return f"{minutes}m {seconds}s"


def safe_json_parse(text: str, default: Optional[dict] = None) -> Optional[dict]:
    """
    安全地解析JSON

    Args:
        text: JSON字符串
        default: 解析失败时的默认值

    Returns:
        解析结果或默认值
    """
    import json

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
