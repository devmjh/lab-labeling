# Lab labeling

Portable Python tools for Zebra box, bag and device labels, plus the existing
component-photo inbox tools. Repository: https://github.com/devmjh/lab-labeling

## Linux setup on labnet007

On Debian/Ubuntu install the following packages (use equivalents on other distributions):

```sh
sudo apt-get install python3 python3-venv python3-tk fonts-dejavu-core openssh-client adb
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

## Label app (recommended)

```sh
.venv/bin/python labels/label_app.py            # opens http://127.0.0.1:8765
.venv/bin/python labels/label_app.py --dry-run  # practice: writes ZPL to local/dry-run/, never prints
```

On Windows use `.venv/Scripts/python`. The app runs only on this computer (127.0.0.1)
and needs no extra packages. It offers:

- Box, Bag/device and USB strip (2, 3 or 4 rows) editors with a live preview. The
  preview is the exact raster that prints; Print stays disabled until it is current.
- USB text size: Auto-fit, or Fixed px (Small/Medium/Large) for modest text like `32GB`.
  Fixed text is never enlarged and never cropped; you are told if it does not fit.
- Readability warnings below 2.5 mm text height, and text heights per line in mm.
- A confirm step before every send, a "sent N seconds ago, send again?" guard,
  and honest outcomes: Sent, Failed (nothing sent), or Outcome unknown.
- Queue of saved drafts and auto-saved work that survive restarts.
- History with search, Reprint, Edit copy, and "Printed OK / Problem" confirmation.
- Printer host/port settings, a connection test that sends no data, light/dark theme.
- **Photos** view: thumbnails from the phone inbox, **Wait for next photo** (opens it as
  soon as it arrives), a large viewer, and "Label a part / box" which keeps the photo
  beside the editor as a reference. Only the photo's name goes into history.
- Shortcuts: Ctrl+Enter print, Ctrl+S queue, Alt+1/2/3 label type.

Drafts, queue, history and settings live in `local/ui-*.json` (ignored by Git).

## Preview, then print (command line)

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

## USB stick strips

Use the separate strip format for short USB names. It keeps the calibrated
456 x 253 dot sheet and +5 mm offset, with two, three or four horizontal strips.
Supply one name per occupied strip; unused strips stay blank. Dashed horizontal
guides separate strips, and short vertical marks show the trim length.

```sh
.venv/bin/python labels/print_usb_label.py "UBUNTU SRV 26.04" --rows 3 --length-mm 40 --output outputs/usb-ubuntu
```

Add `--font-px 28` for a fixed, modest text size instead of auto-fit, `--rows 4` for
four strips (about 7.9 mm each), and `""` to leave a middle strip blank.

Inspect the PNG and check the usable flat area on the stick before repeating the
same command with `--print`. Four strips are about 7.9 mm high, three about 10.5 mm,
two about 15.8 mm. Four strips at 40 mm were printed and confirmed to fit on 2026-11-22. A photo showed
the sheet sitting high, so strip sheets print 1.25 mm lower than box labels (`^LT50`
instead of `^LT40`); box/bag calibration is unchanged. The lowered sheet is not yet
physically checked; look at the next real USB sheet you print. `--length-mm` accepts 15 to 55 mm, default 40. Each send prints one
full sheet. To save media, supply up to three different names together. Do not
feed manually cut strips back through the printer. This CLI does not inspect USB
devices; identification and Obsidian inventory recording remain agent-assisted.

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

## Phone photos: from camera to label

Photos are the evidence for every component label. The pipeline is hands-off:

```text
Samsung SM-G990U1 camera ──FolderSync instant upload (SFTP, Wi-Fi)──> rdulx009:/srv/lab-photos/inbox
        (normal Camera app)        3-6 s typical, retries every 5 min          (14-day temporary inbox)
                                                                                      │
                     labnet007 / Windows:  lab-photos/photos.py (SSH, read-only) <────┘
                                                   │
                               agent inspects original → label text → label app preview → print
```

### Everyday use

1. Take the photo with the normal Camera app. Nothing else to tap.
2. On the computer, fetch it (use `python` instead of `.venv/bin/python` on Windows):

```sh
.venv/bin/python lab-photos/photos.py wait             # waits for the NEXT photo, then downloads it
.venv/bin/python lab-photos/photos.py latest --max-age 10   # newest, refused if older than 10 min
.venv/bin/python lab-photos/photos.py list             # newest first, JSON
.venv/bin/python lab-photos/photos.py fetch 20261122_154654.jpg
```

   Each prints a local path under `lab-photos/cache/` (disposable, 1 GiB cap).
   Prefer `wait` or `latest --max-age`: plain `latest` can return an old, unrelated photo.
3. Identify or inventory it. In Claude Code (opened in this repo):
   `/identify part` (component, logic board, device model) or
   `/identify box ROBOT CAR KIT` (compare a box photo with its inventory note).
   Both wait for the next photo if you do not name one. Or open it in the label app's
   Photos view and write the label yourself.
4. Nothing else. Photos are disposable working copies: once the box is inventoried or
   the part identified, the photo has done its job. The inbox deletes them automatically.

### Health checks

```sh
.venv/bin/python lab-photos/photos.py status   # server disk use and retention timer
.venv/bin/python lab-photos/photos.py phone    # read-only adb check of the phone (USB debugging on)
```

`phone` verifies: model and Android version, FolderSync installed and not force-stopped,
battery-optimization exemption, instant-sync service running in the foreground,
automatic date/time (filenames are timestamps), and that every camera photo from the
last 13 days is on the server. It changes nothing on the phone. Last run 2026-11-22:
all checks passed, 49 of 49 phone photos present on the server.

### If photos stop arriving

| Symptom | Check |
| --- | --- |
| `wait` times out | Phone on lab Wi-Fi? FolderSync monitoring notification visible? Unlock once after a reboot. Allow up to 5 min for the scheduled retry. |
| `phone` reports service not running | Open FolderSync once; do not force-stop it. Confirm battery setting is "Unrestricted". |
| `Could not reach rdulx009` | Lab network/VPN, `ssh rdulx009` works by itself, key loaded. |
| Uploads fail, server full | `status`; the 12 GiB filesystem is the hard cap, retention trims above 8 GiB. |

Full phone/server configuration and recovery: [configuration](docs/configuration.md) and
[photo intake](docs/photo-inbox.md). Photo access requires your own authorized OpenSSH
alias `rdulx009`; keys are never in this repository. Server provisioning/retention sources
are references, not workstation setup steps; do not run them to test labeling.

The inventory and durable lab context remain in the separate Obsidian repository
`devmjh/lab-context`. Pull that repository on each computer, then read its `AGENTS.md`
and `Inventory/Lab Inventory.md` before resuming. This shares records, procedures and
decisions rather than chat history. These tools do not automatically edit or sync
Obsidian. Identification and inventory updates remain agent-assisted.

## Project contents and provenance

- `labels/label_app.py`, `labels/web/index.html`: local web UI and its small server.
- `labels/print_box_label.py`: calibrated renderer, CLI, GUI and TCP transport.
- `labels/print_usb_label.py`: USB strip renderer and CLI.
- `.claude/`: the `/label` slash command and `lab-label-writer` skill for Claude Code
  (see [commands and skills](docs/claude-code-commands-and-skills.md)).
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
