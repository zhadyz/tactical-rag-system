"""
CODEBASE INTELLIGENCE SYSTEM
Persistent knowledge graph for MENDICANT_BIAS acceleration

Eliminates redundant operations through:
- Automatic project indexing
- Smart caching
- Incremental updates
- Cross-session persistence
"""

import json
import os
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class FileMetadata:
    """Cached metadata for a single file"""
    path: str
    last_modified: float
    size: int
    hash: str
    language: str
    summary: str
    symbols: List[Dict[str, Any]]
    imports: List[str]
    exports: List[str]
    dependencies: List[str]


@dataclass
class SymbolInfo:
    """Symbol relationship information"""
    name: str
    kind: str  # class, function, method, variable, etc.
    file_path: str
    line_start: int
    line_end: int
    signature: Optional[str]
    docstring: Optional[str]
    references: List[str]  # Files that reference this symbol
    children: List[str]  # Child symbols (methods, nested classes)
    parent: Optional[str]  # Parent symbol


@dataclass
class ProjectIndex:
    """Complete project knowledge graph"""
    root_path: str
    last_updated: float
    files: Dict[str, FileMetadata]
    symbols: Dict[str, SymbolInfo]  # symbol_id -> SymbolInfo
    symbol_map: Dict[str, List[str]]  # symbol_name -> [symbol_ids]
    file_relationships: Dict[str, List[str]]  # file -> [files it imports]
    conventions: Dict[str, Any]
    architecture: Dict[str, Any]
    technology_stack: List[str]
    entry_points: List[str]
    test_locations: List[str]
    config_files: List[str]


class CodebaseIntelligence:
    """
    Persistent codebase knowledge system

    Optimized for SPEED and ZERO redundancy
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.memory_dir = self.project_root / ".claude" / "memory"
        self.cache_dir = self.memory_dir / "file_cache"
        self.index_path = self.memory_dir / "project_index.json"

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.index: Optional[ProjectIndex] = None
        self._load_index()

    def _load_index(self):
        """Load existing index or create new one"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.index = self._deserialize_index(data)
                print(f"[INTELLIGENCE] Loaded existing index: {len(self.index.files)} files, {len(self.index.symbols)} symbols")
            except Exception as e:
                print(f"[INTELLIGENCE] Error loading index: {e}, creating new")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create fresh index"""
        self.index = ProjectIndex(
            root_path=str(self.project_root),
            last_updated=time.time(),
            files={},
            symbols={},
            symbol_map=defaultdict(list),
            file_relationships={},
            conventions={},
            architecture={},
            technology_stack=[],
            entry_points=[],
            test_locations=[],
            config_files=[]
        )

    def _save_index(self):
        """Persist index to disk"""
        data = self._serialize_index(self.index)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[INTELLIGENCE] Index saved: {len(self.index.files)} files, {len(self.index.symbols)} symbols")

    def _serialize_index(self, index: ProjectIndex) -> dict:
        """Convert index to JSON-serializable dict"""
        return {
            "root_path": index.root_path,
            "last_updated": index.last_updated,
            "files": {k: asdict(v) for k, v in index.files.items()},
            "symbols": {k: asdict(v) for k, v in index.symbols.items()},
            "symbol_map": dict(index.symbol_map),
            "file_relationships": index.file_relationships,
            "conventions": index.conventions,
            "architecture": index.architecture,
            "technology_stack": index.technology_stack,
            "entry_points": index.entry_points,
            "test_locations": index.test_locations,
            "config_files": index.config_files
        }

    def _deserialize_index(self, data: dict) -> ProjectIndex:
        """Convert JSON dict to ProjectIndex"""
        return ProjectIndex(
            root_path=data["root_path"],
            last_updated=data["last_updated"],
            files={k: FileMetadata(**v) for k, v in data["files"].items()},
            symbols={k: SymbolInfo(**v) for k, v in data["symbols"].items()},
            symbol_map=defaultdict(list, data["symbol_map"]),
            file_relationships=data["file_relationships"],
            conventions=data["conventions"],
            architecture=data["architecture"],
            technology_stack=data["technology_stack"],
            entry_points=data["entry_points"],
            test_locations=data["test_locations"],
            config_files=data["config_files"]
        )

    def _compute_file_hash(self, file_path: Path) -> str:
        """Fast file hash for change detection"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            return hasher.hexdigest()
        except:
            return ""

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql'
        }
        return ext_map.get(file_path.suffix.lower(), 'unknown')

    def needs_update(self, file_path: Path) -> bool:
        """Check if file needs re-indexing"""
        rel_path = str(file_path.relative_to(self.project_root))

        if rel_path not in self.index.files:
            return True

        cached = self.index.files[rel_path]

        # Check modification time
        try:
            current_mtime = file_path.stat().st_mtime
            if current_mtime > cached.last_modified:
                return True
        except:
            return True

        # Check hash for extra safety
        current_hash = self._compute_file_hash(file_path)
        if current_hash != cached.hash:
            return True

        return False

    def get_file_summary(self, file_path: str) -> Optional[str]:
        """
        INSTANT file summary retrieval - NO file reading

        Returns cached summary or None
        """
        if file_path in self.index.files:
            return self.index.files[file_path].summary
        return None

    def get_symbols_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        INSTANT symbol retrieval - NO file reading

        Returns cached symbols or empty list
        """
        if file_path in self.index.files:
            return self.index.files[file_path].symbols
        return []

    def find_symbol(self, symbol_name: str) -> List[SymbolInfo]:
        """
        INSTANT symbol lookup across entire codebase

        No searching needed - direct hash lookup
        """
        symbol_ids = self.index.symbol_map.get(symbol_name, [])
        return [self.index.symbols[sid] for sid in symbol_ids if sid in self.index.symbols]

    def get_file_dependencies(self, file_path: str) -> List[str]:
        """
        INSTANT dependency retrieval

        Returns list of files this file depends on
        """
        if file_path in self.index.files:
            return self.index.files[file_path].dependencies
        return []

    def get_dependent_files(self, file_path: str) -> List[str]:
        """
        INSTANT reverse dependency lookup

        Returns files that depend on this file
        """
        dependents = []
        for fpath, deps in self.index.file_relationships.items():
            if file_path in deps:
                dependents.append(fpath)
        return dependents

    def get_architecture_overview(self) -> Dict[str, Any]:
        """
        INSTANT architecture summary

        Pre-computed project structure
        """
        return {
            "technology_stack": self.index.technology_stack,
            "entry_points": self.index.entry_points,
            "test_locations": self.index.test_locations,
            "config_files": self.index.config_files,
            "architecture_patterns": self.index.architecture,
            "conventions": self.index.conventions,
            "file_count": len(self.index.files),
            "symbol_count": len(self.index.symbols)
        }

    def query(self, question: str) -> Dict[str, Any]:
        """
        Natural language query interface

        Instantly answer questions about codebase without reading files
        """
        question_lower = question.lower()

        # "What does file X do?"
        if "what does" in question_lower and "do" in question_lower:
            for file_path in self.index.files:
                if file_path in question:
                    return {
                        "answer": self.index.files[file_path].summary,
                        "symbols": self.index.files[file_path].symbols,
                        "dependencies": self.index.files[file_path].dependencies
                    }

        # "Where is class/function X?"
        if "where is" in question_lower or "find" in question_lower:
            for word in question.split():
                symbols = self.find_symbol(word)
                if symbols:
                    return {
                        "answer": f"Found {len(symbols)} definitions",
                        "locations": [
                            {
                                "file": s.file_path,
                                "line": s.line_start,
                                "kind": s.kind,
                                "signature": s.signature
                            }
                            for s in symbols
                        ]
                    }

        # "What's the architecture?"
        if "architecture" in question_lower or "structure" in question_lower:
            return {"answer": self.get_architecture_overview()}

        return {"answer": "Query not understood", "suggestions": [
            "What does [file] do?",
            "Where is [symbol]?",
            "What's the project architecture?",
            "What files depend on [file]?"
        ]}

    def invalidate_cache(self, file_path: str):
        """
        Smart cache invalidation

        Invalidates file and all dependent caches
        """
        if file_path in self.index.files:
            # Remove file metadata
            del self.index.files[file_path]

            # Remove symbols from this file
            symbols_to_remove = [
                sid for sid, sinfo in self.index.symbols.items()
                if sinfo.file_path == file_path
            ]
            for sid in symbols_to_remove:
                sinfo = self.index.symbols[sid]
                # Remove from symbol map
                if sinfo.name in self.index.symbol_map:
                    self.index.symbol_map[sinfo.name] = [
                        s for s in self.index.symbol_map[sinfo.name] if s != sid
                    ]
                del self.index.symbols[sid]

            # Remove file relationships
            if file_path in self.index.file_relationships:
                del self.index.file_relationships[file_path]

            print(f"[INTELLIGENCE] Invalidated cache for: {file_path}")

    def get_stats(self) -> Dict[str, Any]:
        """Get intelligence system statistics"""
        return {
            "total_files": len(self.index.files),
            "total_symbols": len(self.index.symbols),
            "technology_stack": self.index.technology_stack,
            "last_updated": time.ctime(self.index.last_updated),
            "cache_size_mb": self._get_cache_size(),
            "languages": self._get_language_distribution()
        }

    def _get_cache_size(self) -> float:
        """Calculate total cache size in MB"""
        total_size = 0
        for file in self.cache_dir.glob("**/*"):
            if file.is_file():
                total_size += file.stat().st_size
        if self.index_path.exists():
            total_size += self.index_path.stat().st_size
        return round(total_size / (1024 * 1024), 2)

    def _get_language_distribution(self) -> Dict[str, int]:
        """Get distribution of languages in codebase"""
        dist = defaultdict(int)
        for file_meta in self.index.files.values():
            dist[file_meta.language] += 1
        return dict(dist)

    def export_knowledge_graph(self, output_path: str):
        """Export knowledge graph in various formats"""
        data = {
            "metadata": {
                "project_root": self.index.root_path,
                "generated_at": time.time(),
                "stats": self.get_stats()
            },
            "files": {
                path: {
                    "summary": meta.summary,
                    "language": meta.language,
                    "symbols": meta.symbols,
                    "dependencies": meta.dependencies
                }
                for path, meta in self.index.files.items()
            },
            "symbols": {
                name: [
                    {
                        "file": self.index.symbols[sid].file_path,
                        "kind": self.index.symbols[sid].kind,
                        "line": self.index.symbols[sid].line_start,
                        "signature": self.index.symbols[sid].signature
                    }
                    for sid in symbol_ids
                ]
                for name, symbol_ids in self.index.symbol_map.items()
            },
            "architecture": self.get_architecture_overview()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"[INTELLIGENCE] Knowledge graph exported to: {output_path}")


# Singleton instance
_intelligence_instance = None

def get_intelligence(project_root: str = ".") -> CodebaseIntelligence:
    """Get or create intelligence instance"""
    global _intelligence_instance
    if _intelligence_instance is None:
        _intelligence_instance = CodebaseIntelligence(project_root)
    return _intelligence_instance
