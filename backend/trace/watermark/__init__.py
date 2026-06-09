"""Per-candidate invisible DCT-domain watermarking and forensic tracing."""

from .core import (
    PAYLOAD_BITS,
    embed_fingerprint,
    extract_payload,
    make_fingerprint,
    psnr,
)
from .render import render_paper
from .trace import Registry, trace_image

__all__ = [
    "embed_fingerprint",
    "extract_payload",
    "make_fingerprint",
    "psnr",
    "PAYLOAD_BITS",
    "render_paper",
    "Registry",
    "trace_image",
]
