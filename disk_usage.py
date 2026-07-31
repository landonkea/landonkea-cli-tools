#!/usr/bin/env python3
"""
disk_usage.py — Show disk usage for directories.

This script shows how much space files and directories are using,
sorted by size (largest first).

Usage:
    python disk_usage.py [directory] [--top N]

Examples:
    python disk_usage.py .
    python disk_usage.py ~/Downloads --top 10
    python disk_usage.py / --top 5
"""

import os
import sys
import argparse
from pathlib import Path


def format_size(size_bytes):
    """
    Convert bytes to human-readable format.

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
    Calculate the total size of a directory.

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
    Scan a directory and get sizes of subdirectories.

    Args:
        directory (str): Path to scan
        top_n (int): Number of top items to show

    Returns:
        list: List of dicts with name, size, path
    """
    dir_path = Path(directory)
    results = []

    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return results

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return results

    # Get the total size of the directory itself
    total_size = get_directory_size(dir_path)
    results.append({
        "name": directory,
        "size": total_size,
        "path": str(dir_path),
        "is_dir": True,
    })

    # Scan immediate children
    try:
        for item in sorted(dir_path.iterdir()):
            # Skip hidden files
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
                # Skip items we can't access
                pass
    except (PermissionError, OSError):
        pass

    # Sort by size (largest first)
    results.sort(key=lambda x: x["size"], reverse=True)

    # Return top N
    return results[:top_n]


def display_results(results, show_tree=False):
    """
    Display disk usage results.

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
    """
    parser = argparse.ArgumentParser(
        description="Show disk usage for directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .                  Show current directory usage
  %(prog)s ~/Downloads        Show Downloads usage
  %(prog)s / --top 5          Show top 5 largest in root
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

    args = parser.parse_args()

    # Scan and display
    results = scan_directory(args.directory, args.top)
    display_results(results)


if __name__ == "__main__":
    main()
