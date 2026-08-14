# Feature Ideas

Concrete next steps for the five tools in this repo, grouped by which script they'd land in. Everything here follows the patterns already established: stdlib only, `argparse`, `--dry-run`/`--force`/`--quiet`/`--recursive` where they make sense, `--json` for scriptability. Nothing here needs a new dependency.

## file_organizer.py

1. **`--by-date` mode.** Organize into `2026/08/` folders based on file modified time instead of (or alongside) extension. Downloads folders accumulate by time as much as by type, and this is a small addition on top of the existing `scan_directory`/`move_files` split.

2. **Config file for categories.** Right now `CATEGORIES` is a hardcoded dict at the top of the file. Reading an optional `~/.landonkea-cli-tools/categories.json` and merging it over the defaults lets someone add `.psd` to Images or invent a `Fonts` category without touching source.

3. **`--exclude` flag.** A repeatable `--exclude "*.tmp"` (or extension list) so things like partial downloads or lockfiles don't get swept into a category folder.

4. **Real duplicate detection, not just name collision.** Currently a same-named file in the destination gets skipped. Hashing (stdlib `hashlib.sha256`) would let it tell the difference between "this is actually the same file" (safe to skip silently) and "different file, same name" (needs a rename like `report (1).pdf`, the way every OS file manager already handles this).

5. **`organize --history`.** `.organize.log` already exists for `undo`; a small addition reads and summarizes past runs ("Downloads organized 4 times, 212 files moved total, last run 2026-08-10") instead of leaving that data write-only.

## disk_usage.py

6. **`--min-size` threshold.** On a directory with thousands of tiny files, `--top 10` still gets crowded out by noise if there's one huge outlier and nine near-identical small ones. A size floor (`--min-size 10MB`) filters before sorting.

7. **Inline bar chart.** A `[########..] 42%` bar next to each row in `display_results`, sized relative to the largest entry in the results, one column addition to an already-aligned table.

8. **`--exclude` for scan.** Skip `node_modules`, `.git`, `venv` by name during the `rglob`/`iterdir` walk. Right now a `disk_usage .` in a JS project spends most of its time walking a folder nobody wants measured.

9. **Progress feedback on large trees.** `get_directory_size` can take a while walking something like `/`. A simple "scanned N files..." line written to stderr every second or so (no extra dependency, just `time.time()` checks) turns a silent multi-second hang into visible progress.

10. **Snapshot and diff.** `disk_usage . --json > before.json`, do some cleanup, `disk_usage . --json > after.json`, then a new `disk_usage diff before.json after.json` subcommand shows what grew and what shrank. Useful for "did that build step actually clean up after itself."

## text_tools.py

11. **Multi-file support via glob.** `text_tools.py wc "*.py"` running `word_count` over every match and printing a per-file breakdown plus a total, instead of one file per invocation.

12. **Opt-in regex mode.** `replace` and `search` are literal-substring by design (documented and deliberate, per the docstrings). Adding `--regex` as an explicit opt-in on both subcommands keeps the safe default while unlocking pattern matching for people who ask for it.

13. **`-C`/`--context` for search.** Borrowing `grep -C`'s idea: show N lines before and after each match, useful when a bare matching line has no context to judge whether it's the right hit.

14. **`.bak` backup on replace.** Before `replace_in_file` overwrites the file, write the original content to `<file>.bak`. `--dry-run` already exists for previewing; a backup is the safety net for when someone skips it and the replacement wasn't what they meant.

15. **`diff` subcommand.** `text_tools.py diff a.txt b.txt` using stdlib `difflib.unified_diff`, no new dependency, and it's a natural sibling to `wc`/`search`/`replace` since they're all "look at a text file and tell me something" operations.

## system_info.py

16. **`--watch` refresh mode.** Reprint the report every N seconds (clear screen, redraw) for a lightweight `top`-adjacent view, useful for eyeballing load average or free disk space during a long-running task without installing `htop`.

17. **Network section.** Hostname and local IP address (`socket.gethostname()`, `socket.gethostbyname()`, both stdlib) as a new section alongside OS/Python/CPU/Disk, useful when you're SSH'd into something and forget which box you're on.

18. **`--env` flag.** Dump environment variables as their own section (or standalone with `--env`), same idea as the existing `Current Directory` section's `USER`/`HOME` but generalized. Worth defaulting to redacting anything with `KEY`, `TOKEN`, `SECRET`, or `PASSWORD` in the name so it isn't a footgun on a shared screen.

## batch_rename.py

19. **Sequence tokens.** Support a `{n}` (or `{n:03d}` for zero-padding) token in the replacement text that gets substituted with an incrementing counter, so `s/IMG_/vacation_{n:03d}/g` produces `vacation_001.jpg`, `vacation_002.jpg`, and so on, a genuinely common batch-rename need that plain substitution can't do.

20. **Undo support.** `file_organizer.py` already has the `.organize.log` / `undo_organize()` pattern; `batch_rename.py` doing the equivalent (`.rename.log` + `undo` command) is the same idea applied to the other tool that moves/renames things on disk, and it's currently the one file-touching tool in this repo without an undo path.

## Cross-cutting (affects more than one tool)

21. **Shared `~/.landonkea-cli-tools/config.toml`.** One place for defaults like "always quiet" or "default categories," read by whichever tool cares about a given key, ignored by the ones that don't. Keeps each tool's own code simple while removing the need to retype the same flags every time.

22. **`--version` on every tool.** None of the five currently answer `--version`. Once `RELEASING.md`'s tagging scheme is in place, wiring each tool's `--version` output to the current git tag (or a `_version.py` bumped by the release workflow) means `system_info.py --version` actually means something.
