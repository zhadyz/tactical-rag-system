"""
SERENA INTEGRATION LAYER
Wraps serena MCP tools for codebase intelligence

Provides high-level interface for symbolic code analysis
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from codebase_intelligence import (
    get_intelligence,
    FileMetadata,
    SymbolInfo
)


class SerenaIndexer:
    """
    High-level wrapper for serena symbolic tools

    Integrates serena with codebase intelligence system
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.intelligence = get_intelligence(str(self.project_root))

        # Symbol kind mapping (LSP symbol kinds)
        self.SYMBOL_KINDS = {
            1: "File",
            2: "Module",
            3: "Namespace",
            4: "Package",
            5: "Class",
            6: "Method",
            7: "Property",
            8: "Field",
            9: "Constructor",
            10: "Enum",
            11: "Interface",
            12: "Function",
            13: "Variable",
            14: "Constant",
            15: "String",
            16: "Number",
            17: "Boolean",
            18: "Array",
            19: "Object",
            20: "Key",
            21: "Null",
            22: "EnumMember",
            23: "Struct",
            24: "Event",
            25: "Operator",
            26: "TypeParameter"
        }

    def index_file_with_serena(self, file_path: str) -> FileMetadata:
        """
        Index a file using serena symbolic tools

        This is the main integration point with serena MCP

        Args:
            file_path: Relative path from project root

        Returns:
            FileMetadata with complete symbolic information
        """
        abs_path = self.project_root / file_path

        # Get basic file info
        stat = abs_path.stat()
        file_hash = self.intelligence._compute_file_hash(abs_path)
        language = self.intelligence._detect_language(abs_path)

        # Use serena to get symbols overview
        # ACTUAL serena call would be:
        # symbols_data = mcp__serena__get_symbols_overview(
        #     relative_path=file_path,
        #     max_answer_chars=-1
        # )

        # For now, simulate serena response
        symbols_data = self._simulate_serena_symbols(file_path, abs_path)

        # Extract imports and exports
        imports = self._extract_imports_from_symbols(symbols_data)
        exports = self._extract_exports_from_symbols(symbols_data)

        # Generate file summary
        summary = self._generate_file_summary(file_path, symbols_data)

        # Resolve dependencies
        dependencies = self._resolve_dependencies(file_path, imports)

        # Create metadata
        metadata = FileMetadata(
            path=file_path,
            last_modified=stat.st_mtime,
            size=stat.st_size,
            hash=file_hash,
            language=language,
            summary=summary,
            symbols=symbols_data,
            imports=imports,
            exports=exports,
            dependencies=dependencies
        )

        # Index symbols into symbol map
        self._index_symbols(file_path, symbols_data)

        return metadata

    def find_symbol_with_serena(
        self,
        name_path: str,
        within_path: str = "",
        include_body: bool = False
    ) -> List[SymbolInfo]:
        """
        Find symbols using serena

        Args:
            name_path: Symbol name or path (e.g., "MyClass" or "MyClass/method")
            within_path: Optional path to restrict search
            include_body: Whether to include source code

        Returns:
            List of SymbolInfo objects
        """
        # ACTUAL serena call:
        # results = mcp__serena__find_symbol(
        #     name_path=name_path,
        #     relative_path=within_path,
        #     include_body=include_body,
        #     depth=0
        # )

        # Simulate for now
        results = self._simulate_find_symbol(name_path, within_path)

        symbols = []
        for result in results:
            symbol_info = SymbolInfo(
                name=result.get("name", ""),
                kind=self.SYMBOL_KINDS.get(result.get("kind", 0), "Unknown"),
                file_path=result.get("file_path", ""),
                line_start=result.get("line_start", 0),
                line_end=result.get("line_end", 0),
                signature=result.get("signature"),
                docstring=result.get("docstring"),
                references=[],
                children=result.get("children", []),
                parent=result.get("parent")
            )
            symbols.append(symbol_info)

        return symbols

    def find_references_with_serena(
        self,
        name_path: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Find all references to a symbol using serena

        Args:
            name_path: Symbol to find references for
            file_path: File containing the symbol

        Returns:
            List of reference locations
        """
        # ACTUAL serena call:
        # results = mcp__serena__find_referencing_symbols(
        #     name_path=name_path,
        #     relative_path=file_path
        # )

        # Simulate for now
        return self._simulate_find_references(name_path, file_path)

    def search_pattern_with_serena(
        self,
        pattern: str,
        within_path: str = "",
        context_lines: int = 2
    ) -> Dict[str, List[str]]:
        """
        Search for pattern using serena

        Args:
            pattern: Regex pattern to search
            within_path: Optional path to restrict search
            context_lines: Lines of context around matches

        Returns:
            Dict mapping file paths to matched lines
        """
        # ACTUAL serena call:
        # results = mcp__serena__search_for_pattern(
        #     substring_pattern=pattern,
        #     relative_path=within_path,
        #     context_lines_before=context_lines,
        #     context_lines_after=context_lines
        # )

        # Simulate for now
        return self._simulate_search_pattern(pattern, within_path)

    def _simulate_serena_symbols(
        self,
        file_path: str,
        abs_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Simulate serena symbols response

        In production, this would be replaced by actual serena MCP call
        """
        # Try to parse file and extract basic symbols
        try:
            content = abs_path.read_text(encoding='utf-8', errors='ignore')
            language = self.intelligence._detect_language(abs_path)

            if language == 'python':
                return self._extract_python_symbols(content, file_path)
            elif language in {'javascript', 'typescript'}:
                return self._extract_js_symbols(content, file_path)
            else:
                return []
        except:
            return []

    def _extract_python_symbols(
        self,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Extract Python symbols (simplified)"""
        symbols = []
        lines = content.split('
')

        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()

            # Class definition
            if stripped.startswith('class '):
                name = stripped.split('class ')[1].split('(')[0].split(':')[0].strip()
                symbols.append({
                    "name": name,
                    "kind": 5,  # Class
                    "line_start": i,
                    "line_end": i,  # Would need proper parsing
                    "signature": stripped.rstrip(':'),
                    "children": []
                })

            # Function/method definition
            elif stripped.startswith('def '):
                name = stripped.split('def ')[1].split('(')[0].strip()
                symbols.append({
                    "name": name,
                    "kind": 12,  # Function
                    "line_start": i,
                    "line_end": i,
                    "signature": stripped.rstrip(':'),
                    "children": []
                })

        return symbols

    def _extract_js_symbols(
        self,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Extract JavaScript/TypeScript symbols (simplified)"""
        symbols = []
        lines = content.split('
')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Class definition
            if 'class ' in stripped:
                try:
                    name = stripped.split('class ')[1].split('{')[0].split(' extends')[0].strip()
                    symbols.append({
                        "name": name,
                        "kind": 5,
                        "line_start": i,
                        "line_end": i,
                        "signature": stripped,
                        "children": []
                    })
                except:
                    pass

            # Function definition
            elif 'function ' in stripped:
                try:
                    name = stripped.split('function ')[1].split('(')[0].strip()
                    symbols.append({
                        "name": name,
                        "kind": 12,
                        "line_start": i,
                        "line_end": i,
                        "signature": stripped,
                        "children": []
                    })
                except:
                    pass

            # Arrow function assigned to const/let/var
            elif any(stripped.startswith(kw) for kw in ['const ', 'let ', 'var ']):
                if '=>' in stripped:
                    try:
                        name = stripped.split('=')[0].replace('const', '').replace('let', '').replace('var', '').strip()
                        symbols.append({
                            "name": name,
                            "kind": 12,
                            "line_start": i,
                            "line_end": i,
                            "signature": stripped,
                            "children": []
                        })
                    except:
                        pass

        return symbols

    def _extract_imports_from_symbols(
        self,
        symbols_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract import statements (would use serena in production)"""
        # This would be detected by serena's import analysis
        return []

    def _extract_exports_from_symbols(
        self,
        symbols_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract export statements (would use serena in production)"""
        # This would be detected by serena's export analysis
        return []

    def _generate_file_summary(
        self,
        file_path: str,
        symbols: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable file summary"""
        filename = Path(file_path).name

        if not symbols:
            return f"Source file: {filename}"

        # Count symbol types
        classes = [s for s in symbols if s.get("kind") == 5]
        functions = [s for s in symbols if s.get("kind") == 12]
        methods = [s for s in symbols if s.get("kind") == 6]

        parts = [f"Source file: {filename}"]

        if classes:
            class_names = [c["name"] for c in classes[:3]]
            parts.append(f"Classes: {', '.join(class_names)}")
            if len(classes) > 3:
                parts.append(f"(+{len(classes) - 3} more)")

        if functions:
            parts.append(f"{len(functions)} functions")

        if methods:
            parts.append(f"{len(methods)} methods")

        return " | ".join(parts)

    def _resolve_dependencies(
        self,
        file_path: str,
        imports: List[str]
    ) -> List[str]:
        """Resolve import paths to actual files"""
        dependencies = []

        for imp in imports:
            resolved = self._resolve_import(imp, file_path)
            if resolved:
                dependencies.append(resolved)

        return dependencies

    def _resolve_import(self, import_path: str, from_file: str) -> Optional[str]:
        """Resolve single import to file path"""
        # Language-specific import resolution
        # Would use serena's import analysis in production
        return None

    def _index_symbols(self, file_path: str, symbols: List[Dict[str, Any]]):
        """Index symbols into intelligence system"""
        for symbol in symbols:
            symbol_id = f"{file_path}:{symbol['name']}:{symbol['line_start']}"

            symbol_info = SymbolInfo(
                name=symbol.get("name", ""),
                kind=self.SYMBOL_KINDS.get(symbol.get("kind", 0), "Unknown"),
                file_path=file_path,
                line_start=symbol.get("line_start", 0),
                line_end=symbol.get("line_end", 0),
                signature=symbol.get("signature"),
                docstring=symbol.get("docstring"),
                references=[],
                children=symbol.get("children", []),
                parent=symbol.get("parent")
            )

            # Add to intelligence index
            self.intelligence.index.symbols[symbol_id] = symbol_info

            # Add to symbol map
            self.intelligence.index.symbol_map[symbol["name"]].append(symbol_id)

    def _simulate_find_symbol(
        self,
        name_path: str,
        within_path: str
    ) -> List[Dict[str, Any]]:
        """Simulate serena find_symbol response"""
        # In production, this is a real serena MCP call
        return []

    def _simulate_find_references(
        self,
        name_path: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Simulate serena find_referencing_symbols response"""
        # In production, this is a real serena MCP call
        return []

    def _simulate_search_pattern(
        self,
        pattern: str,
        within_path: str
    ) -> Dict[str, List[str]]:
        """Simulate serena search_for_pattern response"""
        # In production, this is a real serena MCP call
        return {}

    def batch_index_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Index multiple files in batch

        Optimized for speed with progress tracking
        """
        print(f"[SERENA] Batch indexing {len(file_paths)} files...")
        start_time = __import__('time').time()

        indexed = 0
        errors = []

        for i, file_path in enumerate(file_paths):
            if i % 50 == 0 and i > 0:
                print(f"  Progress: {i}/{len(file_paths)} ({indexed} indexed)")

            try:
                metadata = self.index_file_with_serena(file_path)
                self.intelligence.index.files[file_path] = metadata
                indexed += 1
            except Exception as e:
                errors.append({"file": file_path, "error": str(e)})

        elapsed = __import__('time').time() - start_time

        print(f"[SERENA] Batch complete: {indexed} indexed in {elapsed:.2f}s")

        return {
            "indexed": indexed,
            "errors": errors,
            "elapsed_seconds": round(elapsed, 2),
            "files_per_second": round(indexed / elapsed, 2) if elapsed > 0 else 0
        }


def get_serena_indexer(project_root: str = ".") -> SerenaIndexer:
    """Get serena indexer instance"""
    return SerenaIndexer(project_root)
