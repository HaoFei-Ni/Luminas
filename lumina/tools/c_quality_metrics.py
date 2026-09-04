"""C/CUDA 结构度量：文件/函数行数、循环、自递归、文档注释标志.

本模块只*测量*，不判违规；阈值与开关在 ``c_quality_gate`` + quality-gate.toml。
解析策略：轻量正则 + 花括号配对，避免强制依赖 compile_commands.json。
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from tools.c_doc_comments import has_file_banner, has_leading_doc_comment
from tools.c_function_spans import function_spans
from tools.c_loop_nesting import scan_loops
from tools.c_recursion import has_self_recursion
from tools.inline_comments import uncommented_complex_c_lines

__all__ = [
    "CFileMetrics",
    "CFunctionMetrics",
    "as_file_key",
    "collect_c_files",
    "function_spans",
    "measure_c_files",
]

_C_SUFFIXES = {".c", ".h", ".cu", ".cuh", ".cpp", ".hpp", ".cc"}


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
    """测量文件级与函数级结构指标."""
    files: list[CFileMetrics] = []
    functions: list[CFunctionMetrics] = []
    why_patterns = list(why_file_patterns or [])
    # 单遍：逐文件测量，避免跨文件状态污染指标。
    for path in collect_c_files(paths, exclude_patterns):
        file_key = as_file_key(path)
        require_why = _require_why(file_key, why_patterns)
        file_metrics, func_metrics = _measure_one(path, require_why=require_why)
        files.append(file_metrics)
        functions.extend(func_metrics)
    return files, functions


def _require_why(file_key: str, why_patterns: list[str]) -> bool:
    """True when L4 why patterns apply to this file key."""
    if not why_patterns:
        return False
    if any(pat in {"**", "**/*", "*"} for pat in why_patterns):
        return True
    return any(fnmatch.fnmatch(file_key, pat) for pat in why_patterns)


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
    functions = [_function_metric(file_key, raw_lines, name, start, end, require_why) for name, start, end in spans]
    return file_metrics, functions


def _function_metric(
    file_key: str,
    raw_lines: list[str],
    name: str,
    start: int,
    end: int,
    require_why: bool,
) -> CFunctionMetrics:
    """Build metrics for one function span."""
    body = raw_lines[start - 1 : end]
    nesting, count = scan_loops(body)
    return CFunctionMetrics(
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


def _count_physical(lines: list[str]) -> int:
    """统计计入门禁的物理行（空行/整行注释不计）."""
    total = 0
    # 单遍：空行与整行注释不计物理行，避免虚高门禁行数。
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if stripped.startswith("/*") and stripped.endswith("*/"):
            continue
        total += 1
    return total
