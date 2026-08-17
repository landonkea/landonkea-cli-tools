#!/usr/bin/env python3
"""
_shared.py, Helpers shared by the standalone CLI scripts in this repo.

Not a script itself (leading underscore, no main()), just the bits that
batch_rename.py, disk_usage.py, file_organizer.py, and system_info.py all
needed identically: byte-size formatting and directory-path validation.
"""


def format_size(size_bytes):
    """
    Convert bytes to human-readable format.

    HOW: repeatedly divide by 1024 and move to the next unit (KB, MB,
    GB, TB) until the value is under 1024 or we run out of units. This
    matches binary/1024-based sizing, the convention most file browsers
    and disk tools use.

    Args:
        size_bytes (int): Size in bytes, or None

    Returns:
        str: Human-readable size string ("N/A" if size_bytes is None)

    Examples:
        >>> format_size(0)
        '0 B'
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1048576)
        '1.0 MB'
    """
    if size_bytes is None:
        return "N/A"

    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0

    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1

    return f"{size_bytes:.1f} {units[unit_index]}"


def validate_directory(dir_path, directory):
    """
    Check that the given path exists and is a directory, printing the
    same "Error: ..." message every caller here already expects.

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
