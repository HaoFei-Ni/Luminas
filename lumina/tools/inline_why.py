"""L4 why-comment heuristics for complex-statement inline notes."""

from __future__ import annotations

import re

_WHY_MARKERS = re.compile(
    r"不变量|精度|边界|为何|不能改|同步|溢出|除零|有限|收敛|稳定|避免|必须|防止|须|"
    r"别名|冲突|容差|重标定|镜像|奇异|发散|旋转|共享|可见|一致|门禁|防护|"
    r"截断|饱和|量化|尾数|指数|归一|归约|读前|写完|有限性|隐含|前导|定点|格点|"
    r"幂|对照|校验|越界|正交|对称|上三角|能量|排序|投影|stride|"
    r"invariant|precision|bound|overflow|underflow|finite|sync|barrier|race|"
    r"alias|guard|must|avoid|why|eps|ulp|nan|inf|shared|stabiliz|converg|"
    r"singular|mantissa|exponent|before|after|∈|≡|⌊|区间|范围",
    re.IGNORECASE,
)

_WHAT_BLACKLIST = re.compile(
    r"单层遍历|退出/边界见|退出／边界见|遍历数组|遍历列表|loop over|iterate over|"
    r"for each|单遍归约|^遍历\b|^循环\b",
    re.IGNORECASE,
)

_COMMENT_STRIP = re.compile(r"^/\*+|\*+/$|^//+|^#+|\*/$")
_MIN_WHY_LEN = 2


def is_why_comment(text: str) -> bool:
    """Return True when comment text looks like a why-note (L4 heuristic)."""
    cleaned = _normalize_comment(text)
    if len(cleaned) < _MIN_WHY_LEN:
        return False
    if _WHAT_BLACKLIST.search(cleaned):
        return False
    return _WHY_MARKERS.search(cleaned) is not None


def _normalize_comment(text: str) -> str:
    """Strip comment delimiters and collapse whitespace."""
    cleaned = text.strip()
    cleaned = _COMMENT_STRIP.sub("", cleaned).strip()
    cleaned = cleaned.strip("*").strip()
    return re.sub(r"\s+", " ", cleaned)
