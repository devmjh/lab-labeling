# Lab labeling

Portable Python tools for Zebra box, bag and device labels, plus the existing
component-photo inbox tools. Repository: https://github.com/devmjh/lab-labeling

## Linux setup on labnet007

On Debian/Ubuntu install the following packages (use equivalents on other distributions):

```sh
sudo apt-get install python3 python3-venv python3-tk fonts-dejavu-core openssh-client
git clone git@github.com:devmjh/lab-labeling.git
cd lab-labeling
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

For an existing clone, use `git pull --ff-only` with a clean working tree.
Python 3.11+ is required. Tk is optional for command-line use; the form needs a desktop.

## Windows setup

```powershell
git clone git@github.com:devmjh/lab-labeling.git
cd lab-labeling
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m unittest discover -s tests -v
```

## Preview, then print

Run from the repository root. On Windows substitute `.venv/Scripts/python`:

```sh
.venv/bin/python labels/print_box_label.py "PROJECT ELECTRONICS" "BOARDS / SENSORS / AUDIO" --copies 2 --output outputs/project-electronics
```

Inspect `outputs/project-electronics.png`, then repeat with `--print` to send:

```sh
.venv/bin/python labels/print_box_label.py "PROJECT ELECTRONICS" "BOARDS / SENSORS / AUDIO" --copies 2 --output outputs/project-electronics --print
```

One quoted argument per line, heading first. Two copies for boxes, one for bags/devices.
Without text arguments, the script opens the label form:

```sh
.venv/bin/python labels/print_box_label.py --copies 2
```

The calibrated defaults remain Zebra GX420d, `192.168.4.113:9100`, 456 x 253 dots,
margin 8, no border and +5 mm Label Top (`^LT40`). Override address with `--host`
and `--port`. Raw TCP printing needs lab network access, but no CUPS/printer driver.
TCP success confirms sending, not physical printing. Check the printer before retrying.

Windows uses Arial Bold; Linux uses DejaVu Sans Bold. Dimensions remain the same,
but font appearance can differ. Use `--font /path/to/font.ttf` if desired and always
preview after changing computers/fonts. See [label details](docs/labels.md).

## Batch helpers

Both portable helpers accept a JSON manifest instead of yesterday's hardcoded paths:

```sh
.venv/bin/python preview-component-labels.py examples/labels.json --output-dir outputs/example
```

Inspect every PNG and the combined `previews.png`, then send the same reviewed manifest:

```sh
.venv/bin/python print-component-labels.py examples/labels.json --output-dir outputs/example --print
```

Without `--print`, the print helper also previews only. Successful TCP sends are logged
in `sends.jsonl`; identical previously sent jobs in that output directory are skipped.
Changed content/copies are new jobs requiring preview. Logs cannot confirm physical
printing, resolve interrupted sends or prevent duplicates across separate computers.
Actual batch manifests and send logs stay local; the example contains no inventory.

## Photos and shared context

```sh
.venv/bin/python lab-photos/photos.py list
.venv/bin/python lab-photos/photos.py fetch PHOTO_FILENAME.jpg
```

Photo access requires your own authorized OpenSSH alias `rdulx009`. Keys are not
included. See [configuration](docs/configuration.md) and [photo intake](docs/photo-inbox.md).
The cache and server inbox are temporary. Included server provisioning/retention
sources are references, not workstation setup steps; do not run them to test labeling.

The inventory and durable lab context remain in the separate Obsidian repository
`devmjh/lab-context`. Pull that repository on each computer, then read its `AGENTS.md`
and `Inventory/Lab Inventory.md` before resuming. This shares records, procedures and
decisions rather than chat history. These tools do not automatically edit or sync
Obsidian. Identification and inventory updates remain agent-assisted.

## Project contents and provenance

- `labels/print_box_label.py`: calibrated renderer, CLI, GUI and TCP transport.
- `labels/batch_labels.py`: portable batch previews and send log.
- `preview-component-labels.py`, `print-component-labels.py`: batch entry points.
- `tests/`: mocked printer tests and temporary retention fixtures.
- `docs/`: labeling, inventory workflow, photo configuration and historical checks.
- `AGENTS.md`: continuing assistant instructions and regular push authorization.

This is the labeling development home as of 2026-11-22. Source and support files
were copied from `devmjh/lab-inventory` commit `b9106f9`; batch helpers were made
portable. Existing source copies, live servers, phone settings, inventory placements
and printer calibration were preserved. No physical test labels are needed for setup.

After completed batches, push reviewed inventory updates to `lab-context` and tool
changes here. Credentials, photo caches, generated labels, local manifests and live
vault copies are excluded from Git. See [inventory workflow](docs/inventory-workflow.md).
