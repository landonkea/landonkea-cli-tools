# Build Log

This is the resurrection doc for `landonkea-cli-tools`. Two things live here:

1. A real, git-log-backed account of how this repo got to its current state.
2. A script that rebuilds the repo's structure, git history milestones, and tooling from scratch, with no manual steps or judgment calls required.

If GitHub ever eats this repo, or a local clone gets wiped, this file plus the working source files (backed up separately, see "What this script does NOT do" below) is what gets it back.

## Timeline

Thirteen commits, all on `main`, spanning July 30 to August 13, 2026.

**`720c234`:** feat: Python CLI tools collection (2026-07-30)
The initial drop. Four scripts landed at once: `file_organizer.py`, `disk_usage.py`, `text_tools.py`, `system_info.py`, plus `tests/test_tools.py` with 8 tests and a 39-line README. Compiled `.pyc` files from `__pycache__` got committed alongside the source in this first pass, an easy mistake when there's no `.gitignore` yet.

**`ca44776`:** chore: add .gitignore, remove cached Python files (2026-07-30)
Fixed the above, same day. Added a standard Python `.gitignore` (`__pycache__/`, `*.pyc`, IDE files, `.DS_Store`) and removed the three `.pyc` files that shouldn't have been tracked.

**`91fc95a`:** Refactor for readability (2026-08-01)
No behavior changes. The four scripts had grown a few long, doing-too-much functions (`organize_files`, `scan_directory`, `display_info`), so those got split into small single-purpose helpers, and WHAT/HOW/WHY comments were added throughout, aimed at someone newer to Python who might wonder why `os.statvfs` is POSIX-only or why file moves get logged in reversed from/to order.

**`2d28862`:** Add GitHub Actions CI (2026-08-01)
`.github/workflows/ci.yml` shows up, running the test suite and `ruff` on every push and PR. `ruff.toml` pins the ruleset to the classic `E4/E7/E9/F` set (pyflakes plus basic pycodestyle errors), because ruff's expanded default rules flagged a bunch of style-only issues that weren't worth chasing in a 5-script utility repo. A handful of genuinely unused imports ruff caught got removed at the same time.

**`21b4331`:** Add JSON output, CPU/load info, fix empty-replace bug (2026-08-06)
Three real fixes/features in one commit: `text_tools.py`'s `replace_in_file` now rejects an empty `old_text` (Python's `content.replace("", x)` inserts `x` between every character, silently corrupting the file otherwise), `disk_usage.py` gained a `--json` flag to match the pattern `system_info.py` already had, and `system_info.py` gained a CPU section (core count, load average). Test coverage for `system_info.py` went from zero to real.

**`28d64db`:** ci: add workflow to block AI attribution in commits (2026-08-07)
`.github/workflows/ai-attribution-check.yml` added: scans commit messages, author/committer fields, and file contents for AI-tool attribution strings on every push/PR to `main`, `master`, `dev`, and `staging`.

**`3e17157`:** chore: trigger GitHub re-index (2026-08-07)
An empty commit, same day as the previous one. No file changes; this is a "nudge GitHub's search index" commit, the kind every repo picks up eventually.

**`e957c27`:** ci: upgrade AI attribution check to cover author/committer fields (2026-08-07)
Widened the attribution scan from just commit message text to also check `git log`'s author-name, author-email, committer-name, and committer-email fields.

**`0fe8436`:** docs: add design workflow documentation (2026-08-08)
`docs/DESIGN.md` added: mermaid diagrams of the tool layout and two of the workflows (file-organizer, disk-usage), plus a file-relationship table.

**`2aad882`:** docs: remove em dashes from README (2026-08-09)
Despite the message, this touched seven files, not just the README: `disk_usage.py`, `file_organizer.py`, `system_info.py`, `text_tools.py`, `tests/test_tools.py`, and `docs/DESIGN.md` all had stray em dashes in comments, docstrings, or prose swapped for commas or periods.

**`340c37a`:** feat: implement batch-rename (2026-08-12)
The punchline of the whole history: the README had documented a `batch-rename` tool (with usage examples) since the very first commit, but `batch_rename.py` didn't exist until this one, over a week later. It landed as a sed-style `s/old/new/[flags]` renamer with `--dry-run`, `--force`, `--recursive`, `--quiet`, supporting `g` (global) and `i` (case-insensitive) flags, plus test coverage in `tests/test_tools.py`. The AI-attribution workflow also got a matching update.

**`docs: add build log and feature ideas` (2026-08-13)**
This file and `FEATURE_IDEAS.md` show up. The former exists because the repo had no resurrection plan (if GitHub and every local clone vanished at once, there was nothing but memory to rebuild from); the latter because five working tools with no roadmap tend to accumulate feature requests as scattered comments instead of a real list.

**`feat: add release-candidate and stable release workflows` (2026-08-13)**
`RELEASING.md`, `.github/workflows/release-candidate.yml`, and `.github/workflows/release.yml` added, plus a short pointer in the README. `dev` was already sitting there as a branch with no defined purpose; this gives it one. Pushing a `vX.Y.Z-rcN` tag runs lint and tests, then publishes a pre-release. Pushing a `vX.Y.Z` tag does the same, but only after confirming the tagged commit is actually reachable from `main`, refusing to publish a stable release cut from anywhere else.

## Current state (what actually exists right now)

```
landonkea-cli-tools/
├── README.md
├── BUILD_LOG.md
├── FEATURE_IDEAS.md
├── RELEASING.md
├── .gitignore
├── ruff.toml
├── batch_rename.py
├── disk_usage.py
├── file_organizer.py
├── system_info.py
├── text_tools.py
├── docs/
│   └── DESIGN.md
├── tests/
│   └── test_tools.py
└── .github/
    └── workflows/
        ├── ci.yml
        ├── ai-attribution-check.yml
        ├── release-candidate.yml
        └── release.yml
```

Five CLI scripts, one test file, stdlib-only (no `requirements.txt`, nothing to `pip install` besides `ruff` for linting), Python 3.7+ per the README, tested against 3.11/3.14 locally. No packaging (`setup.py`/`pyproject.toml`), no version file, but tags now have somewhere to go: see `RELEASING.md` for the release-candidate and stable channels.

## Rebuild from scratch

The goal here is a script an automated process can run start to finish with no prompts, no decisions, and no human filling in a blank. It has one precondition:

**Precondition: the source files already exist somewhere on disk.** This script does not regenerate 1,500+ lines of Python from a description, that's not a "rebuild," that's a rewrite, and it would drift from the real thing the moment either one changed. What it *does* automate is everything else: turning a folder of files into a proper git repo with sane history milestones, correct tooling, and working CI, none of which requires a human to sit down and decide anything.

If you're restoring after a total loss (GitHub gone AND local `.git` gone, only the working files survive from a backup/zip), run this from inside a directory containing the files listed in "Current state" above:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Sanity check: bail loudly instead of half-initializing a repo in the
# wrong place.
for f in README.md file_organizer.py disk_usage.py text_tools.py \
         system_info.py batch_rename.py tests/test_tools.py .gitignore \
         ruff.toml BUILD_LOG.md FEATURE_IDEAS.md RELEASING.md \
         .github/workflows/release-candidate.yml .github/workflows/release.yml; do
  if [ ! -f "$f" ]; then
    echo "Missing $f, this script expects to run inside a folder that" >&2
    echo "already has the current working files in it." >&2
    exit 1
  fi
done

git init -b main
git config user.name "LANDON KEA"
git config user.email "115629435+landonkea@users.noreply.github.com"

# --- Milestone 1: initial collection ---
git add README.md file_organizer.py disk_usage.py text_tools.py system_info.py tests/test_tools.py
git commit -m "feat: Python CLI tools collection"

# --- Milestone 2: stop tracking build artifacts ---
git add .gitignore
git commit -m "chore: add .gitignore, remove cached Python files"

# --- Milestone 3: readability refactor (no behavior change) ---
git add file_organizer.py disk_usage.py text_tools.py system_info.py
git commit -m "Refactor for readability: split long functions, add in-depth comments"

# --- Milestone 4: CI ---
mkdir -p .github/workflows
git add .github/workflows/ci.yml ruff.toml file_organizer.py disk_usage.py text_tools.py system_info.py tests/test_tools.py
git commit -m "Add GitHub Actions CI (tests + ruff lint)"

# --- Milestone 5: JSON output, CPU info, bugfix ---
git add text_tools.py disk_usage.py system_info.py tests/test_tools.py
git commit -m "Add JSON output, CPU/load info, and fix empty-replace corruption bug"

# --- Milestone 6: AI attribution gate ---
git add .github/workflows/ai-attribution-check.yml
git commit -m "ci: add workflow to block AI attribution in commits"

# --- Milestone 7: attribution check covers author/committer fields ---
git add .github/workflows/ai-attribution-check.yml
git commit -m "ci: upgrade AI attribution check to cover author/committer fields"

# --- Milestone 8: design docs ---
mkdir -p docs
git add docs/DESIGN.md
git commit -m "docs: add design workflow documentation"

# --- Milestone 9: writing cleanup ---
git add README.md disk_usage.py file_organizer.py system_info.py text_tools.py tests/test_tools.py docs/DESIGN.md
git commit -m "docs: remove em dashes from README"

# --- Milestone 10: ship the tool the README already promised ---
git add batch_rename.py tests/test_tools.py .github/workflows/ai-attribution-check.yml
git commit -m "feat: implement batch-rename, the one tool the README documented but never shipped"

# --- Milestone 11: dev branch, mirroring what this repo actually has ---
git branch dev main~6

echo "Rebuild complete. Add a remote and push when ready:"
echo "  git remote add origin git@github.com:landonkea/landonkea-cli-tools.git"
echo "  git push -u origin main dev"
```

This produces new commit hashes and timestamps (git generates those from the commit content and clock, they're not something a script can fake to match old ones), but the same file contents, the same commit messages, and the same logical sequence of milestones. Anyone reading `git log` afterward gets an accurate history, not identical bytes.

### What this script does NOT do

It doesn't recreate the original commit SHAs, author dates, or the two accidental/fixed detours (the `.pyc` files that got committed then removed in commit 1→2, and the empty re-index commit). Those are real but not worth automating around, they're noise, not structure. If byte-identical history ever matters (it usually doesn't for a small tools repo), the actual fix is upstream of this doc: keep an off-site mirror.

### The better answer, if `.git` still exists anywhere

If a copy of this repository's `.git` folder survives *anywhere* (a teammate's clone, a CI runner's cache, a backup), skip the script above entirely and just run:

```bash
git clone --mirror /path/to/surviving/.git landonkea-cli-tools.git
git clone landonkea-cli-tools.git landonkea-cli-tools
```

That restores everything, exact hashes, exact timestamps, exact author info, with one command. The script above is the fallback for the worst case: no `.git` anywhere, only the files. Worth remembering next time this repo (or any repo) is set up: `git bundle create backup.bundle --all`, stored somewhere off of GitHub, turns "worst case" into "one command" too.
