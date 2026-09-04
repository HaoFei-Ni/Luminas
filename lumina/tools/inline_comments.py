"""复杂语句行内注释检测（C/Python 共用启发式）.

LUM-ENG-101 §8：循环、同步点、关键数值原语行须有贴身 why 注释。
本模块只报告「缺注释 / why 不合格的复杂行」；是否判失败由门禁开关决定。

档位：
- L0（默认）：复杂行邻接有 ``//`` / ``#`` / 块注释即通过。
- L4（``require_why=True``）：邻接注释须命中 why 线索，且不得是 what 模板句。
"""

from __future__ import annotations

import re

# C/CUDA：循环、同步、原子、共享内存、数值不稳定点（L2 扩模式）。
_C_COMPLEX = re.compile(
    r"\b(for|while|do)\b"
    r"|__syncthreads\b"
    r"|__shared__\b"
    r"|atomic(?:Add|Exch|CAS|Max|Min)\b"
    r"|\bfrexpf?\s*\("
    r"|\bldexpf?\s*\("
    r"|exp2f\s*\("
    r"|floorf\s*\(\s*log2"
)

# Python：仅循环头（与 AST For/While 互补；字符串扫描用于无 AST 的片段）。
_PY_COMPLEX = re.compile(r"^\s*(async\s+)?(for|while)\b")

# L4 why 线索：不变量 / 精度 / 边界 / 同步 / 溢出防护等（中英）。
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

# L4 what / 模板黑名单：命中则即使有字也不算 why。
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


def uncommented_complex_c_lines(body_lines: list[str], *, require_why: bool = False) -> list[int]:
    """返回函数体内缺行内注释（或 why 不合格）的复杂语句行号（1-based）."""
    return _uncommented(body_lines, _C_COMPLEX, c_style=True, require_why=require_why)


def uncommented_complex_py_lines(body_lines: list[str], *, require_why: bool = False) -> list[int]:
    """返回 Python 片段中缺 ``#``（或 why 不合格）的循环行号（1-based）."""
    return _uncommented(body_lines, _PY_COMPLEX, c_style=False, require_why=require_why)


def _normalize_comment(text: str) -> str:
    """Strip comment delimiters and collapse whitespace."""
    cleaned = text.strip()
    cleaned = _COMMENT_STRIP.sub("", cleaned).strip()
    cleaned = cleaned.strip("*").strip()
    return re.sub(r"\s+", " ", cleaned)


def _uncommented(
    body_lines: list[str],
    pattern: re.Pattern[str],
    *,
    c_style: bool,
    require_why: bool,
) -> list[int]:
    """扫描 body，收集匹配 pattern 且邻接注释不足（或 why 不合格）的行号."""
    missing: list[int] = []
    # 单遍：复杂行集合有限，按行扫描即可。
    for index, raw in enumerate(body_lines):
        stripped = raw.strip()
        if not stripped or _is_comment_only(stripped, c_style) or stripped in {"{", "}", "};"}:
            continue
        if stripped.startswith("#") and c_style:
            continue  # C 预处理
        code = _strip_strings(_code_part(raw, c_style))
        if not pattern.search(code):
            continue
        note = _adjacent_comment_text(body_lines, index, c_style)
        if note is None:
            missing.append(index + 1)
            continue
        if require_why and not is_why_comment(note):
            missing.append(index + 1)
    return missing


def _code_part(line: str, c_style: bool) -> str:
    """去掉行尾注释后的代码部分，避免注释正文触发复杂模式."""
    if c_style:
        if "//" in line:
            return line[: line.index("//")]
        return line
    if "#" in line:
        return line[: line.index("#")]
    return line


def _strip_strings(code: str) -> str:
    r"""Strip double-quoted strings so ``"... for ..."`` does not fake a loop."""
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', code)


def _is_comment_only(stripped: str, c_style: bool) -> bool:
    """整行是否为注释."""
    if c_style:
        return stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or stripped == "*/"
    return stripped.startswith("#")


def _adjacent_comment_text(lines: list[str], index: int, c_style: bool) -> str | None:
    """同行尾注释，或紧邻上一非空注释行的正文；无则 None."""
    raw = lines[index]
    inline = _inline_comment_text(raw, c_style)
    if inline is not None:
        return inline
    prev = index - 1
    # 跳过空行：贴身注释允许与代码之间有空行，避免误杀格式化结果。
    while prev >= 0 and not lines[prev].strip():
        prev -= 1
    if prev < 0:
        return None
    prev_stripped = lines[prev].strip()
    if not _is_comment_only(prev_stripped, c_style):
        return None
    return prev_stripped


def _inline_comment_text(raw: str, c_style: bool) -> str | None:
    """Extract trailing comment on a code line, if any."""
    if c_style:
        if "//" in raw:
            return raw[raw.index("//") :]
        if "/*" in raw:
            start = raw.index("/*")
            end = raw.find("*/", start)
            if end >= 0:
                return raw[start : end + 2]
        return None
    if "#" not in raw:
        return None
    code = raw[: raw.index("#")].strip()
    if not code:
        return None
    return raw[raw.index("#") :]
