#!/usr/bin/env python3
"""
batch_rename.py, Rename multiple files with a sed-style pattern.

Usage:
    python batch_rename.py <pattern> <directory> [--dry-run] [--force] [--recursive]

Pattern:
    A sed-style substitution: s/old/new/[flags]
    - old/new are treated as literal text by default, not regex, so
      characters like "." or "(" in a filename match themselves.
    - Append "g" to replace every occurrence in a filename, not just
      the first (e.g. s/a/b/g on "banana.txt" -> "bbnbnb.txt").
    - Append "i" for case-insensitive matching.

Examples:
    python batch_rename.py "s/old/new/" ~/Photos
    python batch_rename.py "s/IMG_/vacation_/g" ~/Photos --dry-run
    python batch_rename.py "s/jpeg/jpg/i" ~/Photos --force
"""

import argparse
import re
from pathlib import Path


def parse_pattern(pattern):
    """
    Parse a sed-style "s/old/new/[flags]" string into (old, new, flags).

    HOW: sed uses "/" as the field separator between the three parts,
    but "/" could also appear inside old/new themselves (e.g. renaming
    something that contains a literal slash isn't realistic for a
    filename, but a defensive parser shouldn't assume that). Splitting
    on "/" naively would break on an escaped "\\/" inside old/new, so
    this only supports the common case (no escaped separators), which
    matches every example in this file's own docstring and the
    project README, rather than building a full sed-pattern parser for
    a filename-renaming tool.

    WHY require the "s/old/new/" shape instead of just taking two
    separate old/new arguments: the README documents this exact
    single-argument sed-style form (`"s/old/new/"`), matching what
    someone who already knows basic sed would expect.

    Args:
        pattern (str): A string like "s/old/new/" or "s/old/new/gi"

    Returns:
        tuple: (old, new, flags) where flags is a string (possibly
            empty) containing any of "g"/"i"

    Raises:
        ValueError: if pattern isn't a valid "s/old/new/[flags]" string
    """
    match = re.match(r"^s/((?:[^/]|\\/)*)/((?:[^/]|\\/)*)/([a-z]*)$", pattern)
    if not match:
        raise ValueError(
            f"Invalid pattern '{pattern}', expected sed-style 's/old/new/' "
            f"or 's/old/new/flags' (supported flags: g, i)"
        )

    old, new, flags = match.groups()
    # Unescape "\/" back to a literal "/", the one escape this parser
    # supports (see HOW above).
    old = old.replace("\\/", "/")
    new = new.replace("\\/", "/")

    unknown_flags = set(flags) - {"g", "i"}
    if unknown_flags:
        raise ValueError(
            f"Unknown flag(s) '{''.join(sorted(unknown_flags))}' in pattern "
            f"'{pattern}', supported flags are 'g' and 'i'"
        )

    if old == "":
        # Same bug class text_tools.replace_in_file() guards against:
        # an empty "old" would match "between every character" once
        # compiled as a regex, silently corrupting every filename it
        # touches instead of doing anything meaningful.
        raise ValueError("old text in pattern cannot be empty")

    return old, new, flags


def compute_new_name(filename, old, new, flags):
    """
    Apply a parsed (old, new, flags) substitution to one filename.

    HOW: old/new are literal text (see parse_pattern's docstring), so
    old is escaped with re.escape() before being compiled as a regex,
    that's what lets flags like "i" (case-insensitive) be layered on
    top via Python's re module without old itself being interpreted as
    a regex pattern. "g" maps to re.sub's default (replace every
    match); its absence maps to count=1 (first match only), mirroring
    sed's own g-flag semantics.

    Args:
        filename (str): Original filename (not full path)
        old (str): Literal text to find
        new (str): Literal text to replace it with
        flags (str): Parsed flags, may contain "g" and/or "i"

    Returns:
        str: The new filename, unchanged if `old` wasn't found
    """
    re_flags = re.IGNORECASE if "i" in flags else 0
    count = 0 if "g" in flags else 1
    return re.sub(re.escape(old), new.replace("\\", "\\\\"), filename, count=count, flags=re_flags)
    # new.replace("\\", "\\\\") guards against re.sub treating a literal
    # backslash in `new` as the start of a backreference (e.g. "\1"),
    # `new` is meant to be inserted as-is, not interpreted.


def scan_renames(directory, pattern, recursive=False):
    """
    Find every file in `directory` whose name matches `pattern`, and
    compute what it would be renamed to.

    HOW: only filenames (not full paths) are matched against the
    pattern, matching sed's line-oriented model applied to "one name
    at a time" here, and matching what file_organizer.py's own
    get_category() does (extension/name-based, not path-based).

    Args:
        directory (str): Directory to scan
        pattern (str): A "s/old/new/[flags]" string
        recursive (bool): If True, also scan subdirectories

    Returns:
        list: dicts with keys "old_path" (Path), "new_path" (Path),
            only for files where the pattern actually changed the name

    Raises:
        ValueError: if pattern is invalid (propagated from parse_pattern)
    """
    old, new, flags = parse_pattern(pattern)

    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return []
    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return []

    entries = dir_path.rglob("*") if recursive else dir_path.iterdir()

    renames = []
    for entry in entries:
        if not entry.is_file():
            continue

        new_name = compute_new_name(entry.name, old, new, flags)
        if new_name == entry.name:
            # Pattern didn't match this filename, nothing to rename.
            continue

        renames.append({
            "old_path": entry,
            "new_path": entry.with_name(new_name),
        })

    return renames


def apply_renames(renames, quiet=False):
    """
    Actually perform a list of renames computed by scan_renames().

    HOW: checks each destination for a collision right before renaming
    (not just once up front), a second matched file could collide with
    a destination created earlier in this same batch, iterating in
    order means each check sees the real, current filesystem state.

    WHY skip-and-warn on collision rather than overwriting: silently
    replacing an existing file because two names happened to collide
    under this pattern is much more likely to be a program bug or an
    unexpected input than something the user actually wanted.

    Args:
        renames (list): Output of scan_renames()
        quiet (bool): If True, suppress per-file progress lines

    Returns:
        int: Number of files actually renamed
    """
    renamed = 0
    for entry in renames:
        old_path, new_path = entry["old_path"], entry["new_path"]

        if new_path.exists():
            print(f"  Skipped {old_path.name}: '{new_path.name}' already exists")
            continue

        old_path.rename(new_path)
        renamed += 1
        if not quiet:
            print(f"  {old_path.name} -> {new_path.name}")

    return renamed


def confirm_proceed(force, quiet):
    """
    Ask the user to confirm before renaming files, unless --force or
    --quiet was passed. Mirrors file_organizer.py's confirm_proceed():
    --force is an explicit "I already know what this will do", --quiet
    is for scripted/non-interactive use where a prompt would hang.

    Args:
        force (bool): If True, skip the prompt and proceed
        quiet (bool): If True, skip the prompt and proceed

    Returns:
        bool: True if renaming should proceed
    """
    if force or quiet:
        return True

    response = input("Proceed with renaming? [y/N] ").strip().lower()
    return response in ("y", "yes")


def rename_files(directory, pattern, dry_run=False, force=False, recursive=False, quiet=False):
    """
    Full batch-rename flow: scan for matches, preview, optionally stop
    for --dry-run, ask for confirmation, then rename.

    Args:
        directory (str): Directory to scan
        pattern (str): A "s/old/new/[flags]" string
        dry_run (bool): If True, show what would happen without doing it
        force (bool): If True, skip confirmation prompt
        recursive (bool): If True, also scan subdirectories
        quiet (bool): If True, suppress non-essential output

    Returns:
        dict: {"matched": int, "renamed": int}
    """
    try:
        renames = scan_renames(directory, pattern, recursive)
    except ValueError as e:
        print(f"Error: {e}")
        return {"matched": 0, "renamed": 0}

    if not renames:
        if not quiet:
            print("No files matched.")
        return {"matched": 0, "renamed": 0}

    if not quiet:
        print(f"{len(renames)} file(s) would be renamed:")
        for entry in renames:
            print(f"  {entry['old_path'].name} -> {entry['new_path'].name}")

    if dry_run:
        return {"matched": len(renames), "renamed": 0}

    if not confirm_proceed(force, quiet):
        print("Aborted.")
        return {"matched": len(renames), "renamed": 0}

    renamed = apply_renames(renames, quiet)

    if not quiet:
        print(f"Renamed {renamed} of {len(renames)} file(s).")

    return {"matched": len(renames), "renamed": renamed}


def build_arg_parser():
    """Build the argparse parser for batch_rename.py's CLI."""
    parser = argparse.ArgumentParser(
        description="Rename multiple files with a sed-style pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "s/old/new/" ~/Photos
  %(prog)s "s/IMG_/vacation_/g" ~/Photos --dry-run
  %(prog)s "s/jpeg/jpg/i" ~/Photos --force
        """
    )
    parser.add_argument("pattern", help="Sed-style pattern, e.g. s/old/new/")
    parser.add_argument("directory", help="Directory containing files to rename")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without doing it"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Also rename files in subdirectories"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output"
    )
    return parser


def main():
    """Main entry point for batch_rename.py."""
    parser = build_arg_parser()
    args = parser.parse_args()

    rename_files(
        args.directory,
        args.pattern,
        dry_run=args.dry_run,
        force=args.force,
        recursive=args.recursive,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
