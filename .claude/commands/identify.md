---
description: Identify a part/board/device from a lab phone photo, or inventory a box's contents from one
argument-hint: part|box [PHOTO.jpg] [BOX NAME]   (no photo = wait for the next one)
allowed-tools: Read, Bash(.venv/bin/python lab-photos/photos.py:*), Bash(git -C ../lab-context pull --ff-only)
---

Mode and arguments: **$ARGUMENTS**
(First word is `part` or `box`. A word ending in .jpg/.png/.heic is a photo name.
Anything else after `box` is the box name.)

## 1. Get exactly one photo
- Photo name given: `.venv/bin/python lab-photos/photos.py fetch NAME`
- Otherwise tell me "Take the photo now", then run
  `.venv/bin/python lab-photos/photos.py wait --timeout 300`
Read the printed path once with Read. Do not fetch extra photos unless I ask:
each image costs tokens. Photos are temporary; never copy them anywhere.

## 2a. Mode `part`: identify a component, logic board or device
- Read every legible marking. Separate **confirmed** (read from the photo),
  **inferred** (family by appearance/layout) and **unknown** (ratings, revision).
- Give: most specific supported name/model, what it does in plain words, a
  practical project use, and anything worth knowing (voltage if printed, etc.).
- If markings are unreadable, say exactly which close-up would settle it
  (e.g. "the chip near the USB port, straight on") instead of guessing.
- Propose Bag/device label text using the lab-label-writer skill.
- Suggest which existing box it belongs in: `git -C ../lab-context pull --ff-only`,
  then read `../lab-context/Inventory/Lab Inventory.md` (box list only).

## 2b. Mode `box`: inventory a box
- List what is visible, grouped, with counts only when they are clear.
- If a box name was given, read `../lab-context/Inventory/Boxes/<BOX NAME>.md`
  after pulling and show: **new** (in photo, not in note), **missing** (in note,
  not visible), **uncertain**. Missing from one photo is not proof it is gone.
- Propose the note edits and a Box label; follow `docs/inventory-workflow.md`.

## 3. Stop and ask
Do not edit notes or print until I say yes. Then: note edits per the inventory
workflow, label via the label app or `/label`, and report "sent", never "printed".
If `../lab-context` does not exist on this computer, ask where the vault clone is.
