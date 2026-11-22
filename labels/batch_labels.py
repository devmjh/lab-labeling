"""Portable, preview-first component-label batches."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

from PIL import Image, ImageDraw
from labels import print_box_label as printer


def load_jobs(path):
    jobs = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("Manifest must be a nonempty array of jobs.")
    seen = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("Each job must be an object.")
        identifier = job.get("id", "")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", identifier):
            raise ValueError("IDs must be safe filenames using letters, digits, underscore or hyphen.")
        if identifier in seen:
            raise ValueError("Duplicate job ID: " + identifier)
        seen.add(identifier)
        lines = job.get("lines")
        if not isinstance(lines, list) or not lines or not all(isinstance(x, str) and x.strip() for x in lines):
            raise ValueError("Each job needs nonempty text lines.")
        copies = job.get("copies", 1)
        if type(copies) is not int or not 1 <= copies <= 100:
            raise ValueError("Copies must be an integer from 1 to 100.")
    return jobs


def run_batch(jobs, args):
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    log = output / "sends.jsonl"
    sent = set()
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            sent.add((record["id"], record["fingerprint"]))
    prepared = []
    sheet = Image.new("RGB", (936, ((len(jobs) + 1) // 2) * 285), "#dddddd")
    draw = ImageDraw.Draw(sheet)
    # Validate/render the entire batch before making any printer connections.
    for i, job in enumerate(jobs):
        settings = SimpleNamespace(width=456, height=253, margin=8, border=False,
            font=args.font, offset_mm=5, copies=job.get("copies", 1),
            output=str(output / job["id"]), host=args.host, port=args.port)
        label = printer.save_and_send(job["lines"], settings, send=False)
        x, y = (i % 2) * 468, (i // 2) * 285
        draw.text((x + 8, y + 4), job["id"], fill="black")
        sheet.paste(label.convert("RGB"), (x, y + 22))
        payload = {"zpl": Path(settings.output).with_suffix(".zpl").read_text(),
                   "host": args.host, "port": args.port}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        prepared.append((job, settings, digest))
    sheet.save(output / "previews.png")
    if not args.send:
        return
    for job, settings, digest in prepared:
        if (job["id"], digest) in sent:
            print("Already sent, skipping:", job["id"])
            continue
        printer.save_and_send(job["lines"], settings, send=True)
        with log.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({"id": job["id"], "fingerprint": digest,
                "copies": settings.copies, "status": "sent, physical output unconfirmed"}) + "\n")
        sent.add((job["id"], digest))


def main(allow_print=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", default="outputs/batch")
    parser.add_argument("--host", default=printer.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--font", default=printer.FONT)
    if allow_print:
        parser.add_argument("--print", dest="send", action="store_true")
    else:
        parser.set_defaults(send=False)
    args = parser.parse_args()
    try:
        run_batch(load_jobs(args.manifest), args)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Batch error: {error}\n")
