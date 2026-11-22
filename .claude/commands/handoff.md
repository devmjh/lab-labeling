---
description: Record this session's outcome in the project's Obsidian handoff note, then commit and push lab-context
argument-hint: [project folder under Projects/, default "Lab Labeling"]
allowed-tools: Read, Edit, Bash(git -C ../lab-context:*), Bash(git status:*), Bash(git log:*)
---

Project: **$ARGUMENTS** (if empty, use `Lab Labeling`).

Context gathered before you start (no need to re-run these):
- Code repo: !`git status -sb | head -5`
- Recent code commits: !`git log --oneline -6`
- Vault repo: !`git -C ../lab-context status -sb | head -5`

Steps:
1. `git -C ../lab-context pull --ff-only`. Stop and tell me if it fails.
2. Open `../lab-context/Projects/<project>/<project> - Dev Handoff.md`.
3. Insert a block directly under `## Start here`, newest first:
   `## Status YYYY-MM-DD: <five-word summary>` followed by at most 8 lines:
   what changed (with commit ids), what is verified vs **not** verified,
   decisions made, and the single next step. No chat history, no secrets.
4. If there are more than 3 status blocks, move the oldest ones to the bottom
   under `## Older status` so the top of the note stays short to read.
5. Commit only that note with a clear message and push to `origin main`
   (standing authorization in lab-context AGENTS.md). Show the final
   `git -C ../lab-context status -sb`.
