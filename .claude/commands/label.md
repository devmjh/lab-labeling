---
description: Draft a lab label from a plain description, preview it, and print only after approval
argument-hint: <what it is, e.g. "box of robot car parts" or "usb: ubuntu 26.04, empty 32gb">
allowed-tools: Read, Bash(.venv/bin/python labels/print_box_label.py:*), Bash(.venv/bin/python labels/print_usb_label.py:*)
---

Make a lab label for: **$ARGUMENTS**

Current label conventions (from the repo instructions):
@AGENTS.md

Steps:
1. Decide the format: Box (2 copies), Bag/device (1 copy), or USB strips
   (2, 3 or 4 rows). Use the lab-label-writer skill for wording rules.
2. Write the text: one heading plus up to three short detail lines, or one short
   name per USB strip. Show me the proposed text before rendering.
3. Render a preview only, never with `--print`:
   - General: `.venv/bin/python labels/print_box_label.py "HEADING" "DETAIL" --copies N --output outputs/slash-preview`
   - USB: `.venv/bin/python labels/print_usb_label.py "NAME 1" "NAME 2" --rows 3 --output outputs/slash-preview`
4. Open `outputs/slash-preview.png` with Read and show it to me.
5. Ask whether to print. Only after I say yes, rerun the exact same command with
   `--print`. Say "sent", never "printed": TCP success does not prove the label came out.
