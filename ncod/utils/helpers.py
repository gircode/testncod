import re
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


def generate_id() -> str:
    """生成唯一ID

    Returns:
        str: 唯一ID
    """
    return str(uuid.uuid4())


def to_camel(string: str) -> str:
    """转换为驼峰命名

    Args:
        string: 输入字符串

    Returns:
        str: 驼峰命名字符串
    """
    string = string.replace("-", " ").replace("_", " ")
    return "".join(word.capitalize() for word in string.split())


def to_snake(string: str) -> str:
    """转换为蛇形命名

    Args:
        string: 输入字符串

    Returns:
        str: 蛇形命名字符串
    """
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", string).lower()


def to_kebab(string: str) -> str:
    """转换为短横线命名

    Args:
        string: 输入字符串

    Returns:
        str: 短横线命名字符串
    """
    return to_snake(string).replace("_", "-")


def utc_now() -> datetime:
    """获取当前UTC时间

    Returns:
        datetime: 当前UTC时间
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime) -> str:
    """格式化日期时间

    Args:
        dt: 日期时间

    Returns:
        str: 格式化后的字符串
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(string: str) -> Optional[datetime]:
    """解析日期时间字符串

    Args:
        string: 日期时间字符串

    Returns:
        Optional[datetime]: 解析后的日期时间
    """
    try:
        return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def filter_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """过滤字典

    Args:
        data: 原始字典
        keys: 要保留的键列表

    Returns:
        Dict[str, Any]: 过滤后的字典
    """
    return {k: v for k, v in data.items() if k in keys}


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """合并字典

    Args:
        *dicts: 要合并的字典

    Returns:
        Dict[str, Any]: 合并后的字典
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    """分割列表

    Args:
        lst: 要分割的列表
        size: 分割大小

    Returns:
        List[List[Any]]: 分割后的列表
    """
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def flatten_list(lst: List[Any]) -> List[Any]:
    """扁平化列表

    Args:
        lst: 要扁平化的列表

    Returns:
        List[Any]: 扁平化后的列表
    """
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result
