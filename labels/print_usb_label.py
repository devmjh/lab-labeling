"""Preview compact USB names on a full calibrated label, with cutting guides."""
import argparse
from pathlib import Path
import socket

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from .print_box_label import DEFAULT_HOST, FONT, render_label, to_zpl
except ImportError:
    from print_box_label import DEFAULT_HOST, FONT, render_label, to_zpl


ROW_CHOICES = (2, 3, 4)
FONT_PX_RANGE = (10, 120)


def render_fixed(name, width, height, font_px, font_path=FONT, margin=8):
    """Render one line at an explicit font size, centred, never enlarged or cropped."""
    if not FONT_PX_RANGE[0] <= font_px <= FONT_PX_RANGE[1]:
        raise ValueError(f"Text size must be between {FONT_PX_RANGE[0]} and {FONT_PX_RANGE[1]} px.")
    font = ImageFont.truetype(font_path, int(font_px))
    box = font.getbbox(name)
    glyph = Image.new("L", (max(1, box[2] - box[0]), max(1, box[3] - box[1])), 255)
    ImageDraw.Draw(glyph).text((-box[0], -box[1]), name, font=font, fill=0)
    ink = ImageOps.invert(glyph).getbbox()
    if not ink:
        raise ValueError("A strip has no printable characters.")
    glyph = glyph.crop(ink)
    if glyph.width > width - 2 * margin or glyph.height > height - 2 * margin:
        raise ValueError(f"'{name}' does not fit at {font_px} px; use a smaller size, "
                         "a longer strip or auto-fit.")
    label = Image.new("L", (width, height), 255)
    label.paste(glyph, ((width - glyph.width) // 2, (height - glyph.height) // 2))
    return label.point(lambda p: 255 if p >= 128 else 0).convert("1")


def render_strips(names, rows=3, length_mm=40, font_path=FONT, font_px=None):
    """Lay out up to ``rows`` names. Empty strings leave that strip blank.

    ``font_px`` None means auto-fit (the original behaviour); a number keeps
    that exact font size and refuses text that does not fit.
    """
    if rows not in ROW_CHOICES:
        raise ValueError("Choose two, three or four strips.")
    if not 15 <= length_mm <= 55:
        raise ValueError("Strip length must be between 15 and 55 mm.")
    if not 1 <= len(names) <= rows or not any(name.strip() for name in names):
        raise ValueError("Supply at least one name, up to the row count.")
    if any("\n" in name or "\r" in name for name in names):
        raise ValueError("Each strip needs a single line of text.")
    if any(len(name) > 300 for name in names):
        raise ValueError("Use at most 300 characters per strip; text is never truncated.")
    label = Image.new("1", (456, 253), 1)
    draw = ImageDraw.Draw(label)
    strip_width = round(length_mm * 8)
    for index in range(rows):
        top = round(index * 253 / rows)
        bottom = round((index + 1) * 253 / rows)
        if index < len(names) and names[index].strip():
            if font_px is None:
                strip = render_label([names[index]], width=strip_width,
                                     height=bottom - top - 8, margin=8,
                                     font_path=font_path)
            else:
                strip = render_fixed(names[index].strip(), strip_width,
                                     bottom - top - 8, font_px, font_path)
            label.paste(strip, (0, top + 4))
        if index:
            for x in range(0, 456, 12):
                draw.line((x, top, min(x + 4, 455), top), fill=0)
        # Short marks indicate where to trim the strip to the requested length.
        draw.line((strip_width, top + 3, strip_width, top + 9), fill=0)
        draw.line((strip_width, bottom - 10, strip_width, bottom - 4), fill=0)
    return label


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="+",
                        help='One quoted name per strip; "" leaves a strip blank; unused strips stay blank.')
    parser.add_argument("--rows", type=int, choices=ROW_CHOICES, default=3)
    parser.add_argument("--length-mm", type=float, default=40)
    parser.add_argument("--font-px", type=int, default=None,
                        help="Fixed text size in px (10-120). Default: auto-fit each strip.")
    parser.add_argument("--font", default=FONT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--print", dest="send", action="store_true")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "outputs/usb-strips"))
    args = parser.parse_args()
    try:
        label = render_strips(args.names, args.rows, args.length_mm, args.font, args.font_px)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        label.save(output.with_suffix(".png"))
        zpl = to_zpl(label, copies=1)
        output.with_suffix(".zpl").write_text(zpl, encoding="ascii")
        if args.send:
            with socket.create_connection((args.host, args.port), timeout=5) as printer:
                printer.sendall(zpl.encode("ascii"))
            print("Sent one sheet; check physical output before retrying.")
        else:
            print(f"Preview: {output.with_suffix('.png')}")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Label error: {exc}\n")


if __name__ == "__main__":
    main()
