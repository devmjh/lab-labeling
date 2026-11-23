# Obsidian inventory contract

The live source of truth is `C:\Users\james\Lab\Lab` (inner Lab directory).
Use the connected Obsidian tools where available. Read current notes before edits;
do not rebuild inventory from chat history or the old JSON snapshots.

## End-to-end batch

1. James takes a photo on the dedicated Samsung and asks for identification/sorting.
2. Run `python lab-photos/photos.py wait` (or `latest --max-age 10`, or `fetch NAME`).
   Plain `latest` can return an older, unrelated photo. Or use `/identify part|box`.
3. Inspect the original resolution, read markings, and keep uncertain IDs explicit.
   Photo arrival alone does not authorize printing or assigning guessed contents.
4. Read the relevant box/item notes and index. Choose practical existing categories,
   preserve complete kits, and distinguish suggested additions from actual contents.
5. Update the notes and index for confirmed changes. Save UTF-8 with LF; preserve
   unrelated fields. Read back edits and check links/contents.
6. Generate and inspect the label preview, then print requested copies. If printing
   fails, report that separately from the inventory update; do not claim it printed.
7. Report affected files and physical label sends. Record any unresolved placement.
8. Commit and push the reviewed batch under the standing authorization in the vault's AGENTS.md; verify
   synchronization before ending the batch or pausing the session.

The workflow is currently agent-assisted. There is no transaction spanning paper,
files and photos. Persistent evidence needs explicit preservation outside temporary
storage. A future UI should show inventory-save and print-send results separately.

## Structure

Vault paths (moved under `Projects/AI Tech Lab/` on 2026-11-22):

```text
Projects/AI Tech Lab/Inventory/Lab Inventory.md         # category links and Still to inventory checklist
Projects/AI Tech Lab/Inventory/Inventory.base           # existing Bases table; do not edit unless asked
Projects/AI Tech Lab/Inventory/Boxes/<Box Name>.md
Projects/AI Tech Lab/Inventory/Drawers/Drawer NN.md      # Drawer 01 through Drawer 15 as inventoried
Projects/AI Tech Lab/Inventory/Items/<Item Name>.md
Templates/Box template.md          # do not change unless asked
```

## Box/drawer schema

```markdown
---
tags: [inventory, box]
category: Components & Supplies
size: ""
location: ""
status: packed
---
# Box Name

## Contents
- Specific item, model number where known

## Notes
- [ ] Optional unresolved work

## Related
- [[Related Note]]

---
Back to [[Lab Inventory]]
```

For drawers use `tags: [inventory, drawer]`. Allowed categories:
`Cables & Power`, `Components & Supplies`, `Tools & Maintenance`,
`Boards, Equipment & Kits`. Add a category only if none fits, with an index section.
Allowed inventory status values: `packed`, `room left`, `project in progress`,
`awaiting assembly`, `ready to assemble`, `unplaced`, `placed`.
Host notes use their own status vocabulary, for example `offline`.

Item notes use `tags: [inventory, item]`, `box: ""`, and `status: unplaced`.
Once placed, add the item to its destination Contents and set
`box: "[[Box Name]]"`, `status: placed` (preferred over deleting the item note).

## Editing invariants

- Filename represents the physical label. Avoid `/ \\ : * ? " < > |` in filenames.
  Existing names sometimes differ from printed headings, e.g. Raspberry Pi + PiSugar.
  Keep those established names until James confirms a rename; do not bulk normalize.
- A rename must update all references across the entire vault, including aliases,
  anchors and path-qualified wikilinks. Verify with a whole-vault search afterward.
- A move removes the item from its former box and adds it to its new one. Do not
  leave duplicate ownership. Do not confuse identical multiple items with one item.
- A new box/drawer also gets a category link in the index. Keep its count current.
- Tick completed Still to inventory tasks. For partially completed drawer work,
  retain the overall task until all drawers are done; track progress in its checklist.
- Use wikilinks, including existing [[ESP32 Enclosure]], [[AI Tech Lab]] and hosts
  such as [[rdunano1]], where relevant.
- Keep existing YAML fields and meanings intact. Change only requested fields;
  quote values containing colons or beginning with `[`. Do not overwrite metadata
  by replacing the full note body with a guessed frontmatter block.
- Do not touch `.obsidian/`, templates, or non-Inventory notes. Exceptions: rename
  link maintenance and a host's status when hardware moves. Report such exceptions.
- Leave unknown size/location blank. Do not promote suggestions to confirmed facts.

## Confirmed state and remaining work at consolidation

The index contains 38 box links. rdunano1 is offline and packed in Small Device Kits;
its host note was corrected with James's confirmation. Webcam, Seeed Sensor Kit and
ELECROW HMI outer placements remain unconfirmed. Box shelf locations remain unknown.
Small-parts boxes and about 15 drawers remain to inventory. The live vault, not this
dated paragraph, decides future state.

## Identification rules and push authorization

Identification and sorting expectations live in the `lab-inventory` skill
(`.claude/skills/lab-inventory/SKILL.md`). The standing Git push authorization
lives in the vault's `AGENTS.md`. They are kept in one place each so they cannot drift.

## Labeling repository migration, 2026-11-22

James explicitly requested this directory and authorized publishing its code and support files to `devmjh/lab-labeling`. This is the labeling development home. The old lab-inventory source is preserved; inventory data remains in the separate private lab-context Obsidian repository. Read README.md for Windows/Linux setup.
