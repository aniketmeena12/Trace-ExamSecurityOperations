"""Forensic tracing: map a (possibly recompressed) leaked image to its source.

The issuing system records, for every watermarked copy it hands out, the
fingerprint -> (center, candidate) mapping. To trace a leak we extract the
fingerprint from the image and find the registry entry with the smallest
Hamming distance — this tolerates the handful of bit errors a JPEG round-trip
or screenshot may introduce, and still names the exact source copy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from .core import FINGERPRINT_BITS, extract_payload, int_to_bits, make_fingerprint


@dataclass
class Registry:
    """fingerprint -> metadata about the issued copy."""

    entries: dict[int, dict] = field(default_factory=dict)

    def issue(self, center_id: str, candidate_id: str, **meta) -> int:
        fp = make_fingerprint(center_id, candidate_id)
        self.entries[fp] = {
            "center_id": center_id,
            "candidate_id": candidate_id,
            **meta,
        }
        return fp

    def __len__(self) -> int:
        return len(self.entries)


def trace_image(img: Image.Image, registry: Registry) -> dict:
    """Identify the most likely source copy of `img`.

    Returns a dict with the extracted fingerprint, the matched entry, the bit
    distance, and a confidence in [0, 1] (1 = exact match).
    """
    payload = extract_payload(img)
    recovered = int_to_bits(payload["fingerprint"], FINGERPRINT_BITS)

    best_fp = None
    best_meta = None
    best_hd = FINGERPRINT_BITS + 1
    for fp, meta in registry.entries.items():
        hd = sum(
            1
            for x, y in zip(recovered, int_to_bits(fp, FINGERPRINT_BITS))
            if x != y
        )
        if hd < best_hd:
            best_hd, best_fp, best_meta = hd, fp, meta

    confidence = 1.0 - best_hd / FINGERPRINT_BITS if best_fp is not None else 0.0
    return {
        "watermark_present": payload["present"],
        "magic_hd": payload["magic_hd"],
        "extracted_fingerprint": payload["fingerprint"],
        "matched_fingerprint": best_fp,
        "match": best_meta,
        "bit_distance": best_hd if best_fp is not None else None,
        "confidence": confidence,
    }
