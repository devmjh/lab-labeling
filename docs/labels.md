# Labels

Use `labels/print_box_label.py`, the full-width raster replacement for the old
`C:\Users\james\print_lab_label_net.py`. The old script reserved space for a QR code
and truncated text; this renderer measures glyphs and scales the full heading and
details proportionally. All detail lines share one scale, capped below the heading,
so a short detail such as ARMS does not dominate the label.

```powershell
python labels/print_box_label.py "SOLDERING SUPPLIES" "IRONS / TIPS" "SOLDER / FLUX" --copies 2 --output outputs/soldering
# Inspect outputs/soldering.png, then send:
python labels/print_box_label.py "SOLDERING SUPPLIES" "IRONS / TIPS" "SOLDER / FLUX" --copies 2 --output outputs/soldering --print
```

One quoted argument per line. Newlines within an argument also work. Use one copy
for bags/devices, two for boxes. An explicitly requested extra copy means one.
The GUI uses the `--copies` value supplied when launched.

Defaults: `--host 192.168.4.113 --port 9100 --width 456 --height 253 --margin 8
--offset-mm 5`. The +5 mm calibration is printer Label Top (`^LT40`), not extra
blank pixels. PNG previews show the logical layout before physical offset. Keep
the calibration unless James asks to adjust it. `--border` is diagnostic only.

Fonts are rendered locally with Pillow and sent using ZPL `^GFA`; printer font
availability does not matter. Width/height retain glyph proportions. Four to six
lines are possible, but concise contents preserve legibility. Long headings shrink.
No em-dashes. Use slashes between parallel details and ordinary hyphens where needed.

TCP success means the bytes were sent, not that media fed or a label printed.
Do not retry a possibly sent job automatically: inspect the printer to avoid doubles.
Calibration and transport were proven in the original workflow. Repository tests
do not consume labels. Existing old-workspace scripts remain for compatibility;
future labeling development belongs in devmjh/lab-labeling (this repository).
