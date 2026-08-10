#!/usr/bin/env python3
"""
file_organizer.py, Organize files by type into folders.

This script scans a directory and moves files into categorized subfolders
based on their file extension (Documents, Images, Videos, etc.).

Usage:
    python file_organizer.py [directory] [--dry-run] [--force]

Examples:
    python file_organizer.py ~/Downloads
    python file_organize.py ~/Downloads --dry-run
    python file_organize.py ~/Downloads --force
"""

import shutil
import argparse
from pathlib import Path
from datetime import datetime


# CATEGORY DEFINITIONS
# Maps file extensions to folder names.
# Each key is a folder name, each value is a list of extensions.
# NOTE: ".json" intentionally appears in both "Code" and "Data", since
# get_category() returns on the first match found, "Code" wins for
# .json files simply because it's defined earlier in this dict. That's
# a deliberate (if slightly arbitrary) tie-break, not a bug.
CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "Code": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".rb", ".go", ".rs", ".php", ".html", ".css", ".json"],
    "Data": [".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"],
    "Executables": [".exe", ".dmg", ".app", ".deb", ".rpm", ".msi", ".apk"],
}


def get_category(filename):
    """
    Determine the category for a file based on its extension.

    Args:
        filename (str): The name of the file

    Returns:
        str: The category name, or "Other" if no match found

    Example:
        >>> get_category("report.pdf")
        'Documents'
        >>> get_category("photo.jpg")
        'Images'
        >>> get_category("unknown.xyz")
        'Other'
    """
    # Get the file extension (the part after the last dot)
    # Path.suffix returns the extension WITH the dot: ".pdf"
    ext = Path(filename).suffix.lower()

    # Check each category to see if this extension is in its list
    # .items() returns key-value pairs: ("Documents", [".pdf", ...])
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category

    # No match found, put it in "Other"
    return "Other"


def scan_directory(directory, recursive=False):
    """
    Scan a directory for files and return organized info.

    HOW: uses Path.glob() with either "*" (direct children only) or
    "**/*" (every file in every subdirectory) depending on the
    `recursive` flag, then filters out anything we don't want to
    move: subdirectories themselves, hidden/dotfiles, and the tool's
    own log file.

    WHY the log file is excluded by name: without this, a second run
    of the organizer would try to "organize" its own bookkeeping file,
    which would break undo_organize()'s ability to find it later.

    Args:
        directory (str): Path to the directory to scan
        recursive (bool): If True, scan subdirectories too

    Returns:
        list: List of dicts with file info (name, path, category, size)
    """
    results = []
    dir_path = Path(directory)

    # Check if directory exists
    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return results

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return results

    # Use glob to find files
    # "**/*" means "all files in all subdirectories" if recursive=True
    # "*" means "all files in this directory only" if recursive=False
    pattern = "**/*" if recursive else "*"

    for item in dir_path.glob(pattern):
        # Skip directories, we only want files
        if item.is_dir():
            continue

        # Skip hidden files (starting with ".")
        if item.name.startswith("."):
            continue

        # Skip the log file we create
        if item.name == ".organize.log":
            continue

        # Get file info
        results.append({
            "name": item.name,
            "path": str(item),
            "category": get_category(item.name),
            "size": item.stat().st_size,
        })

    return results


def format_size(size_bytes):
    """
    Convert bytes to human-readable format.

    HOW: repeatedly divide by 1024 and move to the next unit until the
    value is small enough, matching how most file browsers display
    sizes.

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Human-readable size string

    Examples:
        >>> format_size(0)
        '0 B'
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1048576)
        '1.0 MB'
    """
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0

    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1

    return f"{size_bytes:.1f} {units[unit_index]}"


def group_files_by_category(files):
    """
    Group a flat list of file-info dicts into a dict keyed by category.

    HOW: builds the groups with a plain dict instead of
    collections.defaultdict, this repo intentionally avoids extra
    imports for something this small.

    Args:
        files (list): List of dicts as returned by scan_directory()

    Returns:
        dict: category name -> list of file-info dicts in that category
    """
    categories = {}
    for f in files:
        cat = f["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)
    return categories


def print_organize_preview(files):
    """
    Print the "Found N files..." breakdown, grouped by category, that
    the user sees before anything is moved. Used for both normal runs
    (before the confirmation prompt) and --dry-run.
    """
    print(f"Found {len(files)} files to organize:")
    print()

    categories = group_files_by_category(files)

    for cat, cat_files in sorted(categories.items()):
        total_size = sum(f["size"] for f in cat_files)
        print(f"  {cat}: {len(cat_files)} files ({format_size(total_size)})")
        for f in cat_files:
            print(f"    - {f['name']} ({format_size(f['size'])})")

    print()
    print(f"Total: {len(files)} files")


def confirm_proceed(force, quiet):
    """
    Ask the user to confirm before moving files, unless --force or
    --quiet was passed.

    WHY force/quiet both skip the prompt: --force is an explicit "I
    already know what I want, don't ask"; --quiet implies the same,
    since there'd be no visible prompt for the user to answer if we
    tried (input() would block forever with no context on screen).

    Args:
        force (bool): If True, skip the prompt and proceed
        quiet (bool): If True, skip the prompt and proceed

    Returns:
        bool: True if the operation should proceed
    """
    if force or quiet:
        return True

    print()
    answer = input("Proceed? (y/n): ").strip().lower()
    if answer not in ("y", "yes"):
        print("Cancelled.")
        return False

    print()
    return True


def move_files(files, directory, quiet):
    """
    Move each file into its category subfolder, skipping duplicates
    and recording every successful move so it can be undone later.

    HOW: for each file, ensures its category folder exists
    (Path.mkdir(exist_ok=True) is a no-op if it's already there), then
    uses shutil.move() to relocate the file. Every successful move is
    appended to log_entries in "from: (new location), to: (old
    location)" form, reversed naming on purpose, since that's exactly
    the shape undo_organize() needs to move things back (see that
    function's docstring).

    WHY duplicates are skipped rather than overwritten: silently
    overwriting a same-named file in the destination folder could
    destroy data with no way to recover it, so we leave both files in
    place and let the user resolve the conflict manually.

    WHY the broad except around shutil.move: a move can fail for many
    OS-level reasons (permissions, disk full, cross-device edge cases)
    that we can't predict in advance; reporting the error and moving
    on to the next file is better than aborting the whole batch.

    Args:
        files (list): List of dicts as returned by scan_directory()
        directory (str): The root directory being organized
        quiet (bool): If True, suppress per-file output

    Returns:
        tuple: (stats dict, log_entries list)
    """
    stats = {"moved": 0, "categories": {}}
    log_entries = []

    for f in files:
        # Create the category directory
        category_dir = Path(directory) / f["category"]
        category_dir.mkdir(exist_ok=True)

        # Build destination path
        destination = category_dir / f["name"]

        # Handle duplicate filenames
        if destination.exists():
            if not quiet:
                print(f"  SKIP: {f['name']} (already exists in {f['category']}/)")
            continue

        try:
            # Move the file
            shutil.move(f["path"], str(destination))

            # Record the move (reversed from/to, see docstring)
            log_entries.append({
                "from": str(destination),
                "to": f["path"],
                "timestamp": datetime.now().isoformat(),
            })

            # Update stats
            stats["moved"] += 1
            if f["category"] not in stats["categories"]:
                stats["categories"][f["category"]] = 0
            stats["categories"][f["category"]] += 1

            if not quiet:
                print(f"  {f['name']} -> {f['category']}/")

        except Exception as e:
            if not quiet:
                print(f"  ERROR: {f['name']}, {e}")

    return stats, log_entries


def write_log(directory, log_entries):
    """
    Persist the list of moves to a hidden log file so undo_organize()
    can reverse them later.

    HOW: writes plain JSON via the standard library (imported locally
    since it's only needed here), no external dependency required for
    something this small.

    Args:
        directory (str): The root directory being organized
        log_entries (list): Entries produced by move_files()
    """
    log_file = Path(directory) / ".organize.log"
    with open(log_file, "w") as file:
        import json
        json.dump(log_entries, file, indent=2)


def print_organize_summary(stats):
    """Print the final "Done! Moved N files." summary with a per-category breakdown."""
    print()
    print(f"Done! Moved {stats['moved']} files.")
    for cat, count in stats["categories"].items():
        print(f"  {cat}: {count} files")


def organize_files(directory, dry_run=False, force=False, recursive=False, quiet=False):
    """
    Organize files in a directory by moving them into category folders.

    HOW: this is the main orchestration function, it scans, shows a
    preview, optionally stops for --dry-run, asks for confirmation
    (unless skipped), then delegates the actual moving and logging to
    move_files()/write_log(), and finally prints a summary.

    Args:
        directory (str): Path to the directory to organize
        dry_run (bool): If True, show what would happen without doing it
        force (bool): If True, skip confirmation prompt
        recursive (bool): If True, scan subdirectories
        quiet (bool): If True, suppress output

    Returns:
        dict: Statistics about what was done
    """
    # Scan the directory
    files = scan_directory(directory, recursive)

    if not files:
        if not quiet:
            print("Nothing to organize, folder is already clean!")
        return {"moved": 0, "categories": {}}

    # Show what would be organized
    if not quiet:
        print_organize_preview(files)

    # If dry run, stop here.
    # NOTE: the returned "moved" count here means "would move", it's
    # a bit of a naming quirk carried over from the original design,
    # but it's what callers (and the CLI output below) rely on.
    if dry_run:
        if not quiet:
            print()
            print("DRY RUN, no files will be moved")
        return {"moved": len(files), "categories": {}}

    # Ask for confirmation (unless --force or --quiet)
    if not confirm_proceed(force, quiet):
        return {"moved": 0, "categories": {}}

    # Move the files and record what happened
    stats, log_entries = move_files(files, directory, quiet)

    # Save log file so the move can be undone later
    write_log(directory, log_entries)

    # Print summary
    if not quiet:
        print_organize_summary(stats)

    return stats


def undo_organize(directory, quiet=False):
    """
    Undo the last organize operation.

    HOW: reads the JSON log written by write_log(), then replays each
    entry's move in reverse, moving from entry["from"] (the category
    subfolder where organize_files() put it) back to entry["to"] (its
    original location). Entries are processed in reverse chronological
    order, which matters if a later organize run reused a filename
    that an earlier run had already claimed.

    Args:
        directory (str): Path to the directory to undo
        quiet (bool): If True, suppress output

    Returns:
        int: Number of files restored
    """
    log_file = Path(directory) / ".organize.log"

    if not log_file.exists():
        if not quiet:
            print("Nothing to undo, no log file found.")
        return 0

    # Read the log file
    import json
    with open(log_file) as f:
        entries = json.load(f)

    if not entries:
        if not quiet:
            print("Nothing to undo, log is empty.")
        return 0

    # Restore files in reverse order
    restored = 0
    for entry in reversed(entries):
        try:
            shutil.move(entry["from"], entry["to"])
            if not quiet:
                print(f"  Restored: {Path(entry['to']).name}")
            restored += 1
        except Exception as e:
            if not quiet:
                print(f"  ERROR: {Path(entry['to']).name}, {e}")

    # Remove the log file
    log_file.unlink()

    if not quiet:
        print()
        print(f"Undo complete! {restored} files restored.")

    return restored


def main():
    """
    Main entry point for the file organizer.

    Parses command-line arguments and calls the appropriate function.
    """
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Organize files by type into folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ~/Downloads              Organize Downloads folder
  %(prog)s ~/Downloads --dry-run    Show what would happen
  %(prog)s ~/Downloads --force      Skip confirmation
  %(prog)s ~/Downloads --recursive  Include subfolders
  %(prog)s ~/Downloads --quiet      No output
  undo ~/Downloads                  Undo last organize
        """
    )

    # Add arguments
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to organize (default: current directory)"
    )
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
        help="Scan subdirectories too"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="organize",
        help="Command to run (default: organize)"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Run the appropriate command
    if args.command == "undo":
        undo_organize(args.directory, args.quiet)
    else:
        organize_files(
            args.directory,
            args.dry_run,
            args.force,
            args.recursive,
            args.quiet
        )


# This is the standard Python idiom for "only run this if executed directly"
# If imported as a module, this code won't run
if __name__ == "__main__":
    main()
