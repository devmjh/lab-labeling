# Verification and next steps

## Consolidation checks, 2026-11-21

- Read the supplied runbook and original source from labnet007; no private recovery
  material retrieved. Photo client, retention and provision scripts imported intact.
- Read live rdulx009 mount, SFTP restriction file and systemd units. Timer active;
  dedicated ext4 mounted with nodev/nosuid/noexec. Client status reports success.
- Live photo list from Windows succeeds. Original full-resolution fetch is checked
  against remote SHA-256 as part of this consolidation.
- Verified original `20261121_162222.jpg` (3,514,793 bytes): local and server SHA-256
  both `5982529b533a16f7a8ff1b4db1d7724aa8800a0f33b0b5a36351d41fbd6f4b4e`.
- Four label tests passed on Windows; three retention tests passed on rdulx009
  against temporary fixtures. `bash -n` passed for the provisioning script.
- Imported retention script matches the installed executable byte-for-byte:
  SHA-256 `f8804678301bc5efc6f22348c9ffb0081deb3d40aee27d25eef4adfe5f171997`.
- Label rendering preserves the calibrated layout. Added `--copies` and `--font`;
  preview remains the default. No physical labels printed during repository setup.
- Regression tests cover raster encoding, calibration/copies, detail hierarchy,
  preview network isolation, retention age/budget/protection and directory scope.
- The existing phone upload, screen-off and offline-recovery tests are historical
  evidence from the supplied runbook, not newly repeated phone tests.

No production provisioning, live retention invocation, inventory edits or phone
settings changes are required to consolidate the repository.

## Known limits

- Photo IDs are filenames; the client returns up to 100 entries, newest server ctime
  first. Latest is not necessarily a new photo for the current request.
- The cache flattens filenames. The configured phone source excludes subfolders;
  support for multiple phones/subfolders should add collision-resistant cache keys.
- Transfer checks file size. Evidence workflows can compare SHA-256 separately.
- An 8 GiB retention target is not a hard upload ceiling; the 12 GiB filesystem is.
- The exact installed FolderSync regex is not recorded. Read it on-device before
  reproducing the pair settings; do not claim an exact configuration export exists.
- HEIC/HEIF retrieval is supported but display depends on the viewing application's
  codec support. JPEG/PNG originals work with the present agent image viewer.
- Existing box names and printed headings are not perfectly identical. No bulk
  rename is authorized; maintain established links until naming is agreed.

## Roadmap toward a full system

1. Read-only inventory validator: YAML/schema checks, duplicate placement candidates,
   broken index links, missing locations, and host status conflicts.
2. Stable box/item identifiers with display names and preserved label history.
3. Photo intake queue with reviewed/identified/assigned states, hashes and selected
   permanent evidence storage outside the expiring inbox.
4. Reviewed inventory edits with change journal and duplicate-safe item moves.
5. Print jobs with preview, explicit copy count, send status and intentional reprints.
6. Search UI over Obsidian notes, without creating a second authoritative database.

These are future features, not claims about functionality already implemented.

## Lab-labeling extraction, 2026-11-22

- Copied all tracked source/support files from lab-inventory commit b9106f9 into the separate lab-labeling repository. No caches, keys, output images or live vault content copied.
- Replaced machine-specific batch helper paths and per-item copy overrides with a portable JSON manifest interface. Full batch rendering precedes printer connections; successful identical jobs are skipped using a local send log.
- Seven tests passed on Windows, including three batch tests; three Linux-only retention tests skipped. Printer connections were mocked. Example batch PNGs and CLI help generated successfully; preview sheet visually inspected.
- No physical label jobs, server provisioning or live retention executed. Linux runtime, GUI and physical printer validation on labnet007 remain pending James testing there.
