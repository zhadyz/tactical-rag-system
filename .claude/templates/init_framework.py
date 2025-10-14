#!/usr/bin/env python3
"""
MENDICANT_BIAS Framework Initializer
Deploys the intelligent multi-agent framework to any software project
"""

import argparse
import os
import shutil
import json
from pathlib import Path
from datetime import datetime


# Project type to domain mapping
PROJECT_DOMAINS = {
    "web-app": "web applications and full-stack development",
    "api": "API design and backend services",
    "data-pipeline": "data engineering and ETL systems",
    "ml-system": "machine learning and AI systems",
    "mobile-app": "mobile application development",
    "cli-tool": "command-line tools and utilities",
    "library": "software libraries and SDKs",
    "infrastructure": "DevOps and infrastructure automation",
    "custom": "software development"
}

# Project type specific expertise for hollowed_eyes
PROJECT_EXPERTISE = {
    "web-app": """## Web Application Expertise
- Frontend architecture (React, Vue, Angular)
- Backend services (REST APIs, GraphQL)
- Database design and optimization
- Authentication and authorization
- State management and caching
- Performance optimization""",

    "api": """## API Development Expertise
- REST and GraphQL API design
- API versioning and documentation
- Rate limiting and authentication
- Microservices architecture
- API gateway patterns
- Backend optimization""",

    "data-pipeline": """## Data Engineering Expertise
- ETL pipeline design
- Data transformation and validation
- Workflow orchestration (Airflow, Prefect)
- Batch and stream processing
- Data quality and monitoring
- Distributed computing""",

    "ml-system": """## Machine Learning Expertise
- Model training and evaluation
- Feature engineering
- ML pipeline orchestration
- Model serving and deployment
- A/B testing frameworks
- MLOps best practices""",

    "mobile-app": """## Mobile Development Expertise
- iOS/Android native development
- Cross-platform frameworks (React Native, Flutter)
- Mobile UI/UX patterns
- Offline-first architecture
- Push notifications and deep linking
- App store deployment""",

    "custom": """## Software Development Expertise
- Architecture and design patterns
- Algorithm optimization
- System design and scalability
- Code quality and maintainability
- Testing and debugging
- Performance optimization"""
}


def create_agent_configs(target_dir: Path, config: dict):
    """Generate agent configuration files"""

    agents_dir = target_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    domain = PROJECT_DOMAINS.get(config['project_type'], "software development")
    expertise = PROJECT_EXPERTISE.get(config['project_type'], PROJECT_EXPERTISE['custom'])

    # Copy mendicant_bias (orchestrator) - mostly generic
    src_mb = Path(__file__).parent.parent / "agents" / "mendicant_bias.md"
    if src_mb.exists():
        shutil.copy(src_mb, agents_dir / "mendicant_bias.md")
        print(f"[OK] Created mendicant_bias.md (orchestrator)")

    # Create hollowed_eyes (developer) with project-specific expertise
    hollowed_eyes = f"""---
name: hollowed_eyes
description: Elite main developer agent specializing in {domain}. Use this agent for implementing features, refactoring code, solving algorithmic challenges, and building core functionality.
model: sonnet
color: cyan
---

You are HOLLOWED_EYES, an elite software architect and developer specializing in {config['project_name']}. When invoked by Claude Code (the orchestrator), you implement features, solve complex problems, and push the boundaries of what's possible.

# CORE IDENTITY

You are the primary developer - the one who writes the code that matters. You understand both low-level implementation details and high-level architectural patterns. You build things that work, scale, and amaze.

Your agent identifier is: `hollowed_eyes`

# PROJECT CONTEXT

**Project**: {config['project_name']}
**Type**: {config['project_type']}
**Tech Stack**: {config['tech_stack']}
**Mission**: {config['mission']}

{expertise}

# INVOCATION MODEL

When the orchestrator invokes you:
1. Receive Assignment
2. Analyze codebase and requirements
3. Design solution
4. Implement with excellence
5. Test your work
6. Document breakthroughs
7. Report results with memory persistence

# QUALITY STANDARDS

- **Correctness**: Code does exactly what it should
- **Robustness**: Handles edge cases gracefully
- **Performance**: Efficient algorithms and data structures
- **Maintainability**: Clean, readable code
- **Testability**: Easy to test
- **Documentation**: Clear explanations

# MEMORY PERSISTENCE (CRITICAL)

After completing your task:

```python
import sys
sys.path.append('.claude/memory')
from mendicant_bias_state import memory

report = {{
    "task": "Brief description",
    "status": "COMPLETED",
    "duration": "Approximate time",
    "summary": {{
        "implemented": ["What you built"],
        "files_modified": ["file1.py", "file2.py"],
        "breakthroughs": ["Novel insights"]
    }}
}}
memory.save_agent_report("hollowed_eyes", report)
```

You are the architect of innovation. Build with precision and excellence. You are HOLLOWED_EYES.
"""

    (agents_dir / "hollowed_eyes.md").write_text(hollowed_eyes)
    print(f"[OK] Created hollowed_eyes.md (developer)")

    # Copy other agents (they're mostly generic)
    for agent_name in ["the_didact", "loveless", "zhadyz-devops-orchestrator"]:
        src = Path(__file__).parent.parent / "agents" / f"{agent_name}.md"
        dst = agents_dir / f"{agent_name.replace('-devops-orchestrator', '')}.md"

        if src.exists():
            # Read and replace placeholders
            content = src.read_text()
            content = content.replace("RAG system", config['project_name'])
            content = content.replace("RAG", config['project_name'])

            # Write to destination
            if agent_name == "zhadyz-devops-orchestrator":
                (agents_dir / "zhadyz.md").write_text(content)
            else:
                dst.write_text(content)

            print(f"[OK] Created {dst.name}")


def create_memory_files(target_dir: Path, config: dict):
    """Generate memory system files"""

    memory_dir = target_dir / ".claude" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "agent_reports").mkdir(exist_ok=True)

    # Copy Python state manager (it's generic)
    src_state = Path(__file__).parent.parent / "memory" / "mendicant_bias_state.py"
    if src_state.exists():
        shutil.copy(src_state, memory_dir / "mendicant_bias_state.py")
        print(f"[OK] Created mendicant_bias_state.py")

    # Create mission_context.md
    mission_context = f"""# Mission Context - {config['project_name']}

**Last Updated**: {datetime.now().strftime("%Y-%m-%d")} (Auto-generated at initialization)

## Current Mission
{config['mission']}

## Phase
**Phase 1 of 5: Foundation**

Progress: 20% complete

## Active Objectives

1. [TODO] Set up project structure
2. [TODO] Establish development workflow
3. [TODO] Implement core features
4. [TODO] Deploy agent system integration

## Current Technical State

### Architecture
- **Type**: {config['project_type']}
- **Tech Stack**: {config['tech_stack']}
- **Version**: {config.get('version', '0.1.0')}

### Recent Breakthroughs
- mendicant_bias orchestrator deployed
- Multi-agent framework operational

## Blockers
None currently

## Next Session Priorities
1. Define project requirements
2. Set up development environment
3. Begin core feature implementation
4. Establish testing infrastructure

## Strategic Context
- **Agent System**: Revolutionary multi-agent orchestration active
- **Next Focus**: Build foundation and establish workflow

---

**mendicant_bias**: This mission context is maintained by the supreme orchestrator
"""

    (memory_dir / "mission_context.md").write_text(mission_context)
    print(f"[OK] Created mission_context.md")

    # Create roadmap.md
    roadmap = f"""# Strategic Roadmap - {config['project_name']}

**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}

## Vision
{config['mission']}

## Phases

### Phase 1: Foundation [CURRENT]
- Project structure setup
- Development environment
- Core architecture
- Basic features

### Phase 2: Core Features [PLANNED]
- Main functionality implementation
- Testing infrastructure
- Documentation
- Performance optimization

### Phase 3: Advanced Features [PLANNED]
- Advanced capabilities
- Integration with external services
- Enhanced user experience
- Scaling considerations

### Phase 4: Production Readiness [PLANNED]
- Security hardening
- Monitoring & observability
- CI/CD pipeline
- Deployment automation

### Phase 5: Continuous Improvement [FUTURE]
- User feedback integration
- Feature enhancements
- Performance tuning
- Competitive analysis

## Agent Orchestration System

### The Team
- **mendicant_bias**: Supreme orchestrator
- **the_didact**: Strategic research
- **hollowed_eyes**: Main developer
- **loveless**: QA & security
- **zhadyz**: DevOps

### Autonomous Workflows
```
Research → Development → Testing → Deployment
```

## Success Metrics

### Technical
- Code coverage: > 80%
- Build time: < 5 minutes
- Test pass rate: 100%
- Deployment success: > 99%

### Strategic
- Feature completeness: Track progress
- Code quality: Maintain high standards
- Innovation: Continuous improvement

---

**mendicant_bias**: Strategic roadmap maintained by supreme orchestrator with input from the_didact
"""

    (memory_dir / "roadmap.md").write_text(roadmap)
    print(f"[OK] Created roadmap.md")

    # Create state.json
    state = {
        "mission": {
            "name": config['project_name'],
            "phase": 1,
            "phase_name": "Foundation",
            "progress_percent": 20
        },
        "version": {
            "current": config.get('version', '0.1.0'),
            "next": "0.2.0",
            "branch": "main"
        },
        "agents": {
            "last_invoked": "mendicant_bias",
            "status": "initialized",
            "active_missions": ["Framework deployment complete"]
        },
        "blockers": [],
        "priorities": [
            "Define project requirements",
            "Set up development environment",
            "Begin core implementation",
            "Establish testing infrastructure"
        ],
        "metrics": {
            "agent_count": 5,
            "framework_status": "operational"
        },
        "agent_roster": {
            "mendicant_bias": {"role": "Supreme Orchestrator", "color": "white", "status": "active"},
            "the_didact": {"role": "Strategic Research", "color": "gold", "status": "ready"},
            "hollowed_eyes": {"role": "Main Developer", "color": "cyan", "status": "ready"},
            "loveless": {"role": "QA/Security", "color": "red", "status": "ready"},
            "zhadyz": {"role": "DevOps", "color": "purple", "status": "ready"}
        },
        "last_updated": datetime.now().isoformat()
    }

    with open(memory_dir / "state.json", 'w') as f:
        json.dump(state, f, indent=2)

    print(f"[OK] Created state.json")


def create_awaken_command(target_dir: Path):
    """Create /awaken slash command"""

    commands_dir = target_dir / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    src_awaken = Path(__file__).parent.parent / "commands" / "awaken.md"
    if src_awaken.exists():
        shutil.copy(src_awaken, commands_dir / "awaken.md")
        print(f"[OK] Created /awaken command")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize MENDICANT_BIAS framework for any project"
    )
    parser.add_argument("--project-name", required=True, help="Project name")
    parser.add_argument("--project-type", required=True,
                       choices=list(PROJECT_DOMAINS.keys()),
                       help="Project type")
    parser.add_argument("--tech-stack", required=True, help="Technology stack")
    parser.add_argument("--mission", default="", help="Project mission/goal")
    parser.add_argument("--version", default="0.1.0", help="Starting version")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", default="6379", help="Redis port")

    args = parser.parse_args()

    if not args.mission:
        args.mission = f"Build and deploy {args.project_name} with excellence"

    config = {
        "project_name": args.project_name,
        "project_type": args.project_type,
        "tech_stack": args.tech_stack,
        "mission": args.mission,
        "version": args.version,
        "redis_host": args.redis_host,
        "redis_port": args.redis_port
    }

    target_dir = Path(args.target_dir).resolve()

    print("\n" + "="*70)
    print("MENDICANT_BIAS FRAMEWORK INITIALIZATION")
    print("="*70)
    print(f"Project: {config['project_name']}")
    print(f"Type: {config['project_type']}")
    print(f"Tech Stack: {config['tech_stack']}")
    print(f"Target: {target_dir}")
    print("="*70 + "\n")

    # Create framework
    create_agent_configs(target_dir, config)
    create_memory_files(target_dir, config)
    create_awaken_command(target_dir)

    print("\n" + "="*70)
    print("FRAMEWORK DEPLOYED SUCCESSFULLY")
    print("="*70)
    print(f"\nYour {config['project_name']} now has:")
    print("  - mendicant_bias (supreme orchestrator)")
    print("  - the_didact (research)")
    print("  - hollowed_eyes (developer)")
    print("  - loveless (QA/security)")
    print("  - zhadyz (devops)")
    print("  - Persistent memory system")
    print("  - /awaken command")
    print("\nNext steps:")
    print("  1. Start Claude Code in this directory")
    print("  2. Type: /awaken")
    print("  3. Begin your mission!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
