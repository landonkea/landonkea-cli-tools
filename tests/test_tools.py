#!/usr/bin/env python3
"""
test_tools.py — Tests for CLI tools.

Run with: python -m pytest test_tools.py -v
Or: python test_tools.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path so we can import our tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_organizer import get_category, scan_directory, format_size, organize_files, undo_organize
from text_tools import word_count, search_file, replace_in_file
from disk_usage import scan_directory as disk_scan


def test_get_category():
    """Test that file extensions are correctly categorized."""
    # Documents
    assert get_category("report.pdf") == "Documents"
    assert get_category("notes.txt") == "Documents"
    assert get_category("data.xlsx") == "Documents"

    # Images
    assert get_category("photo.jpg") == "Images"
    assert get_category("image.png") == "Images"
    assert get_category("logo.svg") == "Images"

    # Videos
    assert get_category("video.mp4") == "Videos"
    assert get_category("clip.mkv") == "Videos"

    # Audio
    assert get_category("song.mp3") == "Audio"
    assert get_category("music.wav") == "Audio"

    # Archives
    assert get_category("backup.zip") == "Archives"
    assert get_category("archive.tar.gz") == "Archives"

    # Code
    assert get_category("script.py") == "Code"
    assert get_category("app.js") == "Code"

    # Unknown
    assert get_category("unknown.xyz") == "Other"
    assert get_category("noextension") == "Other"


def test_format_size():
    """Test that bytes are correctly formatted."""
    assert format_size(0) == "0 B"
    assert format_size(100) == "100.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1048576) == "1.0 MB"
    assert format_size(1073741824) == "1.0 GB"


def test_scan_directory():
    """Test that directory scanning works."""
    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        (Path(tmpdir) / "report.pdf").write_text("test")
        (Path(tmpdir) / "photo.jpg").write_text("test")
        (Path(tmpdir) / "notes.txt").write_text("test")

        # Scan it
        results = scan_directory(tmpdir)

        # Should find 3 files
        assert len(results) == 3

        # Check categories
        categories = [r["category"] for r in results]
        assert "Documents" in categories
        assert "Images" in categories


def test_organize_and_undo():
    """Test that organizing and undoing works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "report.pdf").write_text("test pdf")
        (Path(tmpdir) / "photo.jpg").write_bytes(b"test jpg")
        (Path(tmpdir) / "notes.txt").write_text("test txt")

        # Organize (force to skip confirmation)
        stats = organize_files(tmpdir, force=True, quiet=True)

        # Should have moved 3 files
        assert stats["moved"] == 3

        # Check that files are in subfolders
        assert (Path(tmpdir) / "Documents" / "report.pdf").exists()
        assert (Path(tmpdir) / "Images" / "photo.jpg").exists()
        assert (Path(tmpdir) / "Documents" / "notes.txt").exists()

        # Check that log file was created
        assert (Path(tmpdir) / ".organize.log").exists()

        # Undo the organize
        restored = undo_organize(tmpdir, quiet=True)

        # Should have restored 3 files
        assert restored == 3

        # Check that files are back in original location
        assert (Path(tmpdir) / "report.pdf").exists()
        assert (Path(tmpdir) / "photo.jpg").exists()
        assert (Path(tmpdir) / "notes.txt").exists()

        # Check that subfolders were removed (or exist but empty)
        assert not (Path(tmpdir) / "Documents" / "report.pdf").exists()


def test_word_count():
    """Test word counting."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello world\nThis is a test")
        f.flush()

        try:
            stats = word_count(f.name)
            assert stats["lines"] == 2
            assert stats["words"] == 6
        finally:
            os.unlink(f.name)


def test_search_file():
    """Test file searching."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello world\nHello Python\nGoodbye world\n")
        f.flush()

        try:
            matches = search_file(f.name, "Hello")
            assert len(matches) == 2
            assert matches[0]["line_num"] == 1
            assert matches[1]["line_num"] == 2
        finally:
            os.unlink(f.name)


def test_replace_in_file():
    """Test text replacement."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello world\nHello Python\n")
        f.flush()

        try:
            count = replace_in_file(f.name, "Hello", "Hi")
            assert count == 2

            with open(f.name) as f2:
                content = f2.read()
                assert content == "Hi world\nHi Python\n"
        finally:
            os.unlink(f.name)


def test_disk_scan():
    """Test disk usage scanning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        (Path(tmpdir) / "file1.txt").write_text("test")
        (Path(tmpdir) / "file2.txt").write_text("test")

        results = disk_scan(tmpdir)

        # Should find the directory itself and 2 files
        assert len(results) >= 3


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_get_category,
        test_format_size,
        test_scan_directory,
        test_organize_and_undo,
        test_word_count,
        test_search_file,
        test_replace_in_file,
        test_disk_scan,
    ]

    passed = 0
    failed = 0

    print("Running tests...")
    print()

    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
