""" "Access of files in local file system"""

from pathlib import Path
from typing import List, Optional, Sequence, Union

from leat.store.filesys import BaseFileSys


class LocalFileSys(BaseFileSys):
    "Access of files in local file system for a list of directories given inclusion and exclusion criteria"

    def __init__(
        self, directories: Optional[Sequence] = None, recursive: Optional[bool] = None
    ):
        self.datadirs: List["LocalDirectory"] = []
        if directories is not None:
            if type(directories) == str or isinstance(directories, Path):
                directories = [directories]
            self.add_directories(
                directories, recursive=recursive if recursive is not None else True
            )

    def add_directory(
        self,
        directory,
        include: Union[str | Sequence[str]] = "*",
        exclude: Optional[Sequence] = None,
        recursive: bool = True,
    ):
        if isinstance(directory, LocalDirectory):
            self.datadirs.append(directory)
            return
        if type(include) == str:
            include = [include]
        self.datadirs.append(
            LocalDirectory(
                Path(directory), include=include, exclude=exclude, recursive=recursive
            )
        )

    def add_directories(self, directories: Sequence, recursive: bool = True):
        for d in directories:
            self.add_directory(d, recursive=recursive)

    def get_files(self, recursive: Optional[bool] = None):
        "Get all file paths given include and exclude criteria"
        results = []
        for d in self.datadirs:
            results.extend(d.get_files(recursive=recursive))
        return results

    def __iter__(self):
        for d in self.datadirs:
            yield from d.get_files()


class LocalDirectory:
    "Local directory path with search information and exclusions"

    def __init__(
        self,
        path: Path,
        include: Optional[Sequence] = None,
        exclude: Optional[Sequence] = None,
        recursive: bool = True,
    ):
        if type(include) == str:
            include = [include]
        if type(exclude) == str:
            exclude = [exclude]
        self.path = path
        self.include = include if include is not None else ["*"]
        self.exclude = exclude if exclude is not None else []
        self.recursive = recursive

    def get_files(self, recursive: Optional[bool] = None):
        "Get files in directory given include and exclude criteria"
        if recursive is None:
            recursive = self.recursive
        results = []
        for pat in self.include:
            for filepath in self.path.rglob(pat) if recursive else self.path.glob(pat):
                if any(filepath.match(ex) for ex in self.exclude):
                    continue
                results.append(filepath)
        return results
