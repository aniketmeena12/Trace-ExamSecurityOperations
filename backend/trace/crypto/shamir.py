"""Shamir's Secret Sharing over GF(256), implemented from scratch.

A secret of arbitrary byte length is split byte-by-byte. For each byte we build
a random polynomial of degree (threshold - 1) whose constant term is that secret
byte, then evaluate it at distinct nonzero x-coordinates 1..n. Each custodian
receives one share: their x-coordinate plus one field element (y value) per
secret byte.

Recovery: any `threshold` custodians interpolate the polynomial (Lagrange) and
read off its value at x = 0, which is the secret byte. Fewer than `threshold`
shares leave the constant term information-theoretically undetermined — every
possible secret remains equally consistent with the shares they hold.

In Trace, the secret being split is the AES-256 key that encrypts an exam paper.
3-of-5 means no single custodian (and no pair) can ever reconstruct the key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from . import gf256


@dataclass(frozen=True)
class Share:
    """One custodian's share: an x-coordinate and one y value per secret byte."""

    x: int      # custodian index, 1..255 (must be nonzero)
    y: bytes    # f(x) for each byte of the secret

    def to_hex(self) -> str:
        """Serialize as ``xx:hexhex...`` for transport / storage."""
        return f"{self.x:02x}:{self.y.hex()}"

    @classmethod
    def from_hex(cls, s: str) -> "Share":
        x_part, y_part = s.split(":")
        return cls(int(x_part, 16), bytes.fromhex(y_part))


def _eval_poly(coeffs: list[int], x: int) -> int:
    """Evaluate a polynomial at x in GF(256) using Horner's method.

    ``coeffs[0]`` is the constant term (the secret byte).
    """
    acc = 0
    for c in reversed(coeffs):
        acc = gf256.add(gf256.mul(acc, x), c)
    return acc


def split(secret: bytes, n: int, k: int) -> list[Share]:
    """Split ``secret`` into ``n`` shares, any ``k`` of which can reconstruct it.

    Raises ValueError on invalid parameters. Coefficients are drawn from a
    cryptographically secure source (os.urandom).
    """
    if not (1 <= k <= n <= 255):
        raise ValueError("require 1 <= k <= n <= 255")
    if len(secret) == 0:
        raise ValueError("secret must be non-empty")

    xs = list(range(1, n + 1))
    ys = [bytearray() for _ in range(n)]

    for secret_byte in secret:
        # Degree k-1 polynomial: constant term is the secret byte, the other
        # k-1 coefficients are random. This is what makes < k shares useless.
        coeffs = [secret_byte] + list(os.urandom(k - 1))
        for i, x in enumerate(xs):
            ys[i].append(_eval_poly(coeffs, x))

    return [Share(x, bytes(y)) for x, y in zip(xs, ys)]


def combine(shares: list[Share]) -> bytes:
    """Reconstruct the secret from a list of shares.

    Needs at least ``threshold`` shares with distinct x-coordinates to return
    the true secret; with fewer it returns a different (wrong) value, never the
    real secret. Shares must all be the same length.
    """
    if len(shares) == 0:
        raise ValueError("need at least one share")

    xs = [s.x for s in shares]
    if 0 in xs:
        raise ValueError("share x-coordinate 0 is invalid")
    if len(set(xs)) != len(xs):
        raise ValueError("shares must have distinct x-coordinates")

    length = len(shares[0].y)
    if any(len(s.y) != length for s in shares):
        raise ValueError("all shares must have equal length")

    secret = bytearray()
    for byte_idx in range(length):
        ys = [s.y[byte_idx] for s in shares]
        secret.append(_lagrange_at_zero(xs, ys))
    return bytes(secret)


def _lagrange_at_zero(xs: list[int], ys: list[int]) -> int:
    """Lagrange-interpolate points (xs, ys) and evaluate the result at x = 0.

    The value at 0 is the polynomial's constant term — the secret byte.
    """
    secret = 0
    for j in range(len(xs)):
        numerator = 1
        denominator = 1
        for m in range(len(xs)):
            if m == j:
                continue
            # Basis term at x=0: product of (0 - x_m) / (x_j - x_m).
            # In GF(256), negation is identity, so (0 - x_m) == x_m and
            # (x_j - x_m) == x_j XOR x_m.
            numerator = gf256.mul(numerator, xs[m])
            denominator = gf256.mul(denominator, gf256.add(xs[j], xs[m]))
        basis = gf256.div(numerator, denominator)
        secret = gf256.add(secret, gf256.mul(ys[j], basis))
    return secret
