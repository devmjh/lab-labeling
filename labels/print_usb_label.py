"""Preview compact USB names on a full calibrated label, with cutting guides."""
import argparse
from pathlib import Path
import socket

from PIL import Image, ImageDraw

try:
    from .print_box_label import DEFAULT_HOST, FONT, render_label, to_zpl
except ImportError:
    from print_box_label import DEFAULT_HOST, FONT, render_label, to_zpl


def render_strips(names, rows=3, length_mm=40, font_path=FONT):
    if rows not in (2, 3):
        raise ValueError("Choose two or three strips.")
    if not 15 <= length_mm <= 55:
        raise ValueError("Strip length must be between 15 and 55 mm.")
    if not 1 <= len(names) <= rows or any(not name.strip() for name in names):
        raise ValueError("Supply one nonempty name per occupied strip, up to the row count.")
    if any("\n" in name or "\r" in name for name in names):
        raise ValueError("Each strip needs a single line of text.")
    label = Image.new("1", (456, 253), 1)
    draw = ImageDraw.Draw(label)
    strip_width = round(length_mm * 8)
    for index in range(rows):
        top = round(index * 253 / rows)
        bottom = round((index + 1) * 253 / rows)
        if index < len(names):
            strip = render_label([names[index]], width=strip_width,
                                 height=bottom - top - 8, margin=8,
                                 font_path=font_path)
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
    parser.add_argument("names", nargs="+", help="One quoted name per strip; unused strips stay blank.")
    parser.add_argument("--rows", type=int, choices=(2, 3), default=3)
    parser.add_argument("--length-mm", type=float, default=40)
    parser.add_argument("--font", default=FONT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--print", dest="send", action="store_true")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "outputs/usb-strips"))
    args = parser.parse_args()
    try:
        label = render_strips(args.names, args.rows, args.length_mm, args.font)
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
