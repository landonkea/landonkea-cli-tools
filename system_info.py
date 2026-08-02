#!/usr/bin/env python3
"""
system_info.py — Display system information.

Shows operating system, CPU, memory, disk, and Python information.

Usage:
    python system_info.py [--json]

Examples:
    python system_info.py
    python system_info.py --json
"""

import os
import sys
import platform
import argparse


def get_os_info():
    """
    Get operating system information.

    HOW: Everything here comes from the standard library's `platform`
    module, which reads values the OS itself exposes (via uname() on
    POSIX systems, or the Windows API on Windows) — there's no manual
    detection logic needed.

    WHY `processor() or "N/A"`: on some platforms (notably macOS and
    Linux in certain configurations) platform.processor() returns an
    empty string instead of raising an error, so we fall back to a
    friendlier placeholder rather than printing nothing.

    Returns:
        dict: OS information
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor() or "N/A",
        "platform": platform.platform(),
    }


def get_python_info():
    """
    Get Python interpreter information.

    HOW: `sys.executable` gives the absolute path to the Python binary
    currently running this script, which is useful for confirming
    which interpreter (e.g. a virtualenv vs. system Python) is in use.

    Returns:
        dict: Python information
    """
    return {
        "version": platform.python_version(),
        "compiler": platform.python_compiler(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
    }


def get_disk_info(path="."):
    """
    Get disk usage information for a path.

    HOW: os.statvfs() is a POSIX system call that reports filesystem
    block counts. Multiplying block counts by the block size (f_frsize)
    converts them into bytes.

    WHY os.statvfs and not something simpler: it's part of the standard
    library and needs no extra dependency, but it only exists on
    POSIX systems (macOS/Linux) — Windows doesn't implement it. The
    except clause catches AttributeError so the script degrades
    gracefully (returns None) instead of crashing on Windows, and
    OSError covers cases like the path not existing or being
    inaccessible.

    Args:
        path (str): Path to check

    Returns:
        dict: Disk information
    """
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free

        return {
            "total": total,
            "used": used,
            "free": free,
            # Guard against dividing by zero on a filesystem report of 0 total blocks
            "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
        }
    except (OSError, AttributeError):
        return None


def format_size(size_bytes):
    """
    Convert bytes to human-readable format.

    HOW: repeatedly divide by 1024 and move to the next unit (KB, MB,
    GB, TB) until the value is under 1024 or we run out of units. This
    mirrors how most OS file browsers display sizes (binary/1024-based
    units, not decimal/1000-based "SI" units).

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Human-readable size string
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


def print_os_section(os_info):
    """Print the "Operating System" block of the human-readable report."""
    print("Operating System:")
    print(f"  System:    {os_info['system']}")
    print(f"  Release:   {os_info['release']}")
    print(f"  Version:   {os_info['version']}")
    print(f"  Machine:   {os_info['machine']}")
    print(f"  Processor: {os_info['processor']}")
    print()


def print_python_section(py_info):
    """Print the "Python" block of the human-readable report."""
    print("Python:")
    print(f"  Version:      {py_info['version']}")
    print(f"  Compiler:     {py_info['compiler']}")
    print(f"  Implementation: {py_info['implementation']}")
    print(f"  Executable:   {py_info['executable']}")
    print()


def print_disk_section(disk_info):
    """
    Print the "Disk Usage" block of the human-readable report.

    WHY the None check: get_disk_info() returns None on platforms/paths
    where statvfs isn't available (see get_disk_info), so this section
    needs a fallback message instead of crashing on a None dict.
    """
    if disk_info:
        print("Disk Usage:")
        print(f"  Total:     {format_size(disk_info['total'])}")
        print(f"  Used:      {format_size(disk_info['used'])}")
        print(f"  Free:      {format_size(disk_info['free'])}")
        print(f"  Used %:    {disk_info['percent_used']}%")
    else:
        print("Disk Usage: Unable to determine")
    print()


def print_current_dir_section():
    """
    Print the "Current Directory" block of the human-readable report.

    WHY os.getenv with a default: USER/HOME are environment variables
    set by the shell, not guaranteed to exist in every environment
    (e.g. some minimal containers), so we fall back to "N/A" instead
    of letting a missing variable produce "None" in the output.
    """
    print("Current Directory:")
    print(f"  Path:      {os.getcwd()}")
    print(f"  User:      {os.getenv('USER', 'N/A')}")
    print(f"  Home:      {os.getenv('HOME', 'N/A')}")
    print()


def display_info():
    """
    Display all system information as a human-readable report.

    HOW: gathers each section's data, then delegates the actual
    printing to small per-section helpers so each piece of formatting
    logic stays easy to read and change independently.
    """
    print("=" * 50)
    print("SYSTEM INFORMATION")
    print("=" * 50)
    print()

    print_os_section(get_os_info())
    print_python_section(get_python_info())
    print_disk_section(get_disk_info())
    print_current_dir_section()

    print("=" * 50)


def get_info_dict():
    """
    Get all system information as a dictionary.

    WHY this exists separately from display_info(): the --json output
    mode needs the raw data structure rather than pre-formatted text,
    so this function reuses the same getters without any print calls.

    Returns:
        dict: All system information
    """
    return {
        "os": get_os_info(),
        "python": get_python_info(),
        "disk": get_disk_info(),
        "current_dir": os.getcwd(),
        "user": os.getenv("USER"),
        "home": os.getenv("HOME"),
    }


def main():
    """
    Main entry point for system info tool.

    HOW: argparse handles the single --json flag; based on it we either
    print the formatted human report or dump JSON (importing `json`
    lazily here since it's only needed for that one branch).
    """
    parser = argparse.ArgumentParser(
        description="Display system information"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if args.json:
        import json
        print(json.dumps(get_info_dict(), indent=2))
    else:
        display_info()


if __name__ == "__main__":
    main()
