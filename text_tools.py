#!/usr/bin/env python3
"""
text_tools.py, Text processing utilities.

Provides common text operations like word count, line count,
character count, and search.

Usage:
    python text_tools.py <command> [file] [options]

Commands:
    wc          Word count, line count, character count
    search      Search for text in a file
    replace     Replace text in a file

Examples:
    python text_tools.py wc README.md
    python text_tools.py search README.md "hello"
    python text_tools.py replace README.md "old" "new"
"""

import argparse
from pathlib import Path


def word_count(filename):
    """
    Count words, lines, and characters in a file.

    HOW: reads the whole file into memory, then relies on str.split()
    for both the line and word counts. `content.split("\\n")` splits
    strictly on newline characters; `content.split()` (no argument)
    splits on any run of whitespace, which is Python's idiomatic way
    to count "words" without writing custom parsing.

    WHY read the whole file rather than stream it: these files are
    expected to be small utility-script-sized text files, so simplicity
    wins over the memory efficiency of a line-by-line read.

    Args:
        filename (str): Path to the file

    Returns:
        dict: Statistics about the file
    """
    path = Path(filename)

    if not path.exists():
        print(f"Error: File '{filename}' does not exist")
        return None

    if not path.is_file():
        print(f"Error: '{filename}' is not a file")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # File might be binary
        print(f"Error: '{filename}' appears to be a binary file")
        return None

    lines = content.split("\n")
    words = content.split()
    chars = len(content)

    return {
        "lines": len(lines),
        "words": len(words),
        "chars": chars,
        "bytes": path.stat().st_size,
    }


def search_file(filename, pattern, ignore_case=False, line_numbers=True):
    """
    Search for text in a file, returning every line that contains the
    given substring.

    HOW: iterates the file line by line with enumerate(f, 1) so
    line_num naturally starts at 1 (matching how line numbers are
    normally displayed to humans, unlike Python's 0-based indexing).
    For case-insensitive search, both the line and the pattern are
    lowercased before comparing, lowercasing both sides is what makes
    the comparison case-insensitive, rather than needing a separate
    case-insensitive string method.

    WHY line-by-line here (unlike word_count, which reads it all at
    once): a search only needs to look at one line at a time, so
    streaming avoids holding the whole file in memory for potentially
    large files.

    Args:
        filename (str): Path to the file
        pattern (str): Text to search for
        ignore_case (bool): If True, ignore case when searching
        line_numbers (bool): If True, show line numbers

    Returns:
        list: List of matching lines
    """
    path = Path(filename)

    if not path.exists():
        print(f"Error: File '{filename}' does not exist")
        return []

    matches = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Check if pattern is in the line
                line_to_check = line.lower() if ignore_case else line
                pattern_to_check = pattern.lower() if ignore_case else pattern

                if pattern_to_check in line_to_check:
                    matches.append({
                        "line_num": line_num,
                        # rstrip only the trailing newline so we don't also
                        # strip meaningful trailing spaces from the line
                        "line": line.rstrip("\n"),
                    })
    except UnicodeDecodeError:
        print(f"Error: '{filename}' appears to be a binary file")
        return []

    return matches


def replace_in_file(filename, old_text, new_text, dry_run=False):
    """
    Replace all occurrences of a substring in a file.

    HOW: str.count() first tells us how many replacements *would*
    happen, which lets us report that number and (in dry-run mode)
    preview affected lines without touching the file at all. The
    actual replacement uses str.replace(), which is a plain literal
    substring replacement, not a regular expression, so characters
    like "." or "*" in old_text are matched exactly, not as patterns.

    WHY read-then-write instead of editing in place: Python has no
    built-in "find and replace in a file", the straightforward way is
    to read the full content, transform the string in memory, then
    overwrite the file with the new content.

    Args:
        filename (str): Path to the file
        old_text (str): Text to find
        new_text (str): Text to replace with
        dry_run (bool): If True, show what would happen without doing it

    Returns:
        int: Number of replacements made
    """
    path = Path(filename)

    if not path.exists():
        print(f"Error: File '{filename}' does not exist")
        return 0

    # BUG GUARD: an empty old_text is a real edge case, not a hypothetical
    # one, "".count(...) matches "between every character", so
    # content.replace("", new_text) would insert new_text before, after,
    # and between every single character in the file (e.g. "ab" ->
    # "XaXbX"). That's not a meaningful "replace" and would silently
    # corrupt the file, so it's rejected up front instead.
    if old_text == "":
        print("Error: old_text cannot be empty")
        return 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Error: '{filename}' appears to be a binary file")
        return 0

    # Count occurrences
    count = content.count(old_text)

    if count == 0:
        print(f"No occurrences of '{old_text}' found")
        return 0

    # Show what would be replaced
    print(f"Found {count} occurrence(s) of '{old_text}'")

    if dry_run:
        # Show the lines that would be changed
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if old_text in line:
                print(f"  Line {i}: {line}")
        return count

    # Do the replacement
    new_content = content.replace(old_text, new_text)

    # Write back
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Replaced {count} occurrence(s)")
    return count


def run_wc_command(args):
    """Handle the `wc` subcommand: print line/word/char/byte counts."""
    stats = word_count(args.file)
    if stats:
        print(f"  {stats['lines']:>6} lines")
        print(f"  {stats['words']:>6} words")
        print(f"  {stats['chars']:>6} characters")
        print(f"  {stats['bytes']:>6} bytes")


def run_search_command(args):
    """Handle the `search` subcommand: print each matching line, prefixed with its line number."""
    matches = search_file(args.file, args.pattern, args.ignore_case)
    if matches:
        for m in matches:
            print(f"{m['line_num']:>4}: {m['line']}")
    else:
        print("No matches found")


def run_replace_command(args):
    """Handle the `replace` subcommand: perform (or preview) the substitution."""
    replace_in_file(args.file, args.old, args.new, args.dry_run)


def build_arg_parser():
    """
    Build the argparse parser and its `wc` / `search` / `replace`
    subcommands.

    WHY subparsers: each command takes a different set of arguments
    (wc needs just a file; search needs a file + pattern + optional
    flag; replace needs a file + old + new + optional flag), and
    argparse's subparsers give each its own isolated argument set and
    its own --help text, rather than one big parser trying to validate
    all combinations at once.

    Returns:
        argparse.ArgumentParser: the configured parser
    """
    parser = argparse.ArgumentParser(
        description="Text processing utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  %(prog)s wc <file>                    Count words, lines, characters
  %(prog)s search <file> <pattern>      Search for text
  %(prog)s replace <file> <old> <new>   Replace text

Examples:
  %(prog)s wc README.md
  %(prog)s search README.md "hello"
  %(prog)s search -i README.md "Hello"
  %(prog)s replace README.md "old" "new" --dry-run
  %(prog)s replace README.md "old" "new"
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # wc command
    wc_parser = subparsers.add_parser("wc", help="Word count")
    wc_parser.add_argument("file", help="File to analyze")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for text")
    search_parser.add_argument("file", help="File to search")
    search_parser.add_argument("pattern", help="Text to search for")
    search_parser.add_argument(
        "-i", "--ignore-case",
        action="store_true",
        help="Ignore case when searching"
    )

    # replace command
    replace_parser = subparsers.add_parser("replace", help="Replace text")
    replace_parser.add_argument("file", help="File to modify")
    replace_parser.add_argument("old", help="Text to find")
    replace_parser.add_argument("new", help="Text to replace with")
    replace_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without doing it"
    )

    return parser


def main():
    """
    Main entry point for text tools.

    HOW: builds the parser, then dispatches to the matching
    run_*_command() handler based on which subcommand was used. If no
    subcommand was given, prints help instead of erroring, friendlier
    for a beginner just trying the tool for the first time.
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "wc":
        run_wc_command(args)
    elif args.command == "search":
        run_search_command(args)
    elif args.command == "replace":
        run_replace_command(args)


if __name__ == "__main__":
    main()
