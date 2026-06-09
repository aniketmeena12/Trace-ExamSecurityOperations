"""Invisible DCT-domain watermarking (Koch-Zhao style differential embedding).

Why this scheme survives JPEG (the required robustness property):

  * We embed on the luminance (Y) channel, which is exactly what JPEG keeps at
    highest fidelity.
  * Each bit is encoded as the *sign of the difference* between two mid-band DCT
    coefficients in an 8x8 block. JPEG quantizes neighbouring mid-band
    coefficients with similar step sizes, so their relative order is preserved
    far better than any single coefficient's value.
  * Every payload bit is interleaved across hundreds of blocks; extraction
    soft-combines the per-block differences (sum, then take the sign). A few
    blocks zeroed by JPEG cannot flip the aggregate.

Payload layout (PAYLOAD_BITS total):
    [ 16-bit MAGIC ][ 64-bit fingerprint ]
The magic acts as a presence/sync check; the fingerprint identifies the exact
issued copy (center + candidate) via the tracing registry.
"""

from __future__ import annotations

import hashlib

import cv2
import numpy as np
from PIL import Image

BLOCK = 8
# Mid-band coefficient pair. Symmetric positions with similar JPEG quant steps,
# low enough in frequency to survive recompression, high enough to stay invisible.
P1 = (2, 3)
P2 = (3, 2)

# 16-bit synchronization magic (0xACE5).
MAGIC = [int(b) for b in format(0xACE5, "016b")]
FINGERPRINT_BITS = 64
PAYLOAD_BITS = len(MAGIC) + FINGERPRINT_BITS  # 80

DEFAULT_GAP = 26.0  # coefficient separation enforced per block


# --------------------------------------------------------------------------
# bit helpers
# --------------------------------------------------------------------------
def int_to_bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def bits_to_int(bits: list[int]) -> int:
    out = 0
    for b in bits:
        out = (out << 1) | (b & 1)
    return out


def hamming(a: list[int], b: list[int]) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def make_fingerprint(center_id: str, candidate_id: str) -> int:
    """Deterministic 64-bit fingerprint for an issued copy."""
    digest = hashlib.blake2b(
        f"{center_id}|{candidate_id}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big")


# --------------------------------------------------------------------------
# channel <-> array
# --------------------------------------------------------------------------
def _split_y(img: Image.Image):
    y, cb, cr = img.convert("YCbCr").split()
    return np.asarray(y, dtype=np.float32), cb, cr


def _merge_y(y: np.ndarray, cb, cr) -> Image.Image:
    y_img = Image.fromarray(np.clip(y, 0, 255).astype(np.uint8), mode="L")
    return Image.merge("YCbCr", (y_img, cb, cr)).convert("RGB")


# --------------------------------------------------------------------------
# embed / extract on a luminance array
# --------------------------------------------------------------------------
def _embed_bits(y: np.ndarray, bits: list[int], gap: float) -> np.ndarray:
    h, w = y.shape
    H, W = h - h % BLOCK, w - w % BLOCK
    n = len(bits)
    idx = 0
    for by in range(0, H, BLOCK):
        for bx in range(0, W, BLOCK):
            bit = bits[idx % n]
            block = y[by : by + BLOCK, bx : bx + BLOCK]
            d = cv2.dct(block)
            c1, c2 = float(d[P1]), float(d[P2])
            if bit == 1:
                if c1 - c2 < gap:
                    mid = (c1 + c2) / 2.0
                    d[P1], d[P2] = mid + gap / 2.0, mid - gap / 2.0
            else:
                if c2 - c1 < gap:
                    mid = (c1 + c2) / 2.0
                    d[P2], d[P1] = mid + gap / 2.0, mid - gap / 2.0
            y[by : by + BLOCK, bx : bx + BLOCK] = cv2.idct(d)
            idx += 1
    return y


def _extract_bits(y: np.ndarray, n_bits: int) -> list[int]:
    h, w = y.shape
    H, W = h - h % BLOCK, w - w % BLOCK
    acc = np.zeros(n_bits, dtype=np.float64)
    idx = 0
    for by in range(0, H, BLOCK):
        for bx in range(0, W, BLOCK):
            block = np.ascontiguousarray(
                y[by : by + BLOCK, bx : bx + BLOCK], dtype=np.float32
            )
            d = cv2.dct(block)
            acc[idx % n_bits] += float(d[P1]) - float(d[P2])
            idx += 1
    # Soft decision: sign of the aggregated coefficient difference.
    return [1 if acc[i] > 0 else 0 for i in range(n_bits)]


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------
def embed_fingerprint(img: Image.Image, fingerprint: int, gap: float = DEFAULT_GAP) -> Image.Image:
    """Return a copy of `img` carrying MAGIC + the 64-bit fingerprint."""
    if fingerprint < 0 or fingerprint >= (1 << FINGERPRINT_BITS):
        raise ValueError("fingerprint must fit in 64 bits")
    bits = MAGIC + int_to_bits(fingerprint, FINGERPRINT_BITS)
    y, cb, cr = _split_y(img)
    h, w = y.shape
    usable = (h // BLOCK) * (w // BLOCK)
    if usable < PAYLOAD_BITS:
        raise ValueError(
            f"image too small: {usable} blocks < {PAYLOAD_BITS} payload bits"
        )
    _embed_bits(y, bits, gap)
    return _merge_y(y, cb, cr)


def extract_payload(img: Image.Image) -> dict:
    """Recover the payload. Returns presence, magic distance, and fingerprint."""
    y, _, _ = _split_y(img)
    bits = _extract_bits(y, PAYLOAD_BITS)
    magic_bits = bits[: len(MAGIC)]
    fp_bits = bits[len(MAGIC) :]
    magic_hd = hamming(magic_bits, MAGIC)
    return {
        "present": magic_hd <= 2,  # tolerate up to 2 flipped magic bits
        "magic_hd": magic_hd,
        "fingerprint": bits_to_int(fp_bits),
        "fingerprint_bits": fp_bits,
    }


def psnr(a: Image.Image, b: Image.Image) -> float:
    """Peak signal-to-noise ratio (dB) between two images. Higher = less visible."""
    arr_a = np.asarray(a.convert("RGB"), dtype=np.float64)
    arr_b = np.asarray(b.convert("RGB"), dtype=np.float64)
    mse = np.mean((arr_a - arr_b) ** 2)
    if mse == 0:
        return float("inf")
    return 10.0 * np.log10((255.0**2) / mse)
