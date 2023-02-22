"""Search document stores for files that match configured search patterns"""

from collections import defaultdict
from pathlib import Path
from typing import Optional, Union

from .config import ConfigData
from .pattern import PatternBuilder
from .result import DocResult
from ..store.core import Document, DocStore
from ..store.filesys import LocalFileSys


class Search:
    "Search document stores for files that match configured search patterns"

    def __init__(
        self,
        config: Optional[Union[ConfigData, Path, str]] = None,
        doc_store: Optional[Union[DocStore, Path, list, str]] = None,
        predefined_configuration: Optional[str] = None,
        default_section_sep: Optional[int] = 125,
    ):
        self.match_patterns: Optional[list] = None
        if predefined_configuration:
            self.config = ConfigData(predefined_configuration=predefined_configuration)
        else:
            self.config = config
        self.doc_store = doc_store
        self.default_section_sep = default_section_sep

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config: Optional[Union[ConfigData, Path, str]]):
        if config is None:
            self._config = None
            return
        if isinstance(config, ConfigData):
            self._config = config
        elif isinstance(config, Path) or isinstance(config, str):
            self._config = ConfigData(config)
        assert isinstance(self._config, ConfigData)
        match_patterns = PatternBuilder.build(self._config)
        self.match_patterns = match_patterns

    @property
    def doc_store(self):
        return self._doc_store

    @doc_store.setter
    def doc_store(self, doc_store):
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
            elif filepath.is_file():
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

    def search_documents(self, section_sep: Optional[int] = None):
        "Search all documents from document store for all match patterns"
        if section_sep is None:
            section_sep = self.default_section_sep
        if self.doc_store is None or self.doc_store.filesys is None:
            print("WARN:", "No documents to search")
            yield from []
        elif self.config is None:
            print("WARN:", "No search patterns configured")
            yield from []
        else:
            for doc in self.doc_store:
                yield self.search_document(doc, section_sep=section_sep)

    def search_document(self, doc: Document, section_sep: Optional[int] = None):
        "Search a document for all match patterns"
        print("INFO:", doc.name, len(doc.text))
        if section_sep is None:
            section_sep = self.default_section_sep
        docresults = defaultdict(list)
        for pattern in self.match_patterns:
            matches = list(pattern.finditer(doc.text))
            docresults[pattern].extend(matches)
        return DocResult(doc, dict(docresults), section_sep=section_sep)

    def read_search_document(
        self, file: Union[Path, str], section_sep: Optional[int] = None
    ):
        "Read a file and search the document for all match patterns"
        doc = self.doc_store.read_document(Path(file))
        if doc is None:
            print("WARN:", "Skipping", file)
            return None
        return self.search_document(doc, section_sep)

    def search_document_text(
        self, text: str, name: str = "No Name", section_sep: Optional[int] = None
    ):
        "Search the text of a document for all match patterns"
        doc = Document(name, text)
        return self.search_document(doc, section_sep)

    def __iter__(self):
        return self.search_documents()

    def __str__(self):
        try:
            datadirs = [str(p.path) for p in self.doc_store.filesys.datadirs]
        except AttributeError:
            datadirs = []
        try:
            return f'<{__class__.__name__} {self.config.short_name}({len(self.match_patterns)}) {",".join(datadirs)[:30]}>'
        except AttributeError:
            return f'<{__class__.__name__} None(0) {",".join(datadirs)[:30]}>'
