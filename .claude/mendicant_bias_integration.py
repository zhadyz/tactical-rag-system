"""
MENDICANT_BIAS INTEGRATION
Connects codebase intelligence to MENDICANT_BIAS workflow

Provides instant answers without redundant file operations
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from codebase_intelligence import get_intelligence, CodebaseIntelligence
from onboarding import check_onboarding_needed, run_onboarding
from incremental_updater import auto_update, IncrementalUpdater
from serena_indexer import get_serena_indexer, SerenaIndexer


class MendicantBiasIntegration:
    """
    High-level interface for MENDICANT_BIAS

    Provides instant codebase intelligence without file reading
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.intelligence = get_intelligence(str(self.project_root))
        self.serena = get_serena_indexer(str(self.project_root))
        self.updater = IncrementalUpdater(str(self.project_root))

        # Auto-initialize if needed
        self._auto_initialize()

    def _auto_initialize(self):
        """
        Automatic initialization on first use

        Runs onboarding if needed, updates if stale
        """
        # Check if onboarding needed
        if check_onboarding_needed(str(self.project_root)):
            print("[MENDICANT_BIAS] First-time project detection - running onboarding...")
            run_onboarding(str(self.project_root))
        else:
            # Check for updates
            index_age = __import__('time').time() - self.intelligence.index.last_updated

            # If index is older than 1 hour, auto-update
            if index_age > 3600:
                print(f"[MENDICANT_BIAS] Index is {int(index_age/60)} minutes old - checking for updates...")
                auto_update(str(self.project_root))

    # ===== INSTANT QUERY INTERFACE =====

    def what_does_file_do(self, file_path: str) -> Dict[str, Any]:
        """
        INSTANT answer to "What does this file do?"

        NO file reading - uses cached intelligence
        """
        summary = self.intelligence.get_file_summary(file_path)

        if not summary:
            return {
                "answer": f"File not indexed: {file_path}",
                "suggestion": "Run update_index() to index this file"
            }

        symbols = self.intelligence.get_symbols_in_file(file_path)
        dependencies = self.intelligence.get_file_dependencies(file_path)
        dependents = self.intelligence.get_dependent_files(file_path)

        return {
            "summary": summary,
            "symbols": symbols,
            "imports": len(dependencies),
            "used_by": len(dependents),
            "dependencies": dependencies[:5],  # Top 5
            "dependents": dependents[:5]
        }

    def where_is_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """
        INSTANT symbol location lookup

        NO searching - direct hash lookup
        """
        locations = self.intelligence.find_symbol(symbol_name)

        if not locations:
            return {
                "answer": f"Symbol '{symbol_name}' not found in index",
                "suggestion": "Check spelling or run update_index()"
            }

        return {
            "symbol": symbol_name,
            "found": len(locations),
            "locations": [
                {
                    "file": loc.file_path,
                    "line": loc.line_start,
                    "kind": loc.kind,
                    "signature": loc.signature
                }
                for loc in locations
            ]
        }

    def what_depends_on_file(self, file_path: str) -> List[str]:
        """
        INSTANT reverse dependency lookup

        Returns files that import/depend on this file
        """
        return self.intelligence.get_dependent_files(file_path)

    def what_is_architecture(self) -> Dict[str, Any]:
        """
        INSTANT architecture overview

        Pre-computed project structure
        """
        return self.intelligence.get_architecture_overview()

    def get_project_stats(self) -> Dict[str, Any]:
        """
        INSTANT project statistics

        Pre-computed metrics
        """
        return self.intelligence.get_stats()

    # ===== NATURAL LANGUAGE QUERY =====

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Natural language query interface

        Examples:
        - "What does auth.py do?"
        - "Where is UserController?"
        - "What files use the database?"
        - "What's the project architecture?"
        """
        return self.intelligence.query(question)

    # ===== UPDATE OPERATIONS =====

    def update_index(self) -> Dict[str, Any]:
        """
        Incremental index update

        Only re-indexes changed files
        """
        return auto_update(str(self.project_root))

    def force_reindex(self) -> Dict[str, Any]:
        """
        Force complete re-indexing

        Use when index is corrupted or after major changes
        """
        print("[MENDICANT_BIAS] Forcing complete re-index...")

        # Clear existing index
        self.intelligence.index.files.clear()
        self.intelligence.index.symbols.clear()
        self.intelligence.index.symbol_map.clear()

        # Run full onboarding
        report = run_onboarding(str(self.project_root))

        return report

    def invalidate_file(self, file_path: str):
        """
        Invalidate cache for specific file

        Forces re-indexing on next update
        """
        self.intelligence.invalidate_cache(file_path)
        print(f"[MENDICANT_BIAS] Invalidated cache for: {file_path}")

    # ===== EXPORT OPERATIONS =====

    def export_knowledge_graph(self, output_path: str = None):
        """
        Export knowledge graph to JSON

        Useful for debugging or external analysis
        """
        if output_path is None:
            output_path = str(self.project_root / ".claude" / "knowledge_graph.json")

        self.intelligence.export_knowledge_graph(output_path)
        print(f"[MENDICANT_BIAS] Knowledge graph exported to: {output_path}")

    def export_architecture_diagram(self, output_path: str = None):
        """
        Export architecture as Mermaid diagram

        Can be rendered in Markdown
        """
        if output_path is None:
            output_path = str(self.project_root / ".claude" / "architecture.md")

        diagram = self._generate_mermaid_diagram()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Project Architecture

")
            f.write("```mermaid
")
            f.write(diagram)
            f.write("
```
")

        print(f"[MENDICANT_BIAS] Architecture diagram exported to: {output_path}")

    def _generate_mermaid_diagram(self) -> str:
        """Generate Mermaid architecture diagram"""
        lines = ["graph TD"]

        # Add top files by dependency count
        file_deps = sorted(
            self.intelligence.index.file_relationships.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]  # Top 20 most connected files

        for i, (file_path, deps) in enumerate(file_deps):
            file_id = f"F{i}"
            file_name = Path(file_path).name

            lines.append(f'    {file_id}["{file_name}"]')

            for dep in deps[:3]:  # Show top 3 deps
                dep_name = Path(dep).name
                # Find or create dep node
                dep_id = None
                for j, (f, _) in enumerate(file_deps):
                    if f == dep:
                        dep_id = f"F{j}"
                        break

                if dep_id:
                    lines.append(f"    {file_id} --> {dep_id}")

        return "
".join(lines)

    # ===== WORKFLOW OPTIMIZATION =====

    def get_files_for_task(self, task_description: str) -> List[str]:
        """
        AI-suggested files for a task

        Uses semantic analysis to suggest relevant files
        """
        # This would use serena's semantic search
        # For now, basic keyword matching

        keywords = task_description.lower().split()
        relevant_files = []

        for file_path, metadata in self.intelligence.index.files.items():
            summary_lower = metadata.summary.lower()

            if any(kw in summary_lower for kw in keywords):
                relevant_files.append(file_path)

            # Check symbols
            for symbol in metadata.symbols:
                symbol_name_lower = symbol.get("name", "").lower()
                if any(kw in symbol_name_lower for kw in keywords):
                    relevant_files.append(file_path)
                    break

        return list(set(relevant_files))[:10]  # Top 10 unique

    def get_impact_analysis(self, file_path: str) -> Dict[str, Any]:
        """
        Impact analysis for file changes

        Shows what would be affected by changing this file
        """
        direct_dependents = self.intelligence.get_dependent_files(file_path)
        all_affected = self.updater.get_affected_files(file_path)

        return {
            "file": file_path,
            "direct_dependents": len(direct_dependents),
            "total_affected": len(all_affected),
            "impact_level": self._calculate_impact_level(len(all_affected)),
            "affected_files": sorted(all_affected)[:20]  # Top 20
        }

    def _calculate_impact_level(self, affected_count: int) -> str:
        """Calculate impact level from affected file count"""
        if affected_count == 0:
            return "NONE"
        elif affected_count <= 5:
            return "LOW"
        elif affected_count <= 20:
            return "MEDIUM"
        elif affected_count <= 50:
            return "HIGH"
        else:
            return "CRITICAL"

    # ===== DEBUGGING & DIAGNOSTICS =====

    def diagnose(self) -> Dict[str, Any]:
        """
        Diagnose intelligence system health

        Returns system status and recommendations
        """
        stats = self.intelligence.get_stats()
        index_age_hours = (__import__('time').time() - self.intelligence.index.last_updated) / 3600

        issues = []
        recommendations = []

        # Check index freshness
        if index_age_hours > 24:
            issues.append(f"Index is {int(index_age_hours)} hours old")
            recommendations.append("Run update_index() to refresh")

        # Check coverage
        changes = self.updater.scan_for_changes()
        total_changes = sum(len(v) for v in changes.values())

        if total_changes > 10:
            issues.append(f"{total_changes} unindexed changes detected")
            recommendations.append("Run update_index() to sync")

        # Check cache size
        if stats["cache_size_mb"] > 100:
            issues.append(f"Cache size is {stats['cache_size_mb']} MB")
            recommendations.append("Consider cleaning old cache data")

        return {
            "status": "HEALTHY" if not issues else "NEEDS_ATTENTION",
            "stats": stats,
            "index_age_hours": round(index_age_hours, 2),
            "unindexed_changes": total_changes,
            "issues": issues,
            "recommendations": recommendations
        }


# ===== GLOBAL INSTANCE =====

_mendicant_bias = None

def get_mendicant_bias(project_root: str = ".") -> MendicantBiasIntegration:
    """Get or create MENDICANT_BIAS instance"""
    global _mendicant_bias
    if _mendicant_bias is None:
        _mendicant_bias = MendicantBiasIntegration(project_root)
    return _mendicant_bias


# ===== CONVENIENCE FUNCTIONS =====

def quick_query(question: str) -> Dict[str, Any]:
    """Quick natural language query"""
    mb = get_mendicant_bias()
    return mb.ask(question)


def file_info(file_path: str) -> Dict[str, Any]:
    """Quick file information"""
    mb = get_mendicant_bias()
    return mb.what_does_file_do(file_path)


def find_symbol(symbol_name: str) -> Dict[str, Any]:
    """Quick symbol lookup"""
    mb = get_mendicant_bias()
    return mb.where_is_symbol(symbol_name)


def project_overview() -> Dict[str, Any]:
    """Quick project overview"""
    mb = get_mendicant_bias()
    return mb.what_is_architecture()


def update() -> Dict[str, Any]:
    """Quick update"""
    mb = get_mendicant_bias()
    return mb.update_index()


if __name__ == "__main__":
    import sys

    # CLI interface
    if len(sys.argv) < 2:
        print("Usage: python mendicant_bias_integration.py <command> [args]")
        print("
Commands:")
        print("  ask <question>    - Natural language query")
        print("  file <path>       - File information")
        print("  symbol <name>     - Symbol lookup")
        print("  overview          - Project overview")
        print("  update            - Update index")
        print("  diagnose          - System health check")
        sys.exit(1)

    command = sys.argv[1]
    mb = get_mendicant_bias()

    if command == "ask":
        question = " ".join(sys.argv[2:])
        result = mb.ask(question)
        print(json.dumps(result, indent=2))

    elif command == "file":
        file_path = sys.argv[2]
        result = mb.what_does_file_do(file_path)
        print(json.dumps(result, indent=2))

    elif command == "symbol":
        symbol_name = sys.argv[2]
        result = mb.where_is_symbol(symbol_name)
        print(json.dumps(result, indent=2))

    elif command == "overview":
        result = mb.what_is_architecture()
        print(json.dumps(result, indent=2))

    elif command == "update":
        result = mb.update_index()
        print(json.dumps(result, indent=2))

    elif command == "diagnose":
        result = mb.diagnose()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
