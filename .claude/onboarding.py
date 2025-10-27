#!/usr/bin/env python3
"""
MENDICANT_BIAS v1.6 - Automated Project Onboarding
Analyzes project structure and generates memory context
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import Counter

# Add memory module to path
sys.path.append(str(Path(__file__).parent / "memory"))


class ProjectAnalyzer:
    """Analyze project structure and generate onboarding report"""
    
    # Language detection by extension
    LANGUAGE_EXTENSIONS = {
        "Python": {".py", ".pyw", ".pyx", ".pyd"},
        "JavaScript": {".js", ".jsx", ".mjs", ".cjs"},
        "TypeScript": {".ts", ".tsx"},
        "Java": {".java"},
        "Go": {".go"},
        "Rust": {".rs"},
        "C++": {".cpp", ".cc", ".cxx", ".hpp", ".h", ".hxx"},
        "C": {".c", ".h"},
        "C#": {".cs"},
        "Ruby": {".rb"},
        "PHP": {".php"},
        "Swift": {".swift"},
        "Kotlin": {".kt", ".kts"},
        "Scala": {".scala"},
        "Shell": {".sh", ".bash", ".zsh"},
        "PowerShell": {".ps1", ".psm1"},
        "SQL": {".sql"},
        "HTML": {".html", ".htm"},
        "CSS": {".css", ".scss", ".sass", ".less"},
        "Markdown": {".md", ".markdown"},
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "Python": {
            "Django": ["manage.py", "django"],
            "Flask": ["app.py", "flask"],
            "FastAPI": ["fastapi", "uvicorn"],
            "Pyramid": ["pyramid"],
            "Tornado": ["tornado"],
        },
        "JavaScript": {
            "React": ["react", "react-dom"],
            "Vue": ["vue"],
            "Angular": ["@angular/core"],
            "Next.js": ["next"],
            "Express": ["express"],
            "NestJS": ["@nestjs/core"],
        },
        "TypeScript": {
            "Next.js": ["next"],
            "NestJS": ["@nestjs/core"],
            "Angular": ["@angular/core"],
        },
        "Java": {
            "Spring Boot": ["spring-boot"],
            "Micronaut": ["micronaut"],
            "Quarkus": ["quarkus"],
        },
        "Go": {
            "Gin": ["github.com/gin-gonic/gin"],
            "Echo": ["github.com/labstack/echo"],
            "Fiber": ["github.com/gofiber/fiber"],
        },
        "Rust": {
            "Actix": ["actix-web"],
            "Rocket": ["rocket"],
            "Axum": ["axum"],
        }
    }
    
    # Config file patterns
    CONFIG_FILES = {
        "package.json": "npm/Node.js project",
        "requirements.txt": "Python pip dependencies",
        "Pipfile": "Python pipenv project",
        "pyproject.toml": "Python modern packaging",
        "Cargo.toml": "Rust project",
        "go.mod": "Go modules",
        "pom.xml": "Java Maven project",
        "build.gradle": "Java Gradle project",
        "Gemfile": "Ruby Bundler project",
        "composer.json": "PHP Composer project",
        "Dockerfile": "Docker containerization",
        "docker-compose.yml": "Docker Compose multi-container",
        ".github/workflows": "GitHub Actions CI/CD",
        ".gitlab-ci.yml": "GitLab CI/CD",
        "Jenkinsfile": "Jenkins CI/CD",
        "pytest.ini": "pytest testing",
        "jest.config.js": "Jest testing",
        ".eslintrc": "ESLint linting",
        ".prettierrc": "Prettier formatting",
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_path = project_root / ".claude" / "config.json"
        self.load_config()
        
    def load_config(self):
        """Load framework configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"indexing": {"excluded_patterns": []}}
    
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded from analysis"""
        excluded = self.config.get("indexing", {}).get("excluded_patterns", [])
        path_str = str(path.relative_to(self.project_root))
        
        for pattern in excluded:
            # Simple glob matching
            if "*" in pattern:
                if pattern.replace("**", "").replace("*", "") in path_str:
                    return True
            elif pattern in path_str:
                return True
        
        return False
    
    def scan_project(self) -> Dict:
        """Scan project and collect statistics"""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "files_by_extension": Counter(),
            "files_by_language": Counter(),
            "directory_structure": {},
            "config_files": [],
            "largest_files": [],
            "total_size_bytes": 0,
        }
        
        for path in self.project_root.rglob("*"):
            if self.should_exclude(path):
                continue
            
            if path.is_file():
                stats["total_files"] += 1
                stats["files_by_extension"][path.suffix] += 1
                
                # Detect language
                for lang, exts in self.LANGUAGE_EXTENSIONS.items():
                    if path.suffix in exts:
                        stats["files_by_language"][lang] += 1
                        break
                
                # Track config files
                for config, desc in self.CONFIG_FILES.items():
                    if config in str(path):
                        stats["config_files"].append({
                            "file": str(path.relative_to(self.project_root)),
                            "type": desc
                        })
                
                # Track size
                try:
                    size = path.stat().st_size
                    stats["total_size_bytes"] += size
                    stats["largest_files"].append({
                        "file": str(path.relative_to(self.project_root)),
                        "size_mb": round(size / (1024 * 1024), 2)
                    })
                except Exception:
                    pass
            
            elif path.is_dir():
                stats["total_dirs"] += 1
        
        # Sort largest files
        stats["largest_files"].sort(key=lambda x: x["size_mb"], reverse=True)
        stats["largest_files"] = stats["largest_files"][:10]
        
        return stats
    
    def detect_frameworks(self, stats: Dict) -> List[str]:
        """Detect frameworks based on project analysis"""
        frameworks = []
        
        # Get primary language
        primary_lang = stats["files_by_language"].most_common(1)
        if not primary_lang:
            return frameworks
        
        primary_lang = primary_lang[0][0]
        
        # Check framework patterns
        if primary_lang in self.FRAMEWORK_PATTERNS:
            for framework, patterns in self.FRAMEWORK_PATTERNS[primary_lang].items():
                # Check in config files
                for config in stats["config_files"]:
                    config_path = self.project_root / config["file"]
                    if config_path.exists():
                        try:
                            content = config_path.read_text()
                            if any(pattern in content for pattern in patterns):
                                frameworks.append(framework)
                                break
                        except Exception:
                            pass
        
        return frameworks
    
    def estimate_complexity(self, stats: Dict) -> str:
        """Estimate project complexity"""
        file_count = stats["total_files"]
        lang_count = len(stats["files_by_language"])
        
        if file_count < 50:
            size = "Small"
        elif file_count < 200:
            size = "Medium"
        elif file_count < 1000:
            size = "Large"
        else:
            size = "Very Large"
        
        if lang_count == 1:
            diversity = "Single Language"
        elif lang_count <= 3:
            diversity = "Multi-Language"
        else:
            diversity = "Polyglot"
        
        return f"{size} {diversity} Project"
    
    def generate_report(self) -> Dict:
        """Generate comprehensive onboarding report"""
        print("🔍 Analyzing project structure...")
        
        stats = self.scan_project()
        frameworks = self.detect_frameworks(stats)
        complexity = self.estimate_complexity(stats)
        
        # Get primary language
        primary_lang = stats["files_by_language"].most_common(1)
        primary_lang = primary_lang[0][0] if primary_lang else "Unknown"
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "project_root": str(self.project_root),
            "summary": {
                "primary_language": primary_lang,
                "frameworks": frameworks,
                "complexity": complexity,
                "total_files": stats["total_files"],
                "total_directories": stats["total_dirs"],
                "total_size_mb": round(stats["total_size_bytes"] / (1024 * 1024), 2),
            },
            "languages": dict(stats["files_by_language"].most_common()),
            "extensions": dict(stats["files_by_extension"].most_common(20)),
            "config_files": stats["config_files"],
            "largest_files": stats["largest_files"],
            "tech_stack": self.detect_tech_stack(stats),
        }
        
        return report
    
    def detect_tech_stack(self, stats: Dict) -> Dict:
        """Detect technology stack"""
        stack = {
            "backend": [],
            "frontend": [],
            "database": [],
            "devops": [],
            "testing": [],
            "other": []
        }
        
        config_types = [c["type"] for c in stats["config_files"]]
        
        # Backend
        if "Django" in config_types or any("django" in c["file"] for c in stats["config_files"]):
            stack["backend"].append("Django")
        if "Flask" in config_types or any("flask" in c["file"] for c in stats["config_files"]):
            stack["backend"].append("Flask")
        if any("fastapi" in c["file"] for c in stats["config_files"]):
            stack["backend"].append("FastAPI")
        
        # Frontend
        if any("react" in c["file"] for c in stats["config_files"]):
            stack["frontend"].append("React")
        if any("vue" in c["file"] for c in stats["config_files"]):
            stack["frontend"].append("Vue")
        if any("angular" in c["file"] for c in stats["config_files"]):
            stack["frontend"].append("Angular")
        
        # Database
        for config in stats["config_files"]:
            if any(db in config["file"].lower() for db in ["postgres", "mysql", "mongodb", "redis", "sqlite"]):
                stack["database"].append(config["file"].split("/")[-1])
        
        # DevOps
        if "Docker containerization" in config_types:
            stack["devops"].append("Docker")
        if "Docker Compose multi-container" in config_types:
            stack["devops"].append("Docker Compose")
        if any("GitHub Actions" in c["type"] for c in stats["config_files"]):
            stack["devops"].append("GitHub Actions")
        
        # Testing
        if any("pytest" in c["file"] for c in stats["config_files"]):
            stack["testing"].append("pytest")
        if any("jest" in c["file"] for c in stats["config_files"]):
            stack["testing"].append("Jest")
        
        return stack
    
    def save_report(self, report: Dict):
        """Save report to memory"""
        # Save as JSON
        memory_dir = self.project_root / ".claude" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = memory_dir / "onboarding_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Report saved to {report_path}")
        
        # Also save to memory system
        try:
            from mendicant_memory import memory
            memory.save_state("onboarding", report)
            print("✅ Report saved to memory system")
        except Exception as e:
            print(f"⚠️  Could not save to memory system: {e}")
    
    def print_report(self, report: Dict):
        """Print formatted report"""
        print("\n" + "="*70)
        print("PROJECT ONBOARDING REPORT")
        print("="*70)
        
        summary = report["summary"]
        print(f"\n📊 Summary:")
        print(f"  Primary Language: {summary['primary_language']}")
        print(f"  Complexity: {summary['complexity']}")
        print(f"  Files: {summary['total_files']:,}")
        print(f"  Directories: {summary['total_directories']:,}")
        print(f"  Total Size: {summary['total_size_mb']:.2f} MB")
        
        if summary["frameworks"]:
            print(f"\n🚀 Frameworks:")
            for fw in summary["frameworks"]:
                print(f"  - {fw}")
        
        print(f"\n💻 Languages:")
        for lang, count in list(report["languages"].items())[:5]:
            print(f"  - {lang}: {count} files")
        
        if report["tech_stack"]["backend"]:
            print(f"\n🔧 Backend:")
            for tech in report["tech_stack"]["backend"]:
                print(f"  - {tech}")
        
        if report["tech_stack"]["frontend"]:
            print(f"\n🎨 Frontend:")
            for tech in report["tech_stack"]["frontend"]:
                print(f"  - {tech}")
        
        if report["tech_stack"]["database"]:
            print(f"\n💾 Database:")
            for tech in report["tech_stack"]["database"]:
                print(f"  - {tech}")
        
        if report["tech_stack"]["devops"]:
            print(f"\n🐳 DevOps:")
            for tech in report["tech_stack"]["devops"]:
                print(f"  - {tech}")
        
        if report["tech_stack"]["testing"]:
            print(f"\n🧪 Testing:")
            for tech in report["tech_stack"]["testing"]:
                print(f"  - {tech}")
        
        if report["config_files"]:
            print(f"\n📝 Configuration Files:")
            for config in report["config_files"][:10]:
                print(f"  - {config['file']} ({config['type']})")
        
        print("\n" + "="*70)


def main():
    """Main entry point"""
    project_root = Path.cwd()
    
    print("🚀 MENDICANT_BIAS v1.6 - Project Onboarding")
    print(f"📁 Project: {project_root}\n")
    
    analyzer = ProjectAnalyzer(project_root)
    report = analyzer.generate_report()
    analyzer.print_report(report)
    analyzer.save_report(report)
    
    print("\n✅ Onboarding complete!")
    print("💡 Use /awaken to load this context into memory\n")


if __name__ == "__main__":
    main()
