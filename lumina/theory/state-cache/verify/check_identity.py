"""遗留脚手架：旧状态缓存稿的 P1/P2 恒等 Enc/Dec + 2-ulp 检查。

本目录权威判据已切换为 F1–F7（见 verify-degeneration.py 与 ../framework.md）。
勿把本脚本的通过当作表征坍缩框架的核验结果。
正式 CI 中与 KV 编解码相关的门仍以 lumina/tests/c/test_luma_kv.c 为准。
"""

from __future__ import annotations

import math

ULP32 = 2.0**-23


def within_2ulp(x: float, ref: float) -> bool:
    return abs(x - ref) <= 2.0 * ULP32 * max(1.0, abs(ref))


def identity_enc(s: list[float]) -> tuple[list[float], int]:
    if any(not math.isfinite(v) for v in s):
        raise ValueError("non-finite input")
    return list(s), len(s)


def identity_dec(enc: list[float], n: int) -> list[float]:
    if len(enc) != n:
        raise ValueError("enc_len must equal n for identity")
    return list(enc)


def main() -> None:
    s = [1.0, -2.5, 0.0, math.pi, 1e-3]
    enc, enc_len = identity_enc(s)
    hat = identity_dec(enc, len(s))
    assert enc_len == len(s)
    assert all(within_2ulp(a, b) for a, b in zip(hat, s, strict=True))
    print("legacy identity scaffold OK (not F1–F7)")


if __name__ == "__main__":
    main()
