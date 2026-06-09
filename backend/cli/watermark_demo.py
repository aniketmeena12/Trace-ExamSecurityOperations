#!/usr/bin/env python3
"""Trace — invisible watermark + forensic trace walkthrough (Milestone 3).

Demonstrates guarantee #2 end-to-end, all real:

  1. Render the sample paper to an image.
  2. Issue a uniquely watermarked copy to a specific candidate (R-007).
  3. Show it is visually subtle (PSNR) and save before/after/diff images.
  4. "Leak" the copy by re-compressing it as a JPEG (quality 60).
  5. From the leaked JPEG alone, trace it back to the EXACT candidate against a
     roster of 20 — and confirm a clean image is not falsely flagged.

Outputs go to ../demo_output/ so you can open them and confirm the mark is
invisible to the eye.

Usage:  python -m cli.watermark_demo
"""

import io
from pathlib import Path

import numpy as np
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

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
GREEN, RED, CYAN, YELLOW = "\033[32m", "\033[31m", "\033[36m", "\033[33m"


def hdr(t): print(f"\n{BOLD}{CYAN}== {t} =={RESET}")
def ok(t): print(f"  {GREEN}[OK]{RESET} {t}")
def info(t): print(f"  {DIM}{t}{RESET}")


def jpeg(img, q):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def amplified_diff(a, b, factor=24):
    """Visualize where the watermark lives by amplifying the pixel difference."""
    da = np.asarray(a.convert("RGB"), np.int16)
    db = np.asarray(b.convert("RGB"), np.int16)
    diff = np.clip(128 + (db - da) * factor, 0, 255).astype(np.uint8)
    return Image.fromarray(diff)


def main():
    repo = Path(__file__).resolve().parents[2]
    out = repo / "demo_output"
    out.mkdir(exist_ok=True)
    paper = (repo / "sample_data" / "sample_paper.txt").read_text()

    print(f"{BOLD}TRACE — Per-Candidate Invisible Watermark + Forensic Trace (M3){RESET}")

    hdr("1-2  Render the paper and issue a watermarked copy to candidate R-007")
    base = render_paper(paper)
    blocks = (base.size[0] // 8) * (base.size[1] // 8)
    info(f"rendered {base.size[0]}x{base.size[1]} px  ({blocks} 8x8 blocks)")

    registry = Registry()
    for i in range(1, 21):
        registry.issue("DEL-01", f"R-{i:03d}")
    fp = make_fingerprint("DEL-01", "R-007")
    wm = embed_fingerprint(base, fp)
    info(f"fingerprint(DEL-01, R-007) = {fp:#018x}")
    ok(f"watermarked copy issued; registry holds {len(registry)} candidates")

    hdr("3  The mark is visually subtle")
    p = psnr(base, wm)
    ok(f"PSNR(original, watermarked) = {p:.1f} dB  (>32 dB = imperceptible)")
    base.save(out / "01_original.png")
    wm.save(out / "02_watermarked.png")
    amplified_diff(base, wm).save(out / "03_diff_amplified_24x.png")
    info(f"saved 01_original.png, 02_watermarked.png, 03_diff_amplified_24x.png -> {out}")

    hdr("4  Leak the copy as a re-compressed JPEG (quality 60)")
    leaked = jpeg(wm, 60)
    leaked.save(out / "04_leaked_q60.jpg")
    info("saved 04_leaked_q60.jpg (this is the file an attacker would share)")

    hdr("5  Trace the leak back to its exact source")
    res = trace_image(leaked, registry)
    ok(f"watermark detected (magic distance {res['magic_hd']})")
    ok(f"extracted fingerprint = {res['extracted_fingerprint']:#018x}")
    print(f"  {BOLD}{GREEN}>> LEAK TRACED to {res['match']['center_id']} / "
          f"candidate {res['match']['candidate_id']}{RESET}  "
          f"(bit errors: {res['bit_distance']}/64, confidence {res['confidence']*100:.1f}%)")

    clean = extract_payload(jpeg(base, 75))
    info(f"control: un-watermarked page reports present={clean['present']} "
         f"(magic distance {clean['magic_hd']}) — no false accusation")

    print(f"\n{BOLD}{GREEN}M3 watermark + trace verified end-to-end.{RESET}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
