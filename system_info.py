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
from pathlib import Path


def get_os_info():
    """
    Get operating system information.

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
            "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
        }
    except (OSError, AttributeError):
        return None


def format_size(size_bytes):
    """
    Convert bytes to human-readable format.

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


def display_info():
    """
    Display all system information.
    """
    print("=" * 50)
    print("SYSTEM INFORMATION")
    print("=" * 50)
    print()

    # OS Info
    os_info = get_os_info()
    print("Operating System:")
    print(f"  System:    {os_info['system']}")
    print(f"  Release:   {os_info['release']}")
    print(f"  Version:   {os_info['version']}")
    print(f"  Machine:   {os_info['machine']}")
    print(f"  Processor: {os_info['processor']}")
    print()

    # Python Info
    py_info = get_python_info()
    print("Python:")
    print(f"  Version:      {py_info['version']}")
    print(f"  Compiler:     {py_info['compiler']}")
    print(f"  Implementation: {py_info['implementation']}")
    print(f"  Executable:   {py_info['executable']}")
    print()

    # Disk Info
    disk_info = get_disk_info()
    if disk_info:
        print("Disk Usage:")
        print(f"  Total:     {format_size(disk_info['total'])}")
        print(f"  Used:      {format_size(disk_info['used'])}")
        print(f"  Free:      {format_size(disk_info['free'])}")
        print(f"  Used %:    {disk_info['percent_used']}%")
    else:
        print("Disk Usage: Unable to determine")
    print()

    # Current Directory
    print("Current Directory:")
    print(f"  Path:      {os.getcwd()}")
    print(f"  User:      {os.getenv('USER', 'N/A')}")
    print(f"  Home:      {os.getenv('HOME', 'N/A')}")
    print()

    print("=" * 50)


def get_info_dict():
    """
    Get all system information as a dictionary.

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
