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


def format_size(size_bytes):
    """
    Convert bytes to human-readable format.

    HOW: repeatedly divide by 1024 and move to the next unit (KB, MB,
    GB, TB) until the value is under 1024 or we run out of units. This
    matches binary/1024-based sizing, the convention most file
    browsers and disk tools use.

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


def validate_directory(dir_path, directory):
    """
    Check that the given path exists and is a directory.

    WHY this is split out: scan_directory() needs to bail out early
    with a helpful message in two different invalid-input cases
    (missing path, path is a file not a directory). Isolating the
    check keeps scan_directory() focused on scanning.

    Args:
        dir_path (Path): The resolved Path object to check
        directory (str): The original user-supplied string, used in
            error messages so they match what the user typed

    Returns:
        bool: True if dir_path is a valid, usable directory
    """
    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return False

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return False

    return True


def build_root_entry(directory, dir_path):
    """
    Build the result entry representing the scanned directory itself
    (its total recursive size), so it appears alongside its children
    in the results list.

    Args:
        directory (str): The original user-supplied path string
        dir_path (Path): The resolved Path object

    Returns:
        dict: name, size, path, and is_dir for the root directory
    """
    total_size = get_directory_size(dir_path)
    return {
        "name": directory,
        "size": total_size,
        "path": str(dir_path),
        "is_dir": True,
    }


def scan_children(dir_path):
    """
    Scan the immediate children (not grandchildren) of a directory and
    compute each one's size.

    HOW: iterates only the direct entries via Path.iterdir() (unlike
    get_directory_size, which recurses). For a child that's itself a
    directory, its size is the recursive total of everything inside
    it; for a file, it's just that file's own size.

    WHY hidden files are skipped: dotfiles (.git, .DS_Store, etc.) are
    usually noise for a "what's taking up space" report and clutter
    the output, this mirrors how most GUI file browsers hide them by
    default.

    Args:
        dir_path (Path): The directory whose children to scan

    Returns:
        list: List of dicts with name, size, path, is_dir for each child
    """
    results = []

    try:
        for item in sorted(dir_path.iterdir()):
            if item.name.startswith("."):
                continue

            try:
                if item.is_dir():
                    size = get_directory_size(item)
                else:
                    size = item.stat().st_size

                results.append({
                    "name": item.name,
                    "size": size,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                })
            except (PermissionError, OSError):
                # Skip items we can't access (e.g. broken symlinks, permission-denied entries)
                pass
    except (PermissionError, OSError):
        # iterdir() itself can fail if we lack permission to list the directory at all
        pass

    return results


def scan_directory(directory, top_n=10):
    """
    Scan a directory and get sizes of the directory itself plus its
    immediate children, sorted largest-first.

    HOW: delegates to validate_directory (input checking),
    build_root_entry (the directory's own total size), and
    scan_children (each child's size), then sorts everything together
    and truncates to the requested count.

    Args:
        directory (str): Path to scan
        top_n (int): Number of top items to show

    Returns:
        list: List of dicts with name, size, path
    """
    dir_path = Path(directory)

    if not validate_directory(dir_path, directory):
        return []

    results = [build_root_entry(directory, dir_path)]
    results.extend(scan_children(dir_path))

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
