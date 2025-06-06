import os
from pathlib import Path, PosixPath

import pytest

from leat.store.filesys import LocalFileSys


def init_filesys(tmp_path):
    os.makedirs(tmp_path / "a/b/c1/d1/e", exist_ok=True)
    os.makedirs(tmp_path / "a/b/c1/d2/e", exist_ok=True)
    os.makedirs(tmp_path / "a/b/c2/d/e", exist_ok=True)
    Path(tmp_path / "a/b/c1/d1/e", "file1.txt").touch()
    Path(tmp_path / "a/b/c1/d1/e", "file2.txt").touch()
    Path(tmp_path / "a/b/c1/d2/e", "file3.txt").touch()
    Path(tmp_path / "a/b/c2/", "file4.txt").touch()


def test_empty_fs(tmp_path):
    init_filesys(tmp_path)
    test_fs1 = LocalFileSys()
    assert test_fs1.get_files() == []


def test_add_directory(tmp_path):
    init_filesys(tmp_path)
    test_fs2 = LocalFileSys()
    test_fs2.add_directory(tmp_path / "a", recursive=True)
    assert sorted(test_fs2.get_files(recursive=True), key=str) == sorted(
        [
            PosixPath(tmp_path / "a/b"),
            PosixPath(tmp_path / "a/b/c1"),
            PosixPath(tmp_path / "a/b/c2"),
            PosixPath(tmp_path / "a/b/c1/d1"),
            PosixPath(tmp_path / "a/b/c1/d2"),
            PosixPath(tmp_path / "a/b/c1/d1/e"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file2.txt"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file1.txt"),
            PosixPath(tmp_path / "a/b/c1/d2/e"),
            PosixPath(tmp_path / "a/b/c1/d2/e/file3.txt"),
            PosixPath(tmp_path / "a/b/c2/file4.txt"),
            PosixPath(tmp_path / "a/b/c2/d"),
            PosixPath(tmp_path / "a/b/c2/d/e"),
        ],
        key=str,
    )


def test_get_files_nonrecursive(tmp_path):
    init_filesys(tmp_path)
    test_fs2 = LocalFileSys()
    test_fs2.add_directory(tmp_path / "a", recursive=True)
    assert test_fs2.get_files(recursive=False) == [PosixPath(tmp_path / "a/b")]


def test_get_files_subdir(tmp_path):
    init_filesys(tmp_path)
    test_fs3 = LocalFileSys(tmp_path / "a/b/c1", recursive=True)
    assert sorted(test_fs3.get_files(), key=str) == sorted(
        [
            PosixPath(tmp_path / "a/b/c1/d1"),
            PosixPath(tmp_path / "a/b/c1/d2"),
            PosixPath(tmp_path / "a/b/c1/d1/e"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file2.txt"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file1.txt"),
            PosixPath(tmp_path / "a/b/c1/d2/e"),
            PosixPath(tmp_path / "a/b/c1/d2/e/file3.txt"),
        ],
        key=str,
    )


def test_get_files_exclude(tmp_path):
    init_filesys(tmp_path)
    test_fs4 = LocalFileSys()
    test_fs4.add_directory(
        tmp_path / "a", recursive=True, exclude=["d1", "d1/*", "d1/**/*"]
    )
    assert sorted(test_fs4.get_files(), key=str) == sorted(
        [
            PosixPath(tmp_path / "a/b"),
            PosixPath(tmp_path / "a/b/c1"),
            PosixPath(tmp_path / "a/b/c2"),
            PosixPath(tmp_path / "a/b/c1/d2"),
            PosixPath(tmp_path / "a/b/c1/d2/e"),
            PosixPath(tmp_path / "a/b/c1/d2/e/file3.txt"),
            PosixPath(tmp_path / "a/b/c2/file4.txt"),
            PosixPath(tmp_path / "a/b/c2/d"),
            PosixPath(tmp_path / "a/b/c2/d/e"),
        ],
        key=str,
    )


def test_get_files_include(tmp_path):
    init_filesys(tmp_path)
    test_fs5 = LocalFileSys()
    test_fs5.add_directory(tmp_path / "a", recursive=True, include="*.txt")
    assert sorted(test_fs5.get_files(), key=str) == sorted(
        [
            PosixPath(tmp_path / "a/b/c1/d1/e/file2.txt"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file1.txt"),
            PosixPath(tmp_path / "a/b/c1/d2/e/file3.txt"),
            PosixPath(tmp_path / "a/b/c2/file4.txt"),
        ],
        key=str,
    )


def test_class_init_args(tmp_path):
    init_filesys(tmp_path)
    test_fs6 = LocalFileSys(tmp_path / "a", recursive=True)
    assert [f for f in test_fs6] == test_fs6.get_files()


def test_invalid_path(tmp_path):
    init_filesys(tmp_path)
    test_fs7 = LocalFileSys(tmp_path / "a/zzz")
    assert test_fs7.get_files() == []


def test_add_directories(tmp_path):
    init_filesys(tmp_path)
    test_fs8 = LocalFileSys()
    test_fs8.add_directories([tmp_path / "a/b/c1/d1", tmp_path / "a/b/c2"])
    assert sorted(test_fs8.get_files(), key=str) == sorted(
        [
            PosixPath(tmp_path / "a/b/c1/d1/e"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file2.txt"),
            PosixPath(tmp_path / "a/b/c1/d1/e/file1.txt"),
            PosixPath(tmp_path / "a/b/c2/file4.txt"),
            PosixPath(tmp_path / "a/b/c2/d"),
            PosixPath(tmp_path / "a/b/c2/d/e"),
        ],
        key=str,
    )
