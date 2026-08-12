#!/usr/bin/env python3
"""
test_tools.py, Tests for CLI tools.

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
from system_info import get_os_info, get_python_info, get_cpu_info, get_info_dict
from batch_rename import parse_pattern, compute_new_name, scan_renames, rename_files


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


def test_replace_in_file_rejects_empty_old_text():
    """
    Regression test for a real bug: replace_in_file(..., old_text="")
    used to call content.replace("", new_text), which inserts new_text
    between every single character in the file instead of doing
    anything meaningful. It should now be rejected up front and leave
    the file untouched.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("ab")
        f.flush()

        try:
            count = replace_in_file(f.name, "", "X")
            assert count == 0

            with open(f.name) as f2:
                # File must be unchanged, no "XaXbX" corruption
                assert f2.read() == "ab"
        finally:
            os.unlink(f.name)


def test_get_os_info():
    """Test that OS info returns the expected keys with non-empty values."""
    info = get_os_info()
    assert set(info.keys()) == {
        "system", "release", "version", "machine", "processor", "platform"
    }
    # system (e.g. "Darwin"/"Linux"/"Windows") should never be empty
    assert info["system"]


def test_get_python_info():
    """Test that Python interpreter info is reported correctly."""
    info = get_python_info()
    assert info["implementation"] in ("CPython", "PyPy", "Jython", "IronPython")
    assert info["executable"] == sys.executable


def test_get_cpu_info():
    """
    Test CPU info: cores should be a positive int (or "N/A" fallback on
    the rare platform where os.cpu_count() can't tell), and load_avg
    should either be a 3-tuple of floats (POSIX) or None (Windows).
    """
    info = get_cpu_info()
    assert info["cores"] == "N/A" or (isinstance(info["cores"], int) and info["cores"] > 0)
    assert info["load_avg"] is None or len(info["load_avg"]) == 3


def test_get_info_dict_shape():
    """Test that the --json payload includes every top-level section."""
    info = get_info_dict()
    assert set(info.keys()) == {
        "os", "python", "cpu", "disk", "current_dir", "user", "home"
    }


def test_parse_pattern():
    """Test parsing sed-style s/old/new/flags strings."""
    assert parse_pattern("s/old/new/") == ("old", "new", "")
    assert parse_pattern("s/IMG_/vacation_/g") == ("IMG_", "vacation_", "g")
    assert parse_pattern("s/jpeg/jpg/i") == ("jpeg", "jpg", "i")
    assert parse_pattern("s/a/b/gi") == ("a", "b", "gi")
    # Empty new is valid (deleting text), empty old is not.
    assert parse_pattern("s/remove//") == ("remove", "", "")


def assert_raises_value_error(func, *args):
    """
    Small helper since this file's tests run via plain function calls
    (see run_all_tests() below), not pytest, so pytest.raises() isn't
    available, this repo has no pytest dependency installed.
    """
    try:
        func(*args)
    except ValueError:
        return
    raise AssertionError(f"Expected ValueError from {func.__name__}{args!r}")


def test_parse_pattern_rejects_invalid_input():
    """Test that malformed or unsafe patterns raise ValueError."""
    assert_raises_value_error(parse_pattern, "not-a-sed-pattern")
    assert_raises_value_error(parse_pattern, "s/old/new/x")  # unknown flag
    assert_raises_value_error(parse_pattern, "s//new/")  # empty old, same bug class as replace_in_file


def test_compute_new_name():
    """Test applying a parsed substitution to a single filename."""
    assert compute_new_name("IMG_001.jpg", "IMG_", "vacation_", "") == "vacation_001.jpg"
    # No 'g' flag: only the first occurrence is replaced.
    assert compute_new_name("aa.txt", "a", "b", "") == "ba.txt"
    # 'g' flag: every occurrence is replaced.
    assert compute_new_name("aa.txt", "a", "b", "g") == "bb.txt"
    # 'i' flag: case-insensitive match.
    assert compute_new_name("PHOTO.JPEG", "jpeg", "jpg", "i") == "PHOTO.jpg"
    # No match: filename is returned unchanged.
    assert compute_new_name("report.pdf", "xyz", "abc", "") == "report.pdf"
    # A literal backslash in the replacement isn't treated as a regex
    # backreference.
    assert compute_new_name("a.txt", "a", "x\\1y", "") == "x\\1y.txt"


def test_scan_renames():
    """Test scanning a directory for files that match a rename pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "IMG_001.jpg").write_text("test")
        (Path(tmpdir) / "IMG_002.jpg").write_text("test")
        (Path(tmpdir) / "notes.txt").write_text("test")

        renames = scan_renames(tmpdir, "s/IMG_/vacation_/")

        # Only the two IMG_ files match, notes.txt is untouched.
        assert len(renames) == 2
        new_names = sorted(r["new_path"].name for r in renames)
        assert new_names == ["vacation_001.jpg", "vacation_002.jpg"]


def test_rename_files_dry_run_does_not_touch_disk():
    """Test that --dry-run reports matches without renaming anything."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "old_report.pdf").write_text("test")

        result = rename_files(tmpdir, "s/old_/new_/", dry_run=True, quiet=True)

        assert result == {"matched": 1, "renamed": 0}
        # Original file must still exist, untouched.
        assert (Path(tmpdir) / "old_report.pdf").exists()
        assert not (Path(tmpdir) / "new_report.pdf").exists()


def test_rename_files_force_renames_on_disk():
    """Test that --force actually renames matching files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "old_report.pdf").write_text("test content")

        result = rename_files(tmpdir, "s/old_/new_/", force=True, quiet=True)

        assert result == {"matched": 1, "renamed": 1}
        assert not (Path(tmpdir) / "old_report.pdf").exists()
        assert (Path(tmpdir) / "new_report.pdf").exists()
        assert (Path(tmpdir) / "new_report.pdf").read_text() == "test content"


def test_rename_files_skips_on_collision():
    """
    Test that a rename which would overwrite an existing file is
    skipped rather than silently destroying the existing file's
    content.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "old_report.pdf").write_text("original content")
        (Path(tmpdir) / "new_report.pdf").write_text("do not overwrite me")

        result = rename_files(tmpdir, "s/old_/new_/", force=True, quiet=True)

        assert result == {"matched": 1, "renamed": 0}
        # Both files still exist, neither was touched.
        assert (Path(tmpdir) / "old_report.pdf").read_text() == "original content"
        assert (Path(tmpdir) / "new_report.pdf").read_text() == "do not overwrite me"


def test_rename_files_recursive():
    """Test that --recursive reaches files in subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = Path(tmpdir) / "subfolder"
        subdir.mkdir()
        (subdir / "old_nested.txt").write_text("test")
        (Path(tmpdir) / "old_top.txt").write_text("test")

        result = rename_files(tmpdir, "s/old_/new_/", force=True, quiet=True, recursive=True)

        assert result == {"matched": 2, "renamed": 2}
        assert (subdir / "new_nested.txt").exists()
        assert (Path(tmpdir) / "new_top.txt").exists()


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
        test_replace_in_file_rejects_empty_old_text,
        test_get_os_info,
        test_get_python_info,
        test_get_cpu_info,
        test_get_info_dict_shape,
        test_parse_pattern,
        test_parse_pattern_rejects_invalid_input,
        test_compute_new_name,
        test_scan_renames,
        test_rename_files_dry_run_does_not_touch_disk,
        test_rename_files_force_renames_on_disk,
        test_rename_files_skips_on_collision,
        test_rename_files_recursive,
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
