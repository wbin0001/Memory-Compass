# -*- coding: utf-8 -*-
"""Memory Compass Core Modules

This package contains the core components of Memory Compass:
- file_system: WAL Protocol and file-based memory storage
- lance_db: LanceDB vector memory store
- unified_search: Unified search across all memory tracks
"""

from .file_system import FileSystemMemory
from .unified_search import UnifiedSearch

__all__ = [
    "FileSystemMemory",
    "UnifiedSearch",
]

# LanceDB is optional
try:
    from .lance_db import LanceDBMemory
    __all__.append("LanceDBMemory")
except ImportError:
    pass
