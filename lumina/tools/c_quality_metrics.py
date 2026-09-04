"""C/CUDA 结构度量：文件/函数行数、循环、自递归、文档注释标志.

本模块只*测量*，不判违规；阈值与开关在 ``c_quality_gate`` + quality-gate.toml。
解析策略：轻量正则 + 花括号配对，避免强制依赖 compile_commands.json。
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from tools.c_doc_comments import has_file_banner, has_leading_doc_comment
from tools.c_loop_nesting import scan_loops
from tools.c_recursion import has_self_recursion
from tools.inline_comments import uncommented_complex_c_lines

_C_SUFFIXES = {".c", ".h", ".cu", ".cuh", ".cpp", ".hpp", ".cc"}
_CONTROL = frozenset({"if", "for", "while", "switch", "do"})
# 定义形态：限定词* 返回类型 名(...){ ；排除仅有分号的原型。
_FUNC_DEF = re.compile(
    r"(?:(?:__\w+|static|inline|extern|constexpr)\s+)*"
    r"[\w\s\*<>,:]+?\s+(\w+)\s*\([^;]*\)\s*\{"
)


@dataclass(frozen=True)
class CFunctionMetrics:
    """单函数：物理行数、循环嵌套/个数、自递归、前置文档、缺行内注释的复杂行数."""

    file_key: str
    name: str
    lines: int
    start_line: int
    loop_nesting: int
    loop_count: int
    has_recursion: bool
    has_doc_comment: bool
    uncommented_complex: int


@dataclass(frozen=True)
class CFileMetrics:
    """单文件：物理行数、函数个数、是否头文件、文件头 banner."""

    file_key: str
    path: str
    lines: int
    function_count: int
    is_header: bool
    has_file_banner: bool


def as_file_key(path: str | Path) -> str:
    """统一为正斜杠键，便于与 toml 里的 fnmatch 模式对齐."""
    return Path(path).as_posix()


def collect_c_files(roots: list[str], exclude_patterns: list[str]) -> list[Path]:
    """在 roots 下收集 C/CUDA 源，并应用排除模式."""
    found: list[Path] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for root in roots:
        found.extend(_collect_root(Path(root)))
    return sorted(
        {path for path in found if not any(fnmatch.fnmatch(as_file_key(path), pattern) for pattern in exclude_patterns)}
    )


def measure_c_files(
    paths: list[str],
    exclude_patterns: list[str],
    *,
    why_file_patterns: list[str] | None = None,
) -> tuple[list[CFileMetrics], list[CFunctionMetrics]]:
    """测量文件级与函数级结构指标.

    ``why_file_patterns`` 命中时对该文件启用 L4 why 语义（邻接注释须含 why 线索）.
    """
    files: list[CFileMetrics] = []
    functions: list[CFunctionMetrics] = []
    why_patterns = list(why_file_patterns or [])
    # 单遍：逐文件测量，避免跨文件状态污染指标。
    for path in collect_c_files(paths, exclude_patterns):
        file_key = as_file_key(path)
        require_why = bool(why_patterns) and (
            any(pat in {"**", "**/*", "*"} for pat in why_patterns)
            or any(fnmatch.fnmatch(file_key, pat) for pat in why_patterns)
        )
        file_metrics, func_metrics = _measure_one(path, require_why=require_why)
        files.append(file_metrics)
        functions.extend(func_metrics)
    return files, functions


def _collect_root(base: Path) -> list[Path]:
    """单个 root：文件则按后缀过滤；目录则递归."""
    if base.is_file() and base.suffix in _C_SUFFIXES:
        return [base]
    if not base.is_dir():
        return []
    return [path for path in base.rglob("*") if path.is_file() and path.suffix in _C_SUFFIXES]


def _measure_one(path: Path, *, require_why: bool = False) -> tuple[CFileMetrics, list[CFunctionMetrics]]:
    """读入单文件，切函数 span 后挂上循环/递归/文档标志."""
    raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    file_key = as_file_key(path)
    spans = function_spans(raw_lines)
    file_metrics = CFileMetrics(
        file_key=file_key,
        path=str(path),
        lines=_count_physical(raw_lines),
        function_count=len(spans),
        is_header=path.suffix in {".h", ".cuh", ".hpp"},
        has_file_banner=has_file_banner(raw_lines),
    )
    functions: list[CFunctionMetrics] = []
    # 单遍：span 互不重叠，避免嵌套静态函数重复计量。
    for name, start, end in spans:
        body = raw_lines[start - 1 : end]
        nesting, count = scan_loops(body)
        functions.append(
            CFunctionMetrics(
                file_key=file_key,
                name=name,
                lines=_count_physical(body),
                start_line=start,
                loop_nesting=nesting,
                loop_count=count,
                has_recursion=has_self_recursion(name, body),
                has_doc_comment=has_leading_doc_comment(raw_lines, start),
                uncommented_complex=len(uncommented_complex_c_lines(body, require_why=require_why)),
            )
        )
    return file_metrics, functions


def _count_physical(lines: list[str]) -> int:
    """统计计入门禁的物理行（空行/整行注释不计）."""
    return sum(1 for line in lines if _is_physical(line.strip()))


def _is_physical(stripped: str) -> bool:
    """是否计入行数：排除空行、``//``、单行 ``/* ... */``."""
    return (
        bool(stripped) and not stripped.startswith("//") and not (stripped.startswith("/*") and stripped.endswith("*/"))
    )


def function_spans(lines: list[str]) -> list[tuple[str, int, int]]:
    """用花括号配对切出 ``(name, start_line, end_line)``（1-based，含端点）."""
    spans: list[tuple[str, int, int]] = []
    index = 0
    # 单遍：跳过注释/预处理后定位定义，避免嵌套静态函数重复计数。
    while index < len(lines):
        if _skip_line(lines[index].strip()):
            index += 1
            continue
        name = _definition_name_at(lines, index)
        brace_line = _opening_brace_line(lines, index) if name else None
        end = _match_braces(lines, brace_line) if brace_line is not None else None
        if name is None or brace_line is None or end is None:
            index += 1
            continue
        spans.append((name, index + 1, end + 1))
        # 跳到函数结束后，避免嵌套静态函数被外层重复扫描（少见但安全）。
        index = end + 1
    return spans


def _skip_line(stripped: str) -> bool:
    """跳过空白、预处理、注释行.

    块注释续行常以 ``*`` 开头；若不跳过，散文 ``O(n)`` 会在窗口碰到 ``{`` 时
    被 ``_FUNC_DEF`` 误认为函数 ``O``。
    """
    return (
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped == "*/"
        or stripped.startswith("*")
    )


def _definition_name_at(lines: list[str], start: int) -> str | None:
    """若 ``start`` 起是函数定义（非原型），返回函数名."""
    window: list[str] = []
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for index in range(start, min(start + 12, len(lines))):
        window.append(lines[index].rstrip())
        joined = " ".join(part.strip() for part in window)
        # 仅有分号、无花括号 → 原型，交给头文件文档检查。
        if ";" in joined and "{" not in joined:
            return None
        if "{" not in joined:
            continue
        match = _FUNC_DEF.search(joined)
        if match is None:
            return None
        name = match.group(1)
        # C++ 初始化列表 ``Foo() : p_(0) {`` 可能把 ``p_`` 当成名；控制关键字直接丢掉。
        return None if name in _CONTROL else name
    return None


def _opening_brace_line(lines: list[str], start: int) -> int | None:
    """定义起始行起找首个 ``{``；途中先遇 ``;`` 则不是定义."""
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for index in range(start, min(start + 12, len(lines))):
        if "{" in lines[index]:
            return index
        if ";" in lines[index]:
            return None
    return None


def _match_braces(lines: list[str], start: int) -> int | None:
    """从 ``start`` 行的首个 ``{`` 配对到同深度 ``}``，返回结束行下标."""
    depth = 0
    started = False
    # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
    for index in range(start, len(lines)):
        # 单遍扫描：边界由调用方/前置校验保证，避免越界与重复读。
        for char in lines[index]:
            if char == "{":
                depth += 1
                started = True
            elif char == "}":
                depth -= 1
                if started and depth == 0:
                    return index
    return None
