"""Zebra labels with a prominent heading and consistent smaller details.
Requires Pillow (python -m pip install pillow).

python print_box_label.py "SCREWS" --print
python print_box_label.py "USB CABLES" "ADAPTERS" --print
Without --print, saves a PNG preview and ZPL in the repository outputs directory.
With no text arguments, opens a simple label form.
"""
import argparse
from pathlib import Path
import socket
from PIL import Image, ImageDraw, ImageFont, ImageOps

DEFAULT_HOST = "192.168.4.113"
FONT = next((p for p in ("C:/Windows/Fonts/arialbd.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
             if Path(p).is_file()), "DejaVuSans-Bold.ttf")


def render_label(lines, width=456, height=253, margin=8, border=False, font_path=FONT):
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        raise ValueError("Enter at least one line of text.")
    if not 64 <= width <= 832 or not 64 <= height <= 2000:
        raise ValueError("Label dimensions exceed supported limits.")
    gap = 8
    usable_width = width - 2 * margin
    row_height = (height - 2 * margin - gap * (len(lines) - 1)) // len(lines)
    if usable_width < 16 or row_height < 12:
        raise ValueError("Too many lines or too large a margin for this label.")
    label = Image.new("L", (width, height), 255)
    glyphs = []
    for line in lines:
        if len(line) > 300:
            raise ValueError("Use at most 300 characters per line; text is never truncated.")
        font = ImageFont.truetype(font_path, 200)
        box = font.getbbox(line)
        glyph = Image.new("L", (box[2] - box[0], box[3] - box[1]), 255)
        ImageDraw.Draw(glyph).text((-box[0], -box[1]), line, font=font, fill=0)
        ink = ImageOps.invert(glyph).getbbox()
        if not ink:
            raise ValueError("A line has no printable characters.")
        glyph = glyph.crop(ink)
        glyphs.append(glyph)
    # Preserve letter proportions. All detail lines share the same scale,
    # so a short detail such as ARMS cannot become larger than its peers.
    heading_scale = usable_width / glyphs[0].width
    scales = [heading_scale]
    if len(glyphs) > 1:
        detail_scale = min(heading_scale * 0.72,
                           usable_width / max(g.width for g in glyphs[1:]))
        scales.extend([detail_scale] * (len(glyphs) - 1))
    ink_height = sum(g.height * s for g, s in zip(glyphs, scales))
    fit = min(1, (height - 2 * margin - gap * (len(lines) - 1)) / ink_height)
    sized = [g.resize((max(1, round(g.width * s * fit)),
                       max(1, round(g.height * s * fit))), Image.Resampling.LANCZOS)
             for g, s in zip(glyphs, scales)]
    total_height = sum(g.height for g in sized) + gap * (len(lines) - 1)
    y = (height - total_height) // 2
    for glyph in sized:
        label.paste(glyph, ((width - glyph.width) // 2, y))
        y += glyph.height + gap
    if border:
        ImageDraw.Draw(label).rectangle((3, 3, width - 4, height - 4), outline=0, width=2)
    return label.point(lambda p: 255 if p >= 128 else 0).convert("1")


def to_zpl(label, offset_mm=5.0, copies=1):
    if not isinstance(copies, int) or not 1 <= copies <= 100:
        raise ValueError("Copies must be an integer between 1 and 100.")
    # GX420d reports 8 dots/mm. Positive Label Top moves the print down.
    offset_dots = round(offset_mm * 8)
    if not -120 <= offset_dots <= 120:
        raise ValueError("Vertical offset must be between -15 and 15 mm.")
    width, height = label.size
    # ZPL uses 1 for black, unlike Pillow's monochrome image representation.
    row_bytes = (width + 7) // 8
    padded = Image.new("1", (row_bytes * 8, height), 0)
    padded.paste(ImageOps.invert(label.convert("L")).convert("1"), (0, 0))
    raw = padded.tobytes()
    return (f"^XA\n^PW{width}\n^LL{height}\n^LH0,0\n^LS0\n^LT{offset_dots}\n"
            f"^FO0,0^GFA,{len(raw)},{len(raw)},{row_bytes},{raw.hex().upper()}^FS\n^PQ{copies}\n^XZ\n")


def save_and_send(lines, args, send=False):
    label = render_label(lines, args.width, args.height, args.margin, args.border, args.font)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    label.save(output.with_suffix(".png"))
    zpl = to_zpl(label, args.offset_mm, args.copies)
    output.with_suffix(".zpl").write_text(zpl, encoding="ascii")
    if send:
        with socket.create_connection((args.host, args.port), timeout=5) as printer:
            printer.sendall(zpl.encode("ascii"))
        print(f"Sent {args.copies} label(s); check the physical output.")
    else:
        print(f"Preview: {output.with_suffix('.png')}")
    return label


def gui(args):
    import tkinter as tk
    from tkinter import messagebox
    from PIL import ImageTk
    root = tk.Tk()
    root.title("Box Labels")
    tk.Label(root, text="First line: heading. Following lines: smaller, equally sized details.").pack(padx=16, pady=10)
    entry = tk.Text(root, width=38, height=6, font=("Arial", 16))
    entry.pack(padx=16)
    preview = tk.Label(root)
    preview.pack(pady=10)
    status = tk.StringVar(value=f"Printer: {args.host}")

    def run(send=False):
        try:
            label = save_and_send(entry.get("1.0", "end").splitlines(), args, send)
            preview.image = ImageTk.PhotoImage(label)
            preview.configure(image=preview.image)
            status.set(f"Sent {args.copies} label(s)." if send else "Preview updated.")
        except Exception as exc:
            messagebox.showerror("Label error", str(exc))

    tk.Button(root, text="Preview", command=run).pack(pady=3)
    tk.Button(root, text=f"Print {args.copies} label(s)", command=lambda: run(True)).pack(pady=3)
    tk.Label(root, textvariable=status).pack(padx=16, pady=10)
    entry.focus_set()
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lines", nargs="*", help="Each quoted argument is a separate line.")
    parser.add_argument("--print", dest="send", action="store_true")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--copies", type=int, default=1, help="1 for a bag; 2 for a box lid and side.")
    parser.add_argument("--font", default=FONT, help="Path to a bold TrueType font.")
    parser.add_argument("--width", type=int, default=456, help="Label width in dots (203 per inch).")
    parser.add_argument("--height", type=int, default=253)
    parser.add_argument("--margin", type=int, default=8)
    parser.add_argument("--offset-mm", type=float, default=5.0,
                        help="Printer vertical alignment in mm; positive moves down (default: 5). PNG shows layout before this physical alignment correction.")
    parser.add_argument("--border", action="store_true", help="Draw a diagnostic edge frame.")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "outputs" / "label_preview"))
    args = parser.parse_args()
    if args.lines:
        try:
            save_and_send([line for arg in args.lines for line in arg.splitlines()], args, args.send)
        except (ValueError, OSError) as exc:
            parser.exit(1, f"Label error: {exc}\n")
    else:
        gui(args)


if __name__ == "__main__":
    main()
