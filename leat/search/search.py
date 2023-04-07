"""Search document stores for files that match configured search patterns"""

from collections import defaultdict
from pathlib import Path
from typing import Optional, Union, List
import re

from .config import ConfigData
from .pattern import PatternBuilder
from .result import DocResult
from leat.store.core import Document, DocStore
from leat.store.filesys import LocalFileSys


class Search:
    """Search document stores for files that match configured search patterns

    Attributes:
      config: ConfigData | Path | str | None: Configuration data, or path to it
      doc_store: DocStore | Path | list | str | None: Document store, path(s) to it, or a file to be searched
      predefined_configuration: str | None:  If not None, use predefined configuration for config
      default_section_sep: int | None: Length of text without patterns that is sufficient to create a new section or results
      default_section_max: int: Maximum length of a section. Useful if downstream data structures have a max length, e.g., deep learning tensors. Ignore if 0.
      sparse_data: bool: Whether spans are sparse in doc store. Used for efficiency considerations.

    Search takes a DocStore and ConfigData and generates DocResult for each document. Combines functionality of:
      - DocStore - Documents to be searched
      - ConfigData - Match patterns to be used in the search
      - PatternBuilder - Builds the match patterns from config data
      - Doing the actual search, here
      - DocResult - Structuring the results for each document

    Examples::

      doc_results = [doc_result in Search(configfile, document_directory)]
      doc_results = [doc_result for doc_result in Search(predefined_configuration='BasicSearch', doc_store=".")]
      search = Search(predefined_configuration='BasicSearch',
                doc_store="leat/tests/data/docset1/simple-document-1.txt")
      search.all_concepts()
      list(search.search_documents())

    """

    def __init__(
        self,
        config: Optional[Union[ConfigData, Path, str]] = None,
        doc_store: Optional[Union[DocStore, Path, list, str]] = None,
        predefined_configuration: Optional[str] = None,
        default_section_sep: Optional[int] = 125,
        default_section_max: int = 0,
        sparse_data: bool = False,
    ):
        """
        Searches document stores for configured search patterns

        Args:
          config: ConfigData | Path | str | None: Configuration data, or path to it (Default value = None)
          doc_store: DocStore | Path | list | str | None: Document store, path(s) to it, or a file to be searched
          predefined_configuration: str | None:  If not None, use predefined configuration for config (Default value = None)
          default_section_sep: int | None: Length of text without patterns that is sufficient to create a new section or results (Default value = 125)
          default_section_max: int: Maximum length of a section. Useful if downstream data structures have a max length, e.g., deep learning tensors. Ignore if 0 (Default value = 0)
          sparse_data: bool: Whether spans are sparse in doc store. Used for efficiency considerations. (Default value = False)
        """
        self.match_patterns: Optional[list] = None
        self.sparse_data = sparse_data
        self._super_pattern = None
        if predefined_configuration:
            self.config = ConfigData(predefined_configuration=predefined_configuration)
        else:
            self.config = config
        self.doc_store = doc_store
        self.default_section_sep = default_section_sep
        self.default_section_max = default_section_max

    @property
    def config(self) -> Optional[ConfigData]:
        """Config data"""
        return self._config

    @config.setter
    def config(self, config: Optional[Union[ConfigData, Path, str]]):
        """
        Sets config

        Args:
          config: ConfigData | Path | str | None: Configuration data, or path to it (Default value = None)
        """
        if config is None:
            self._config = None
            return
        if isinstance(config, ConfigData):
            self._config = config
        elif isinstance(config, Path) or isinstance(config, str):
            self._config = ConfigData(config)
        assert isinstance(self._config, ConfigData)
        if self.sparse_data:
            match_patterns, super_pattern = PatternBuilder.build(
                self._config, super_pattern=True
            )
        else:
            match_patterns = PatternBuilder.build(self._config)
        self.match_patterns = match_patterns
        if self.sparse_data and len(match_patterns) > 4:
            flag = re.I
            self._super_pattern = re.compile(super_pattern, flags=flag)

    @property
    def doc_store(self) -> Optional[DocStore]:
        """Doc store"""
        return self._doc_store

    @doc_store.setter
    def doc_store(self, doc_store):
        """
        Sets doc store

        Args:
          doc_store: DocStore | Path | list | str | None: Document store, path(s) to it, or a file to be searched
        """
        if doc_store is None:
            self._doc_store = DocStore()
            return
        if isinstance(doc_store, DocStore):
            self._doc_store = doc_store
        elif isinstance(doc_store, Path) or isinstance(doc_store, list):
            self._doc_store = DocStore(LocalFileSys(doc_store))
        elif isinstance(doc_store, str):
            filepath = Path(doc_store)
            if filepath.is_dir():
                print("INFO:", "Creating doc store in search for directory:", doc_store)
                self._doc_store = DocStore(LocalFileSys(filepath))
            elif filepath.expanduser().is_file():
                lfs = LocalFileSys()
                lfs.add_directory(
                    filepath.parent, include=filepath.name, recursive=False
                )
                print("INFO:", "Creating doc store in search for file:", doc_store)
                self._doc_store = DocStore(lfs)
            else:
                print("WARN:", "Unknown doc store in search:", doc_store)
                self._doc_store = None
        else:
            print("WARN:", "Unknown doc store in search:", doc_store)
            self._doc_store = None

    def search_documents(
        self, section_sep: Optional[int] = None, section_max: Optional[int] = None
    ):
        """
        Search all documents from document store for all match patterns

        Args:
          section_sep: int | None: Length of text without patterns that is sufficient to create a new section or results  (Default value = None)
          section_max: int | None: Maximum length of a section. Useful if downstream data structures have a max length, e.g., deep learning tensors. Ignore if 0 or None. (Default value = None)

        Yields:
          DocResult: Result for each document that has one or more matches
        """
        if section_sep is None:
            section_sep = self.default_section_sep
        if section_max is None:
            section_max = self.default_section_max
        if self.doc_store is None or self.doc_store.filesys is None:
            print("WARN:", "No documents to search")
            yield from []
        elif self.config is None:
            print("WARN:", "No search patterns configured")
            yield from []
        else:
            for doc in self.doc_store:
                result = self.search_document(
                    doc, section_sep=section_sep, section_max=section_max
                )
                if result is not None:
                    yield result

    def search_document(
        self,
        doc: Document,
        section_sep: Optional[int] = None,
        section_max: Optional[int] = None,
    ) -> Optional[DocResult]:
        """
        Search a document for all match patterns

        Args:
          doc: Document: Document to search
          section_sep: int | None: Length of text without patterns that is sufficient to create a new section or results  (Default value = None)
          section_max: int | None: Maximum length of a section. Useful if downstream data structures have a max length, e.g., deep learning tensors. Ignore if 0 or None. (Default value = None)

        Returns:
          DocResult | None: Result for each document, or None if no matches
        """
        # print("INFO:", doc.name, len(doc.text))
        if not doc:
            return
        if not doc.text:
            if doc.sha256:
                print("WARNING:", "Text no longer available for doc", doc.name)
            else:
                print("INFO:", "Skipping empty doc", doc.name)
            return
        if (
            self._super_pattern is not None
            and self._super_pattern.search(doc.text) is None
        ):
            # If no matches from super_pattern, then no need to iterate over individual matches
            return
        if section_sep is None:
            section_sep = self.default_section_sep
        if section_max is None:
            section_max = self.default_section_max
        docresults = defaultdict(list)
        for pattern in self.match_patterns:
            matches = list(pattern.finditer(doc.text))
            if matches:
                docresults[pattern].extend(matches)
        if docresults:
            return DocResult(
                doc, dict(docresults), section_sep=section_sep, section_max=section_max
            )

    def read_search_document(
        self, file: Union[Path, str], section_sep: Optional[int] = None
    ) -> Optional[DocResult]:
        """
        Read a file and search the document for all match patterns

        Args:
          file: Path | str: File to search
          section_sep: Optional[int]: Length of text without patterns that is sufficient to create a new section or results (Default value = None)

        Returns:
          DocResult | None: Result for each document, or None if no matches
        """
        doc = self.doc_store.read_document(Path(file))
        if doc is None:
            print("WARN:", "Skipping", file)
            return None
        return self.search_document(doc, section_sep)

    def search_document_text(
        self, text: str, name: str = "No Name", section_sep: Optional[int] = None
    ) -> Optional[DocResult]:
        """
        Search an arbitrary text for all match patterns. Useful for searching texts not in doc store.

        Args:
          text: str: Text to search
          name: str: Name to give to created Document (Default value = "No Name")
          section_sep: int | None:  Length of text without patterns that is sufficient to create a new section or result. Ignore if 0 or None. (Default value = None)

        Returns:
          DocResult | None: Result for the text, or None if no matches
        """
        doc = Document(name, text)
        return self.search_document(doc, section_sep)

    def __iter__(self):
        """Iterate over a search of all documents, from the doc store"""
        return self.search_documents()

    def __str__(self):
        """String representation of the object instance"""
        try:
            datadirs = [str(p.path) for p in self.doc_store.filesys.datadirs]
        except AttributeError:
            datadirs = []
        try:
            return f'<{__class__.__name__} {self.config.short_name}({len(self.match_patterns)}) {",".join(datadirs)[:30]}>'
        except AttributeError:
            return f'<{__class__.__name__} None(0) {",".join(datadirs)[:30]}>'

    def all_concepts(self) -> List[str]:
        """Returns list of all concepts to be searched"""
        return list(set(mp.concept for mp in self.match_patterns))
