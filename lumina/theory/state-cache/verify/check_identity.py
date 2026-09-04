"""P1/P2 脚手架：在当前恒等 Enc/Dec 上检查 2-ulp 门。

不是闭合框架的证明。luma_kv_cpu.c 换成真公式后应继续用本门限；
正式 CI 以 lumina/kernel/test/test_luma_kv.c 为准。
"""

from __future__ import annotations

import math

ULP32 = 2.0**-23


def within_2ulp(x: float, ref: float) -> bool:
    # P2
    return abs(x - ref) <= 2.0 * ULP32 * max(1.0, abs(ref))


def identity_enc(s: list[float]) -> tuple[list[float], int]:
    # P1 占位：Enc = Id，压缩域长度恒等于原长。
    if any(not math.isfinite(v) for v in s):
        raise ValueError("P5: non-finite input")
    return list(s), len(s)


def identity_dec(enc: list[float], n: int) -> list[float]:
    if len(enc) != n:
        raise ValueError("P1: enc_len must equal n for identity")
    return list(enc)


def main() -> None:
    s = [1.0, -2.5, 0.0, math.pi, 1e-3]
    enc, enc_len = identity_enc(s)
    hat = identity_dec(enc, len(s))
    assert enc_len == len(s)
    assert all(within_2ulp(a, b) for a, b in zip(hat, s)), "P2 failed"
    print("P1/P2 identity scaffold OK")


if __name__ == "__main__":
    main()
