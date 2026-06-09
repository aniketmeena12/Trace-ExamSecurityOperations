"""Render exam paper text to an image (Pillow), ready for watermarking."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    # Pillow >= 10 supports a scalable default font.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_paper(
    text: str,
    *,
    font_size: int = 18,
    margin: int = 40,
    line_spacing: int = 8,
    background: tuple[int, int, int] = (250, 250, 250),
    foreground: tuple[int, int, int] = (20, 20, 20),
    min_width: int = 700,
) -> Image.Image:
    """Render `text` to an RGB image sized to fit the content.

    The slightly off-white background gives the watermark mid-band coefficients
    a touch of headroom while remaining visually clean.
    """
    font = _load_font(font_size)
    lines = text.replace("\t", "    ").splitlines() or [" "]

    # Measure with a scratch canvas.
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    line_h = font_size + line_spacing
    text_w = 0
    for line in lines:
        bbox = scratch.textbbox((0, 0), line or " ", font=font)
        text_w = max(text_w, bbox[2] - bbox[0])

    width = max(min_width, text_w + 2 * margin)
    height = 2 * margin + line_h * len(lines)

    img = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(img)
    y = margin
    for line in lines:
        draw.text((margin, y), line, font=font, fill=foreground)
        y += line_h
    return img
