"""Tests for the invisible DCT watermark: round-trip, invisibility, JPEG
robustness, and forensic tracing to the exact candidate."""

import io

import pytest
from PIL import Image

from trace.watermark import (
    Registry,
    embed_fingerprint,
    extract_payload,
    make_fingerprint,
    psnr,
    render_paper,
    trace_image,
)
from trace.watermark.core import FINGERPRINT_BITS, hamming, int_to_bits

# A paper large enough to give the watermark ample redundancy.
PAPER = "\n".join(
    [f"Q{i:02d}. This is exam line number {i} with some content to render." for i in range(1, 40)]
)


def _jpeg(img: Image.Image, quality: int) -> Image.Image:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


@pytest.fixture(scope="module")
def base_image():
    return render_paper(PAPER)


def test_render_has_enough_blocks(base_image):
    w, h = base_image.size
    assert (w // 8) * (h // 8) >= 80  # at least PAYLOAD_BITS blocks


def test_embed_then_extract_exact(base_image):
    fp = make_fingerprint("DEL-01", "R-007")
    wm = embed_fingerprint(base_image, fp)
    payload = extract_payload(wm)
    assert payload["present"] is True
    assert payload["magic_hd"] == 0
    assert payload["fingerprint"] == fp


def test_watermark_is_visually_subtle(base_image):
    fp = make_fingerprint("DEL-01", "R-007")
    wm = embed_fingerprint(base_image, fp)
    # > 32 dB PSNR is a standard "imperceptible" threshold for this kind of mark.
    assert psnr(base_image, wm) > 32.0


@pytest.mark.parametrize("quality", [95, 90, 75, 60])
def test_survives_jpeg_recompression(base_image, quality):
    fp = make_fingerprint("DEL-01", "R-007")
    wm = embed_fingerprint(base_image, fp)
    leaked = _jpeg(wm, quality)
    recovered = extract_payload(leaked)
    assert recovered["present"] is True
    assert recovered["fingerprint"] == fp  # exact recovery after recompression


def test_trace_identifies_exact_candidate_after_jpeg(base_image):
    registry = Registry()
    for i in range(1, 21):  # a roster of 20 candidates
        registry.issue("DEL-01", f"R-{i:03d}")

    fp = make_fingerprint("DEL-01", "R-013")
    wm = embed_fingerprint(base_image, fp)
    leaked = _jpeg(wm, 60)

    result = trace_image(leaked, registry)
    assert result["watermark_present"] is True
    assert result["match"]["candidate_id"] == "R-013"
    assert result["bit_distance"] == 0
    assert result["confidence"] == 1.0


def test_different_candidates_get_different_fingerprints(base_image):
    fp_a = make_fingerprint("DEL-01", "R-001")
    fp_b = make_fingerprint("DEL-01", "R-002")
    assert fp_a != fp_b
    a = extract_payload(embed_fingerprint(base_image, fp_a))["fingerprint"]
    b = extract_payload(embed_fingerprint(base_image, fp_b))["fingerprint"]
    assert a == fp_a and b == fp_b and a != b


def test_clean_image_is_not_flagged_as_watermarked(base_image):
    # An un-watermarked render (even after JPEG) should not trip presence.
    payload = extract_payload(_jpeg(base_image, 75))
    assert payload["present"] is False
    assert payload["magic_hd"] > 2


def test_image_too_small_raises():
    tiny = Image.new("RGB", (40, 40), (250, 250, 250))
    with pytest.raises(ValueError):
        embed_fingerprint(tiny, make_fingerprint("C", "X"))


def test_fingerprint_out_of_range_raises(base_image):
    with pytest.raises(ValueError):
        embed_fingerprint(base_image, 1 << FINGERPRINT_BITS)
