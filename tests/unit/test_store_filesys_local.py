import os
from pathlib import Path, PosixPath

import pytest

from leat.store.filesys import LocalFileSys


def init_filesys(tmpdir):
    os.makedirs("a/b/c1/d1/e", exist_ok=True)
    os.makedirs("a/b/c1/d2/e", exist_ok=True)
    os.makedirs("a/b/c2/d/e", exist_ok=True)
    Path("a/b/c1/d1/e", "file1.txt").touch()
    Path("a/b/c1/d1/e", "file2.txt").touch()
    Path("a/b/c1/d2/e", "file3.txt").touch()
    Path("a/b/c2/", "file4.txt").touch()


def test_empty_fs(tmpdir):
    init_filesys(tmpdir)
    test_fs1 = LocalFileSys()
    assert test_fs1.get_files() == []


def test_add_directory(tmpdir):
    init_filesys(tmpdir)
    test_fs2 = LocalFileSys()
    test_fs2.add_directory("a", recursive=True)
    assert test_fs2.get_files(recursive=True) == [
        PosixPath("a/b"),
        PosixPath("a/b/c1"),
        PosixPath("a/b/c2"),
        PosixPath("a/b/c1/d1"),
        PosixPath("a/b/c1/d2"),
        PosixPath("a/b/c1/d1/e"),
        PosixPath("a/b/c1/d1/e/file2.txt"),
        PosixPath("a/b/c1/d1/e/file1.txt"),
        PosixPath("a/b/c1/d2/e"),
        PosixPath("a/b/c1/d2/e/file3.txt"),
        PosixPath("a/b/c2/file4.txt"),
        PosixPath("a/b/c2/d"),
        PosixPath("a/b/c2/d/e"),
    ]


def test_get_files_nonrecursive(tmpdir):
    init_filesys(tmpdir)
    test_fs2 = LocalFileSys()
    test_fs2.add_directory("a", recursive=True)
    assert test_fs2.get_files(recursive=False) == [PosixPath("a/b")]


def test_get_files_subdir(tmpdir):
    init_filesys(tmpdir)
    test_fs3 = LocalFileSys("a/b/c1", recursive=True)
    assert test_fs3.get_files() == [
        PosixPath("a/b/c1/d1"),
        PosixPath("a/b/c1/d2"),
        PosixPath("a/b/c1/d1/e"),
        PosixPath("a/b/c1/d1/e/file2.txt"),
        PosixPath("a/b/c1/d1/e/file1.txt"),
        PosixPath("a/b/c1/d2/e"),
        PosixPath("a/b/c1/d2/e/file3.txt"),
    ]


def test_get_files_exclude(tmpdir):
    init_filesys(tmpdir)
    test_fs4 = LocalFileSys()
    test_fs4.add_directory("a", recursive=True, exclude=["d1", "d1/*", "d1/**/*"])
    assert test_fs4.get_files() == [
        PosixPath("a/b"),
        PosixPath("a/b/c1"),
        PosixPath("a/b/c2"),
        PosixPath("a/b/c1/d2"),
        PosixPath("a/b/c1/d2/e"),
        PosixPath("a/b/c1/d2/e/file3.txt"),
        PosixPath("a/b/c2/file4.txt"),
        PosixPath("a/b/c2/d"),
        PosixPath("a/b/c2/d/e"),
    ]


def test_get_files_include(tmpdir):
    init_filesys(tmpdir)
    test_fs5 = LocalFileSys()
    test_fs5.add_directory("a", recursive=True, include="*.txt")
    assert test_fs5.get_files() == [
        PosixPath("a/b/c1/d1/e/file2.txt"),
        PosixPath("a/b/c1/d1/e/file1.txt"),
        PosixPath("a/b/c1/d2/e/file3.txt"),
        PosixPath("a/b/c2/file4.txt"),
    ]


def test_class_init_args(tmpdir):
    init_filesys(tmpdir)
    test_fs6 = LocalFileSys("a", recursive=True)
    assert [f for f in test_fs6] == test_fs6.get_files()


def test_invalid_path(tmpdir):
    init_filesys(tmpdir)
    test_fs7 = LocalFileSys("a/zzz")
    assert test_fs7.get_files() == []


def test_add_directories(tmpdir):
    init_filesys(tmpdir)
    test_fs8 = LocalFileSys()
    test_fs8.add_directories(["a/b/c1/d1", "a/b/c2"])
    assert test_fs8.get_files() == [
        PosixPath("a/b/c1/d1/e"),
        PosixPath("a/b/c1/d1/e/file2.txt"),
        PosixPath("a/b/c1/d1/e/file1.txt"),
        PosixPath("a/b/c2/file4.txt"),
        PosixPath("a/b/c2/d"),
        PosixPath("a/b/c2/d/e"),
    ]
