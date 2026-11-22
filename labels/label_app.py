"""Lab Labels: local web UI for previewing and printing Zebra labels.

    python labels/label_app.py              # opens http://127.0.0.1:8765
    python labels/label_app.py --dry-run    # never opens a printer connection

The browser only edits; this process renders every preview with the same
Pillow code the CLIs use and is the only thing that talks to the printer.
Drafts, queue, history and settings live in local/ (ignored by Git).
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import threading
import uuid
import webbrowser

try:
    from . import print_box_label as box
    from . import print_usb_label as usb
except ImportError:
    import print_box_label as box
    import print_usb_label as usb

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent / "web"
DOTS_PER_MM = 8
READABLE_MIN_DOTS = 20      # about 2.5 mm of cap height
REPEAT_WINDOW_SECONDS = 60

KINDS = {
    "box": {"title": "Box", "copies": 2, "hint": "Lid and side copies"},
    "bag": {"title": "Bag / device", "copies": 1, "hint": "One compact label"},
    "usb": {"title": "USB strips", "copies": 1, "hint": "Cuttable name strips"},
}

DEFAULT_SETTINGS = {"host": box.DEFAULT_HOST, "port": 9100, "offset_mm": 5.0,
                    "font": box.FONT}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    """Small JSON files under local/. Writes are atomic and serialized."""

    def __init__(self, directory):
        self.dir = Path(directory)
        self.lock = threading.Lock()

    def _path(self, name):
        return self.dir / f"ui-{name}.json"

    def read(self, name, default):
        try:
            return json.loads(self._path(name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def write(self, name, value):
        with self.lock:
            self.dir.mkdir(parents=True, exist_ok=True)
            tmp = self._path(name).with_suffix(".tmp")
            tmp.write_text(json.dumps(value, indent=2), encoding="utf-8", newline="\n")
            tmp.replace(self._path(name))

    def update_history(self, entry_id, **changes):
        with self.lock:
            history = self.read("history", [])
            for entry in history:
                if entry["id"] == entry_id:
                    entry.update(changes)
            self.dir.mkdir(parents=True, exist_ok=True)
            tmp = self._path("history").with_suffix(".tmp")
            tmp.write_text(json.dumps(history, indent=2), encoding="utf-8", newline="\n")
            tmp.replace(self._path("history"))
            return next((e for e in history if e["id"] == entry_id), None)

    def append_history(self, entry):
        with self.lock:
            history = self.read("history", [])
            history.insert(0, entry)
            self.dir.mkdir(parents=True, exist_ok=True)
            tmp = self._path("history").with_suffix(".tmp")
            tmp.write_text(json.dumps(history[:500], indent=2), encoding="utf-8", newline="\n")
            tmp.replace(self._path("history"))


def clean_job(raw):
    """Validate and normalise a job dict from the browser."""
    if not isinstance(raw, dict):
        raise ValueError("Job must be an object.")
    kind = raw.get("kind")
    if kind not in KINDS:
        raise ValueError("Unknown label type.")
    copies = raw.get("copies", KINDS[kind]["copies"])
    if type(copies) is not int or not 1 <= copies <= 100:
        raise ValueError("Copies must be a whole number from 1 to 100.")
    job = {"kind": kind, "copies": copies}
    if kind == "usb":
        names = raw.get("names") or []
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            raise ValueError("Strip names must be text.")
        rows = raw.get("rows", 3)
        if rows not in usb.ROW_CHOICES:
            raise ValueError("Choose two, three or four strips.")
        names = [n.strip() for n in names][:rows]
        while names and not names[-1]:
            names.pop()
        length = raw.get("length_mm", 40)
        if not isinstance(length, (int, float)):
            raise ValueError("Strip length must be a number.")
        font_px = raw.get("font_px")
        if font_px is not None and type(font_px) is not int:
            raise ValueError("Text size must be a whole number or auto.")
        job.update(names=names, rows=rows, length_mm=length, font_px=font_px)
    else:
        lines = raw.get("lines") or []
        if not isinstance(lines, list) or not all(isinstance(x, str) for x in lines):
            raise ValueError("Lines must be text.")
        job["lines"] = [x.strip() for x in lines if x.strip()]
    return job


def ink_bands(image, box_=None):
    """Heights (in dots) of separate horizontal runs of black pixels."""
    region = image.crop(box_) if box_ else image
    grey = region.convert("L")
    width = grey.width
    data = grey.tobytes()
    bands, run = [], 0
    for y in range(grey.height):
        row = data[y * width:(y + 1) * width]
        if 0 in row:
            run += 1
        elif run:
            bands.append(run)
            run = 0
    if run:
        bands.append(run)
    return bands


def render_job(job, settings):
    """Return (image, zpl, info) for a cleaned job. Never touches the network."""
    font = settings.get("font") or box.FONT
    warnings, metrics = [], []
    if job["kind"] == "usb":
        image = usb.render_strips(job["names"], job["rows"], job["length_mm"],
                                  font, job["font_px"])
        strip_w = round(job["length_mm"] * DOTS_PER_MM)
        for i in range(job["rows"]):
            name = job["names"][i] if i < len(job["names"]) else ""
            if not name:
                metrics.append({"row": i + 1, "text": "", "height_mm": None})
                continue
            top = round(i * 253 / job["rows"]) + 4
            bottom = round((i + 1) * 253 / job["rows"]) - 4
            bands = ink_bands(image, (0, top + 1, strip_w - 1, bottom - 1))
            h = max(bands) if bands else 0
            metrics.append({"row": i + 1, "text": name, "height_mm": round(h / DOTS_PER_MM, 1)})
            if h < READABLE_MIN_DOTS:
                warnings.append(f"Strip {i + 1} text is only {h / DOTS_PER_MM:.1f} mm tall; "
                                "it may be hard to read. Shorten it or lengthen the strip.")
        used = sum(1 for n in job["names"] if n)
        blank = job["rows"] - used
        summary = (f"1 sheet · {used} named strip{'s' if used != 1 else ''}"
                   + (f" · {blank} blank" if blank else ""))
    else:
        if not job["lines"]:
            raise ValueError("Enter at least one line of text.")
        image = box.render_label(job["lines"], font_path=font)
        bands = ink_bands(image)
        for i, h in enumerate(bands):
            metrics.append({"row": i + 1, "text": job["lines"][i] if i < len(job["lines"]) else "",
                            "height_mm": round(h / DOTS_PER_MM, 1)})
        if len(bands) > 1 and min(bands[1:]) < READABLE_MIN_DOTS:
            warnings.append("Detail text is under 2.5 mm tall. Fewer or shorter lines will read better.")
        if bands and bands[0] < READABLE_MIN_DOTS:
            warnings.append("The heading is under 2.5 mm tall. Shorten it if possible.")
        n = len(job["lines"])
        summary = f"{n} line{'s' if n != 1 else ''}"
    if any("—" in t for t in job.get("lines", []) + job.get("names", [])):
        warnings.append("Contains an em-dash; lab convention is slashes or plain hyphens.")
    copies = job["copies"]
    summary += f" · {copies} cop{'ies' if copies != 1 else 'y'}"
    offset = settings["offset_mm"] + (usb.USB_EXTRA_OFFSET_MM if job["kind"] == "usb" else 0)
    zpl = box.to_zpl(image, offset, copies)
    return image, zpl, {"summary": summary, "warnings": warnings, "metrics": metrics}


def fingerprint(zpl, settings):
    payload = json.dumps({"zpl": zpl, "host": settings["host"], "port": settings["port"]},
                         sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def job_title(job):
    texts = job.get("lines") or [n for n in job.get("names", []) if n]
    return " / ".join(texts[:3]) or "(blank)"


class LabelApp:
    def __init__(self, local_dir, dry_run=False, sender=None):
        self.store = Store(local_dir)
        self.dry_run = dry_run
        self.print_lock = threading.Lock()
        self.sender = sender or self._tcp_send
        self.dry_dir = Path(local_dir) / "dry-run"

    # -- settings ---------------------------------------------------------
    def settings(self):
        merged = dict(DEFAULT_SETTINGS)
        merged.update(self.store.read("settings", {}))
        return merged

    def save_settings(self, raw):
        current = self.settings()
        host = str(raw.get("host", current["host"])).strip()
        port = raw.get("port", current["port"])
        offset = raw.get("offset_mm", current["offset_mm"])
        if not host or len(host) > 253 or any(c.isspace() for c in host):
            raise ValueError("Enter a printer host name or address.")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Port must be 1 to 65535.")
        if not isinstance(offset, (int, float)) or not -15 <= offset <= 15:
            raise ValueError("Vertical offset must be between -15 and 15 mm.")
        saved = {"host": host, "port": port, "offset_mm": float(offset)}
        self.store.write("settings", saved)
        return self.settings()

    # -- rendering --------------------------------------------------------
    def preview(self, raw):
        job = clean_job(raw)
        settings = self.settings()
        image, zpl, info = render_job(job, settings)
        buf = io.BytesIO()
        image.convert("L").save(buf, "PNG")
        return {"job": job, "png": base64.b64encode(buf.getvalue()).decode(),
                "fingerprint": fingerprint(zpl, settings), **info,
                "width": image.width, "height": image.height}

    # -- printing ---------------------------------------------------------
    @staticmethod
    def _tcp_send(host, port, data):
        """Raise ConnectionError if nothing was sent, TimeoutError/OSError if unsure."""
        try:
            conn = socket.create_connection((host, port), timeout=5)
        except OSError as exc:
            raise ConnectionError(f"Could not connect to {host}:{port}: {exc}") from exc
        with conn:
            conn.sendall(data)

    def print_job(self, raw):
        job = clean_job(raw.get("job"))
        settings = self.settings()
        _, zpl, info = render_job(job, settings)
        digest = fingerprint(zpl, settings)
        if raw.get("fingerprint") != digest:
            return 409, {"code": "stale", "error": "The preview is out of date. Review the new preview, then print."}
        if not raw.get("confirm_repeat"):
            for entry in self.store.read("history", [])[:50]:
                if entry["fingerprint"] == digest and entry["status"] in ("sent", "sending", "unknown"):
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(entry["created"])).total_seconds()
                    if age < REPEAT_WINDOW_SECONDS:
                        return 409, {"code": "repeat", "error":
                                     f"This exact label was sent {int(age)} s ago. Send it again?"}
        if not self.print_lock.acquire(blocking=False):
            return 409, {"code": "busy", "error": "Another print is still being sent."}
        try:
            entry = {"id": uuid.uuid4().hex[:12], "created": now(), "job": job,
                     "title": job_title(job), "summary": info["summary"],
                     "host": settings["host"], "port": settings["port"],
                     "fingerprint": digest, "status": "sending",
                     "reprint_of": raw.get("reprint_of"), "physical": None, "error": None}
            self.store.append_history(entry)
            if self.dry_run:
                self.dry_dir.mkdir(parents=True, exist_ok=True)
                (self.dry_dir / f"{entry['id']}.zpl").write_text(zpl, encoding="ascii")
                return 200, self.store.update_history(entry["id"], status="dry-run")
            try:
                self.sender(settings["host"], settings["port"], zpl.encode("ascii"))
            except ConnectionError as exc:
                return 200, self.store.update_history(entry["id"], status="failed", error=str(exc))
            except OSError as exc:
                return 200, self.store.update_history(
                    entry["id"], status="unknown",
                    error=f"Connection broke during sending ({exc}). Check the printer before retrying.")
            return 200, self.store.update_history(entry["id"], status="sent")
        finally:
            self.print_lock.release()

    def check_printer(self):
        settings = self.settings()
        if self.dry_run:
            return {"ok": True, "message": "Dry-run mode: printing writes ZPL files only."}
        try:
            with socket.create_connection((settings["host"], settings["port"]), timeout=3):
                pass
        except OSError as exc:
            return {"ok": False, "message": f"Not reachable: {exc}"}
        return {"ok": True, "message": f"{settings['host']}:{settings['port']} accepted a connection. No data was sent."}


class Handler(BaseHTTPRequestHandler):
    app: LabelApp = None
    server_version = "LabLabels/1"

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    def _host_ok(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return host in ("127.0.0.1", "localhost", "::1")

    def _send(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "Forbidden host"})
        app = self.app
        routes = {
            "/api/config": lambda: {"kinds": KINDS, "settings": app.settings(),
                                    "dry_run": app.dry_run, "rows": list(usb.ROW_CHOICES),
                                    "font_px_range": list(usb.FONT_PX_RANGE)},
            "/api/state": lambda: app.store.read("state", {}),
            "/api/history": lambda: app.store.read("history", []),
        }
        if self.path in routes:
            return self._send(200, routes[self.path]())
        name = "index.html" if self.path in ("/", "/index.html") else None
        if name:
            return self._send(200, (WEB / name).read_bytes(), "text/html; charset=utf-8")
        self._send(404, {"error": "Not found"})

    def do_POST(self):
        # The custom header forces a CORS preflight, which this server never
        # approves, so other websites cannot make the browser print labels.
        if not self._host_ok() or self.headers.get("X-Lab-Labels") != "1":
            return self._send(403, {"error": "Forbidden"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 1_000_000:
                raise ValueError("Request too large.")
            raw = json.loads(self.rfile.read(length) or b"{}")
            app = self.app
            if self.path == "/api/preview":
                return self._send(200, app.preview(raw))
            if self.path == "/api/print":
                return self._send(*app.print_job(raw))
            if self.path == "/api/state":
                app.store.write("state", raw)
                return self._send(200, {"ok": True})
            if self.path == "/api/settings":
                return self._send(200, app.save_settings(raw))
            if self.path == "/api/printer-check":
                return self._send(200, app.check_printer())
            if self.path == "/api/history/confirm":
                entry = app.store.update_history(str(raw.get("id")), physical=raw.get("physical"))
                return self._send(200 if entry else 404, entry or {"error": "Unknown job"})
            self._send(404, {"error": "Not found"})
        except (ValueError, OSError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})


def make_server(app, port=8765):
    handler = type("BoundHandler", (Handler,), {"app": app})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dry-run", action="store_true",
                        help="Never connect to the printer; write ZPL to local/dry-run/.")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--local-dir", default=str(ROOT / "local"))
    args = parser.parse_args()
    server = make_server(LabelApp(args.local_dir, args.dry_run), args.port)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"Lab Labels running at {url}" + ("  (DRY RUN)" if args.dry_run else ""))
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, (url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
