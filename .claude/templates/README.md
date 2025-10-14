# MENDICANT_BIAS Universal Framework Templates

This directory contains universal templates for deploying the mendicant_bias multi-agent orchestration framework to ANY software project.

## What This Is

A portable, intelligent agent framework that gives you:
- **mendicant_bias**: Supreme orchestrator (you talk to this)
- **the_didact**: Strategic research & competitive intelligence
- **hollowed_eyes**: Main developer & architect
- **loveless**: QA, security, integration testing
- **zhadyz**: DevOps, CI/CD, deployment

With persistent memory across sessions via Redis + file storage.

## Quick Start

```bash
# In your project directory
python /path/to/.claude/templates/init_framework.py \
  --project-name "My Amazing App" \
  --project-type "web-app" \
  --tech-stack "Python/FastAPI/React"

# Framework deployed! Now use Claude Code:
# Type: /awaken
```

## Supported Project Types

- `web-app`: Web applications (frontend + backend)
- `api`: REST/GraphQL APIs
- `data-pipeline`: ETL, data engineering
- `ml-system`: Machine learning systems
- `mobile-app`: iOS/Android applications
- `cli-tool`: Command-line tools
- `library`: Software libraries/SDKs
- `infrastructure`: DevOps/infrastructure projects
- `custom`: Fully custom (you define everything)

## What Gets Generated

```
your-project/
└── .claude/
    ├── agents/
    │   ├── mendicant_bias.md      # Supreme orchestrator
    │   ├── the_didact.md          # Research specialist
    │   ├── hollowed_eyes.md       # Main developer
    │   ├── loveless.md            # QA/Security
    │   └── zhadyz.md              # DevOps
    ├── commands/
    │   └── awaken.md              # Memory loading command
    └── memory/
        ├── mendicant_bias_state.py  # State manager
        ├── mission_context.md       # Current mission
        ├── roadmap.md               # Strategic roadmap
        ├── state.json               # Structured state
        └── agent_reports/           # Agent archives
```

## Initialization Options

```bash
python init_framework.py \
  --project-name "E-commerce Platform" \
  --project-type "web-app" \
  --tech-stack "Python/FastAPI/React/PostgreSQL" \
  --mission "Build scalable e-commerce platform" \
  --redis-host "localhost" \
  --redis-port 6379
```

## How It Works

1. **Template Expansion**: Replaces {{PLACEHOLDERS}} with your project details
2. **Agent Customization**: Adapts agent expertise to your project domain
3. **Memory Initialization**: Creates project-specific memory files
4. **Ready to Use**: Start Claude Code and type `/awaken`

## Advanced: Manual Customization

After initialization, you can customize:
- Agent personalities and expertise in `.claude/agents/*.md`
- Mission objectives in `.claude/memory/mission_context.md`
- Strategic roadmap in `.claude/memory/roadmap.md`

## Template Variables

The init script replaces these placeholders:

- `{{PROJECT_NAME}}`: Your project name
- `{{PROJECT_TYPE}}`: Project category
- `{{PROJECT_DOMAIN}}`: Domain expertise needed
- `{{TECH_STACK}}`: Technologies used
- `{{PRIMARY_GOAL}}`: Main project objective
- `{{MISSION_DESCRIPTION}}`: Detailed mission
- `{{VERSION_CURRENT}}`: Current version (default: 0.1.0)
- `{{PHASE_NAME}}`: Current phase (default: Foundation)

## Redis Requirement

The memory system requires Redis for optimal performance:
```bash
# Install Redis
# Windows: Use WSL or Redis for Windows
# Mac: brew install redis
# Linux: apt-get install redis

# Start Redis
redis-server
```

Falls back to file-only storage if Redis is unavailable.

## Examples

### Web Application
```bash
python init_framework.py \
  --project-name "Social Media App" \
  --project-type "web-app" \
  --tech-stack "Node.js/Express/React"
```

### Data Pipeline
```bash
python init_framework.py \
  --project-name "Analytics ETL" \
  --project-type "data-pipeline" \
  --tech-stack "Python/Airflow/Spark"
```

### ML System
```bash
python init_framework.py \
  --project-name "Recommendation Engine" \
  --project-type "ml-system" \
  --tech-stack "Python/TensorFlow/FastAPI"
```

## Support

This framework was built for maximum power within Claude Code 2.0.
- Memory persists across sessions
- Agents coordinate autonomously
- Full hierarchical multi-agent orchestration

Created by: mendicant_bias (the supreme orchestrator itself)
