"""Access of files in local file system"""

from pathlib import Path
from typing import List, Optional, Sequence, Union

from leat.store.filesys import BaseFileSys


class LocalFileSys(BaseFileSys):
    """
    Access of files in local file system from a list of directories given inclusion and exclusion criteria

    Attributes:
      datadirs: List[LocalDirectory]: List of directories to track

    Example::

      fs = LocalFileSys()
      fs.add_directory("Documents")
      fs.add_directory("Code", include="*.txt", exclude="tmp*")

    """

    def __init__(
        self, directories: Optional[Sequence] = None, recursive: Optional[bool] = None
    ):
        """
        Create a LocalFileSys for a collection of directories.

        Args:
          directories: Sequence | None:  (Default value = None)
          recursive: bool | None:  (Default value = None)

        Note: None may be passed to recursive to get the default behavior of True
        """
        self.datadirs: List["LocalDirectory"] = []
        if directories is not None:
            if type(directories) == str or isinstance(directories, Path):
                directories = [directories]
            self.add_directories(
                directories, recursive=recursive if recursive is not None else True
            )

    def add_directory(
        self,
        directory: Union[Path, str, "LocalDirectory"],
        #        include: Union[str | Sequence[str]] = "*",  # python 3.10+
        include="*",
        exclude: Optional[Sequence] = None,
        recursive: bool = True,
    ):
        """
        Add a directory to those tracked by the filesys

        Args:
          directory: Path | str | LocalDirectory: Directory to add
          include: str | Sequence[str]: glob patterns to include within a directory (Default value = "*")
          exclude: Sequence | None: glob patterns to exclude a file if matched (Default value = None)
          recursive: bool: Whether to recurse the directory (Default value = True)

        """
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
        """
        Add a list of directories to those tracked by the filesys

        Args:
          directories: Sequence: Directories to add
          recursive: bool: Whether to recurse the directories (Default value = True)
        """
        for d in directories:
            self.add_directory(d, recursive=recursive)

    def get_files(self, recursive: Optional[bool] = None) -> List[Path]:
        """
        Get all file paths given include and exclude criteria

        Args:
          recursive: Optional[bool]: Whether to recurse the directory (Default value = None)

        Returns:
          List of filepaths
        """
        results = []
        for d in self.datadirs:
            results.extend(d.get_files(recursive=recursive))
        return results

    def __iter__(self):
        """Yield filepaths from all the non-excluded directories in the filesys"""
        for d in self.datadirs:
            yield from d.get_files()


class LocalDirectory:
    """
    Local directory path with search information and exclusions

    Attributes:
          path: Path:  Path of the directory
          include: List[str]: glob patterns to include within a directory
          exclude: List[str]: glob patterns to exclude a file if matched
          recursive: bool: Whether to recurse the directory
    """

    def __init__(
        self,
        path: Path,
        include: Optional[Sequence] = None,
        exclude: Optional[Sequence] = None,
        recursive: bool = True,
    ):
        """
        Create local directory path with search information and exclusion

        Args:
          path: Path: Path of the directory
          include: List[str] | str | None: glob patterns to include within a directory (Default value = None)
          exclude: List[str] | str | None: glob patterns to exclude a file if matched (Default value = None)
          recursive: bool: Whether to recurse the directory (Default value = True)
        """
        if type(include) == str:
            include = [include]
        if type(exclude) == str:
            exclude = [exclude]
        self.path = path.expanduser()
        self.include = include if include is not None else ["*"]
        self.exclude = exclude if exclude is not None else []
        self.recursive = recursive

    def get_files(self, recursive: Optional[bool] = None) -> List[Path]:
        """
        Get files in directory given include and exclude criteria

        Args:
          recursive: Optional[bool]: Whether to recurse the directory (Default value = None)

        Returns:
          List of filepaths
        """
        if recursive is None:
            recursive = self.recursive
        results = []
        for pat in self.include:
            for filepath in self.path.rglob(pat) if recursive else self.path.glob(pat):
                if any(filepath.match(ex) for ex in self.exclude):
                    continue
                results.append(filepath)
        return results
