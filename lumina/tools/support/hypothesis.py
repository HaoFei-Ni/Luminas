"""Map quality-gate.toml hypothesis profiles into Hypothesis settings kwargs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def profile_settings_kwargs(
    raw: dict[str, Any],
    *,
    database_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Translate one ``[hypothesis.profiles.*]`` table into ``settings`` kwargs.

    ``derandomize=True`` forces ``database=None`` (Hypothesis rule); persistence is
    skipped when derandomize is on so seeds stay the single reproducibility source.
    """
    out: dict[str, Any] = {
        "max_examples": int(raw["max_examples"]),
        "deadline": int(raw["deadline_ms"]),
        "print_blob": bool(raw.get("print_blob", True)),
    }
    _apply_reproducibility(out, raw, database_factory)
    if "stateful_step_count" in raw:
        out["stateful_step_count"] = int(raw["stateful_step_count"])
    if "suppress_health_check" in raw and not raw["suppress_health_check"]:
        out["suppress_health_check"] = ()
    return out


def _apply_reproducibility(
    out: dict[str, Any],
    raw: dict[str, Any],
    database_factory: Callable[[], Any] | None,
) -> None:
    """Attach derandomize or example database kwargs when the profile enables them."""
    if bool(raw.get("derandomize")):
        out["derandomize"] = True
        return
    if raw.get("persist_examples") and database_factory is not None:
        out["database"] = database_factory()
