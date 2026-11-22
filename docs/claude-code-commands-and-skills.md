# Learning Claude Code: slash commands and skills

This repository ships one of each, so you can read real working examples.

| | Slash command | Skill |
| --- | --- | --- |
| File | `.claude/commands/label.md` | `.claude/skills/lab-label-writer/SKILL.md` |
| Who starts it | You type `/label ...` | Claude loads it by itself when the task matches its `description` (you can also type `/lab-label-writer`) |
| Best for | A repeatable *procedure* you trigger on purpose | *Know-how* Claude should apply whenever relevant |
| Extra files | Usually just the one file | A folder; supporting files (here `examples.md`) are read only when needed |

Both are plain Markdown with a YAML header between `---` lines. Files under the
repo's `.claude/` folder travel with Git, so Windows and Linux get the same ones.
Personal versions go in `~/.claude/commands/` or `~/.claude/skills/` instead.

## Anatomy of `/label`

```markdown
---
description: ...            # shown in the / menu
argument-hint: <what it is> # grey hint after you type /label
allowed-tools: Read, Bash(.venv/bin/python labels/print_box_label.py:*)
---
Make a lab label for: **$ARGUMENTS**   <- everything you typed after /label
@AGENTS.md                              <- pastes that file into the prompt
```

- `$ARGUMENTS` is replaced by your text: `/label box of robot car parts`.
- `@path` includes a file's contents at run time, so the rules are always current.
- `allowed-tools` pre-approves those tools while the command runs. Prefix rules
  cannot exclude `--print`, so the body tells Claude never to print without your yes.
- A line starting with `` !`some command` `` runs that shell command first and
  pastes its output in (handy for `git status` or a printer check).

Try it: in Claude Code, opened in this repo, type `/label usb: ubuntu server 26.04, empty 32gb`.

## Anatomy of the `lab-label-writer` skill

```markdown
---
name: lab-label-writer
description: Writes and reviews text for James's Zebra lab labels ... Use whenever ...
---
# Writing lab labels
...rules...  More worked examples: [examples.md](examples.md)
```

- `description` is the trigger. Claude sees only the name and description until a
  task matches, then reads the full body. Say *what* it does and *when* to use it.
- Keep `SKILL.md` focused and link bigger reference files. Claude opens them only
  when needed, which keeps context small ("progressive disclosure").
- Skills can also bundle scripts that Claude runs instead of rewriting code.

Try it: ask "what should the label for this HC-SR04 bag say?" without any slash.
Claude should pick up the skill on its own.

## More commands in this repo

- `/identify part|box [PHOTO] [BOX]`: waits for the next phone photo, identifies a
  part or inventories a box, proposes label text, and stops for your yes.
- `/handoff [project]`: writes a dated status block into the project's Obsidian
  Dev Handoff note and pushes lab-context. It shows the `` !`git status -sb` ``
  trick: those commands run *before* Claude starts, so their output arrives in
  the prompt without spending tool calls (a token saver).

## Ideas to build next yourself

- `/usb-sheet`: queue scanned USB names until a sheet is full.
- `/lab-sync`: pull both repos and list anything unpushed.
- A `zpl-debugging` skill describing `^LT`, `^PQ`, `^GFA` and the calibration.
- `/inventory-box NAME`: read a box note from the vault and draft its label.
