"""
INCREMENTAL UPDATE SYSTEM
Smart cache invalidation and incremental re-indexing

Only re-index what changed - MAXIMUM SPEED
"""

import os
import time
from pathlib import Path
from typing import List, Set, Dict, Any
from collections import deque

from codebase_intelligence import get_intelligence, FileMetadata


class IncrementalUpdater:
    """
    Monitors file changes and updates index incrementally

    Optimized for speed - only processes changed files
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.intelligence = get_intelligence(str(self.project_root))
        self.change_log: List[Dict[str, Any]] = []

    def scan_for_changes(self) -> Dict[str, List[str]]:
        """
        Scan project for file changes

        Returns categorized changes: added, modified, deleted
        """
        print("[UPDATE] Scanning for file changes...")
        start_time = time.time()

        changes = {
            "added": [],
            "modified": [],
            "deleted": []
        }

        # Get current files on disk
        current_files = set()
        ignore_dirs = {
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            '.venv', 'dist', 'build', '.cache', '.pytest_cache',
            '.mypy_cache', 'vendor', 'target', 'bin', 'obj', '.claude'
        }

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            root_path = Path(root)

            for file in files:
                file_path = root_path / file
                if self._is_indexable(file_path):
                    rel_path = str(file_path.relative_to(self.project_root))
                    current_files.add(rel_path)

        # Compare with index
        indexed_files = set(self.intelligence.index.files.keys())

        # Find added files
        added = current_files - indexed_files
        changes["added"] = sorted(added)

        # Find deleted files
        deleted = indexed_files - current_files
        changes["deleted"] = sorted(deleted)

        # Find modified files
        for file_path in current_files & indexed_files:
            abs_path = self.project_root / file_path
            if self.intelligence.needs_update(abs_path):
                changes["modified"].append(file_path)

        elapsed = time.time() - start_time
        total_changes = len(changes["added"]) + len(changes["modified"]) + len(changes["deleted"])

        print(f"[UPDATE] Scan complete in {elapsed:.2f}s")
        print(f"  Added: {len(changes['added'])}")
        print(f"  Modified: {len(changes['modified'])}")
        print(f"  Deleted: {len(changes['deleted'])}")
        print(f"  Total changes: {total_changes}")

        return changes

    def _is_indexable(self, file_path: Path) -> bool:
        """Check if file should be indexed"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.m', '.mm'
        }

        ignore_extensions = {
            '.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe',
            '.o', '.a', '.lib', '.bin', '.dat', '.lock'
        }

        return (
            file_path.suffix.lower() in code_extensions and
            file_path.suffix.lower() not in ignore_extensions
        )

    def update_index(self, changes: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Update index with changes

        Processes only changed files
        """
        if changes is None:
            changes = self.scan_for_changes()

        print("[UPDATE] Updating index...")
        start_time = time.time()

        # Handle deletions
        for file_path in changes["deleted"]:
            self._handle_deletion(file_path)

        # Handle additions and modifications
        files_to_index = changes["added"] + changes["modified"]

        if files_to_index:
            self._index_files(files_to_index)

        # Rebuild relationship map for affected files
        self._rebuild_relationships(files_to_index)

        # Update timestamp
        self.intelligence.index.last_updated = time.time()

        # Save index
        self.intelligence._save_index()

        elapsed = time.time() - start_time

        report = {
            "elapsed_seconds": round(elapsed, 2),
            "changes_processed": len(files_to_index) + len(changes["deleted"]),
            "files_indexed": len(files_to_index),
            "files_deleted": len(changes["deleted"]),
            "total_files_in_index": len(self.intelligence.index.files),
            "total_symbols": len(self.intelligence.index.symbols)
        }

        print(f"[UPDATE] Update complete in {elapsed:.2f}s")
        return report

    def _handle_deletion(self, file_path: str):
        """
        Handle file deletion

        Invalidates cache and removes from index
        """
        print(f"  Removing: {file_path}")
        self.intelligence.invalidate_cache(file_path)

        self.change_log.append({
            "timestamp": time.time(),
            "action": "delete",
            "file": file_path
        })

    def _index_files(self, file_paths: List[str]):
        """
        Index a list of files

        Uses serena symbolic tools
        """
        print(f"  Indexing {len(file_paths)} files...")

        for i, file_path in enumerate(file_paths):
            if i % 10 == 0 and i > 0:
                print(f"    Progress: {i}/{len(file_paths)}")

            abs_path = self.project_root / file_path
            if not abs_path.exists():
                continue

            try:
                # Get file metadata
                stat = abs_path.stat()
                file_hash = self.intelligence._compute_file_hash(abs_path)
                language = self.intelligence._detect_language(abs_path)

                # PLACEHOLDER: Call serena tools here
                # symbols = mcp__serena__get_symbols_overview(file_path)
                # imports = extract_imports(file_path)

                metadata = FileMetadata(
                    path=file_path,
                    last_modified=stat.st_mtime,
                    size=stat.st_size,
                    hash=file_hash,
                    language=language,
                    summary=f"Source file: {Path(file_path).name}",
                    symbols=[],
                    imports=[],
                    exports=[],
                    dependencies=[]
                )

                self.intelligence.index.files[file_path] = metadata

                self.change_log.append({
                    "timestamp": time.time(),
                    "action": "index",
                    "file": file_path
                })

            except Exception as e:
                print(f"    Error indexing {file_path}: {e}")

    def _rebuild_relationships(self, affected_files: List[str]):
        """
        Rebuild relationship map for affected files

        Also updates dependent files
        """
        # Files that need relationship update
        files_to_update = set(affected_files)

        # Add files that depend on changed files
        for file_path in affected_files:
            dependents = self.intelligence.get_dependent_files(file_path)
            files_to_update.update(dependents)

        # Rebuild relationships
        for file_path in files_to_update:
            if file_path not in self.intelligence.index.files:
                continue

            metadata = self.intelligence.index.files[file_path]
            dependencies = []

            for imp in metadata.imports:
                # Resolve import to file
                resolved = self._resolve_import(imp, file_path)
                if resolved:
                    dependencies.append(resolved)

            metadata.dependencies = dependencies
            self.intelligence.index.file_relationships[file_path] = dependencies

    def _resolve_import(self, import_path: str, from_file: str) -> str:
        """Resolve import to actual file path"""
        # Simplified - would need language-specific logic
        base_dir = Path(from_file).parent

        possible_paths = [
            self.project_root / base_dir / f"{import_path}.py",
            self.project_root / base_dir / f"{import_path}.js",
            self.project_root / base_dir / f"{import_path}.ts",
        ]

        for path in possible_paths:
            try:
                rel = str(path.relative_to(self.project_root))
                if rel in self.intelligence.index.files:
                    return rel
            except:
                continue

        return None

    def get_affected_files(self, changed_file: str) -> Set[str]:
        """
        Get all files affected by a change

        Returns transitive closure of dependent files
        """
        affected = set()
        to_process = deque([changed_file])

        while to_process:
            file_path = to_process.popleft()
            if file_path in affected:
                continue

            affected.add(file_path)

            # Add direct dependents
            dependents = self.intelligence.get_dependent_files(file_path)
            for dep in dependents:
                if dep not in affected:
                    to_process.append(dep)

        return affected

    def watch_and_update(self, interval: int = 60):
        """
        Continuous monitoring mode

        Checks for changes every `interval` seconds
        """
        print(f"[UPDATE] Starting watch mode (interval: {interval}s)")
        print("[UPDATE] Press Ctrl+C to stop")

        try:
            while True:
                time.sleep(interval)
                changes = self.scan_for_changes()

                total_changes = (
                    len(changes["added"]) +
                    len(changes["modified"]) +
                    len(changes["deleted"])
                )

                if total_changes > 0:
                    print(f"
[UPDATE] Detected {total_changes} changes")
                    self.update_index(changes)
                else:
                    print(".", end="", flush=True)

        except KeyboardInterrupt:
            print("
[UPDATE] Watch mode stopped")

    def get_change_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent change log"""
        return self.change_log[-limit:]


def auto_update(project_root: str = ".") -> Dict[str, Any]:
    """
    Convenience function for auto-updating

    Call this periodically or on demand
    """
    updater = IncrementalUpdater(project_root)
    changes = updater.scan_for_changes()

    if any(len(v) > 0 for v in changes.values()):
        return updater.update_index(changes)
    else:
        return {
            "message": "No changes detected",
            "elapsed_seconds": 0,
            "changes_processed": 0
        }


if __name__ == "__main__":
    import sys

    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    mode = sys.argv[2] if len(sys.argv) > 2 else "update"

    updater = IncrementalUpdater(project_root)

    if mode == "watch":
        updater.watch_and_update()
    else:
        report = auto_update(project_root)
        print(f"
Update report: {report}")
