---
name: lab-label-writer
description: Writes and reviews text for James's Zebra lab labels (storage boxes, component bags, devices, USB stick strips) and picks the right format, copy count and text size. Use whenever composing, shortening or checking label wording, or when asked to label a part, kit, box or USB stick.
---

# Writing lab labels

The label is 57 x 32 mm (2.25 x 1.25 in), 456 x 253 dots. Space is tiny, so
every word must earn its place.

## Pick the format

| What | Format | Copies | Shape |
| --- | --- | --- | --- |
| Storage box | Box | 2 (lid and side) | Heading + 1-3 details |
| Component bag, board, device | Bag / device | 1 | Heading + 1-3 details |
| USB sticks | USB strips | 1 sheet | 2, 3 or 4 one-line names, cut apart |

## Wording rules

- **Heading** = the most specific supported name: model or family, e.g.
  `ESP32 DEVKIT V1`, not `MICROCONTROLLER` and not just `DEVKIT V1`.
- **Details** = what it does in plain words, then a practical use. Add confirmed
  quantity or ratings only if verified. Example:
  `WIFI + BLUETOOTH MICROCONTROLLER` / `SENSOR / IOT PROJECTS`.
- UPPERCASE. Slashes between parallel items. Plain hyphens only, **never em-dashes**.
- Generic words alone ("module", "logic board", "charger") are not enough.
  A model number alone is not enough either.
- If the evidence does not support an identification, say so and ask for a
  close-up rather than printing a vague label. Mark inferred IDs as inferred.
- Keep detail lines short; each extra line makes all details smaller. The app warns
  when text drops under 2.5 mm tall; aim to avoid that warning.

## USB strip names

- One short line per stick, from inspection evidence, not a guess:
  `UBUNTU SRV 26.04`, `EMPTY 32GB`, `PROXMOX VE 9.1`, `WINPE UTIL`.
- Auto-fit grows each name to fill its strip. For deliberately modest text such
  as `32GB`, use a fixed size (Small 24 px, Medium 32 px) instead.
- Partial sheets are fine; empty rows print blank. Each copy is a full sheet.

## Previewing

Preview before any print; printing needs James's explicit yes. Either open the app
(`.venv/bin/python labels/label_app.py`, or add `--dry-run` to test safely) or use
the CLIs shown in `README.md`. More worked examples: [examples.md](examples.md).
