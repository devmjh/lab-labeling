# lab-labeling: code repository rules

Zebra label app, label CLIs and the phone-photo client. Setup and usage: `README.md`.

- **Shared lab rules and the Git push authorization** live in the vault's
  `AGENTS.md` (`devmjh/lab-context`). Follow them; this file does not repeat them.
- **Identifying parts, sorting into boxes or editing inventory:** use the
  `lab-inventory` skill (`.claude/skills/lab-inventory/`). Label wording:
  `lab-label-writer` skill.
- **Calibration:** 456 x 253 dots, margin 8, no border. Box/bag labels `^LT40`
  (+5 mm); USB strip sheets `^LT50` (+6.25 mm). Change only when James asks.
- **Printing:** preview before every send; never print to test code. TCP success
  means "sent", not "printed".
- **Tests:** `.venv/bin/python -m unittest discover -s tests` must pass before a
  push. Mock the printer socket, SSH and adb; tests must not consume labels or
  touch the live photo server.
- **Never commit** keys, photo caches (`lab-photos/cache/`), `local/` state,
  generated `outputs/`, or live vault copies.
