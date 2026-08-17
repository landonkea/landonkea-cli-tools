#!/usr/bin/env python3
"""
disk_usage.py, Show disk usage for directories.

This script shows how much space files and directories are using,
sorted by size (largest first).

Usage:
    python disk_usage.py [directory] [--top N]

Examples:
    python disk_usage.py .
    python disk_usage.py ~/Downloads --top 10
    python disk_usage.py / --top 5
"""

import argparse
from pathlib import Path

from _shared import format_size, validate_directory


def get_directory_size(path):
    """
    Calculate the total size of a directory by summing every file
    inside it, recursively.

    HOW: Path.rglob("*") walks the directory tree (like `find`), and
    we add up st_size for every entry that is a regular file
    (directories themselves report a size, but it's not meaningful
    disk usage, so it's skipped).

    WHY the broad except: while walking a large tree it's common to
    hit a folder we don't have permission to read (e.g. system
    directories), or one that's been deleted mid-walk. Rather than
    crash the whole scan over one unreadable subfolder, we simply stop
    counting for that branch and return what we've gathered so far.

    Kept as its own function since it's also useful standalone (e.g.
    from a REPL or another script) for "how big is this one directory"
    without the top-N/sibling scanning scan_directory() does.

    Args:
        path (Path): The directory path

    Returns:
        int: Total size in bytes
    """
    total_size = 0

    try:
        for item in path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
    except (PermissionError, OSError):
        # Skip directories we can't access
        pass

    return total_size


def scan_directory(directory, top_n=10):
    """
    Scan a directory and get sizes of the directory itself plus its
    immediate children, sorted largest-first.

    HOW: walks the tree exactly once. An earlier version of this
    function called get_directory_size() on the root (a full recursive
    walk) and then called it again separately for every child
    directory (each its own full recursive walk of that subtree), so
    every file below a first-level subdirectory got stat()'d twice.
    This version computes each immediate child's total once via
    get_directory_size(), then derives the root's total as the sum of
    its children, no repeated walking of the same files.

    Hidden top-level entries (dotfiles/dot-dirs) are excluded from the
    child listing, same as before, but the root's own total still
    includes them, since get_directory_size() never filtered hidden
    entries at any depth and that didn't change here.

    Args:
        directory (str): Path to scan
        top_n (int): Number of top items to show

    Returns:
        list: List of dicts with name, size, path, is_dir, sorted by
            size descending: the root entry plus up to top_n - 1
            children
    """
    dir_path = Path(directory)

    if not validate_directory(dir_path, directory):
        return []

    child_entries = []
    root_total = 0

    try:
        for item in sorted(dir_path.iterdir()):
            try:
                is_dir = item.is_dir()
                size = get_directory_size(item) if is_dir else item.stat().st_size
            except (PermissionError, OSError):
                # Skip items we can't access (e.g. broken symlinks, permission-denied entries)
                continue

            root_total += size

            if not item.name.startswith("."):
                child_entries.append({
                    "name": item.name,
                    "size": size,
                    "path": str(item),
                    "is_dir": is_dir,
                })
    except (PermissionError, OSError):
        # iterdir() itself can fail if we lack permission to list the directory at all
        pass

    results = [{
        "name": directory,
        "size": root_total,
        "path": str(dir_path),
        "is_dir": True,
    }]
    results.extend(child_entries)

    # Sort by size (largest first)
    results.sort(key=lambda x: x["size"], reverse=True)

    # Return top N
    return results[:top_n]


def display_results(results, show_tree=False):
    """
    Display disk usage results as an aligned text table.

    HOW: computes the widest name to align columns, then prints each
    row padded to that width. Directory names get a trailing "/" to
    distinguish them from files at a glance, and long names are
    truncated with "..." so the table doesn't wrap or misalign.

    Args:
        results (list): List of dicts with name, size, path
        show_tree (bool): If True, show as tree structure
    """
    if not results:
        print("No results to display")
        return

    # Calculate max name length for alignment
    max_name = max(len(r["name"]) for r in results)

    # Print header
    print(f"{'Name':<{max_name}}  {'Size':>10}")
    print("-" * (max_name + 12))

    # Print each result
    for r in results:
        # Add a trailing slash for directories
        name = r["name"]
        if r["is_dir"] and not name.endswith("/"):
            name += "/"

        # Truncate long names
        if len(name) > max_name:
            name = name[:max_name - 3] + "..."

        size_str = format_size(r["size"])
        print(f"{name:<{max_name}}  {size_str:>10}")

    # Print total
    print("-" * (max_name + 12))
    total = sum(r["size"] for r in results)
    print(f"{'Total':<{max_name}}  {format_size(total):>10}")


def main():
    """
    Main entry point for disk usage tool.

    HOW: --json bypasses display_results()'s aligned-table formatting and
    dumps the raw list of result dicts instead, mirrors the --json flag
    system_info.py already offers, so both tools can be piped into other
    scripts/`jq` the same way instead of scraping human-formatted text.
    """
    parser = argparse.ArgumentParser(
        description="Show disk usage for directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .                  Show current directory usage
  %(prog)s ~/Downloads        Show Downloads usage
  %(prog)s / --top 5          Show top 5 largest in root
  %(prog)s . --json           Output as JSON
        """
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to analyze (default: current directory)"
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=10,
        help="Number of top items to show (default: 10)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of a text table"
    )

    args = parser.parse_args()

    # Scan and display
    results = scan_directory(args.directory, args.top)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        display_results(results)


if __name__ == "__main__":
    main()
