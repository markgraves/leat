"""
Isolates and encapsulates file system access.
Currently, only local file systems are supported, but cloud access would go here
"""

from .base_filesys import BaseFileSys
from .local import LocalFileSys
