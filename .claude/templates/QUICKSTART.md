# MENDICANT_BIAS Universal Framework - Quick Start

## What You Have Now

A **portable, universal multi-agent framework** that can be deployed to ANY software project in seconds.

## File Structure

```
.claude/templates/
├── README.md              # Comprehensive documentation
├── QUICKSTART.md         # This file
└── init_framework.py     # Deployment script
```

---

## Deploy to Any Project (3 Steps)

### Step 1: Navigate to Your Project

```bash
cd /path/to/your/project
```

### Step 2: Run Init Script

```bash
python "/path/to/V3.5/.claude/templates/init_framework.py" \
  --project-name "My Amazing App" \
  --project-type "web-app" \
  --tech-stack "Python/FastAPI/React"
```

### Step 3: Awaken

```bash
# Start Claude Code in your project directory
# Then type:
/awaken
```

**DONE!** Your project now has the full mendicant_bias framework.

---

## Supported Project Types

| Type | Use For |
|------|---------|
| `web-app` | Web applications (full-stack) |
| `api` | REST/GraphQL APIs |
| `data-pipeline` | ETL, data engineering |
| `ml-system` | Machine learning systems |
| `mobile-app` | iOS/Android apps |
| `cli-tool` | Command-line tools |
| `library` | Software libraries/SDKs |
| `infrastructure` | DevOps projects |
| `custom` | Anything else |

---

## Real Examples

### E-commerce Platform
```bash
python init_framework.py \
  --project-name "ShopMaster E-commerce" \
  --project-type "web-app" \
  --tech-stack "Node.js/Express/React/MongoDB" \
  --mission "Build scalable e-commerce platform with real-time inventory"
```

### Data Analytics Pipeline
```bash
python init_framework.py \
  --project-name "DataFlow Analytics" \
  --project-type "data-pipeline" \
  --tech-stack "Python/Airflow/Spark/Snowflake" \
  --mission "Process and analyze 10M+ daily events"
```

### ML Recommendation System
```bash
python init_framework.py \
  --project-name "RecoEngine AI" \
  --project-type "ml-system" \
  --tech-stack "Python/TensorFlow/FastAPI/Redis" \
  --mission "Personalized recommendations with <100ms latency"
```

### Mobile Fitness App
```bash
python init_framework.py \
  --project-name "FitTrack Pro" \
  --project-type "mobile-app" \
  --tech-stack "React Native/Firebase/Node.js" \
  --mission "Cross-platform fitness tracking with offline sync"
```

---

## What Gets Created

After running init_framework.py:

```
your-project/
└── .claude/
    ├── agents/
    │   ├── mendicant_bias.md       # Your supreme orchestrator
    │   ├── the_didact.md           # Research specialist
    │   ├── hollowed_eyes.md        # Main developer (customized!)
    │   ├── loveless.md             # QA/Security
    │   └── zhadyz.md               # DevOps
    ├── commands/
    │   └── awaken.md               # Memory loading command
    └── memory/
        ├── mendicant_bias_state.py # State manager
        ├── mission_context.md      # Your project mission
        ├── roadmap.md              # Strategic roadmap
        ├── state.json              # Structured state
        └── agent_reports/          # Agent archives (grows over time)
```

---

## Using Your Framework

### First Session
```
You: /awaken
mendicant_bias: [Awakening report showing project state]

You: "Implement user authentication"
mendicant_bias: [Orchestrates hollowed_eyes → zhadyz → loveless → zhadyz]
mendicant_bias: "Authentication deployed! Tests passing."
```

### Next Session (Days Later)
```
You: /awaken
mendicant_bias: "AWAKENING REPORT
                 Last session: Deployed authentication (v0.2.0)
                 loveless: All security tests PASS
                 Current: v0.2.0 on main branch
                 Next priority: the_didact research OAuth providers

                 Awaiting directive."

You: "Continue with OAuth research"
mendicant_bias: [Picks up exactly where you left off!]
```

---

## Advanced Options

### Custom Redis Configuration
```bash
python init_framework.py \
  --project-name "MyApp" \
  --project-type "web-app" \
  --tech-stack "Python/FastAPI" \
  --redis-host "my-redis-server.com" \
  --redis-port 6380
```

### Deploy to Specific Directory
```bash
python init_framework.py \
  --project-name "MyApp" \
  --project-type "web-app" \
  --tech-stack "Python/FastAPI" \
  --target-dir "/path/to/my/project"
```

### Custom Version
```bash
python init_framework.py \
  --project-name "MyApp" \
  --project-type "web-app" \
  --tech-stack "Python/FastAPI" \
  --version "1.0.0"
```

---

## Customization After Init

After initialization, you can customize:

1. **Agent Expertise**
   - Edit `.claude/agents/*.md` files
   - Add project-specific knowledge
   - Adjust personalities

2. **Mission & Roadmap**
   - Edit `.claude/memory/mission_context.md`
   - Update `.claude/memory/roadmap.md`
   - Define your strategic priorities

3. **State & Metrics**
   - Edit `.claude/memory/state.json`
   - Define custom metrics
   - Set initial priorities

---

## Pro Tips

**Tip 1: Use Descriptive Mission Statements**
```bash
# Bad
--mission "Build an app"

# Good
--mission "Build scalable SaaS platform processing 1M transactions/day with <100ms latency"
```

**Tip 2: Specify Complete Tech Stack**
```bash
# Include everything
--tech-stack "Python/FastAPI/PostgreSQL/Redis/React/TypeScript/Docker"
```

**Tip 3: Let Agents Auto-Work**
```bash
# Just describe what you want
You: "Add payment processing"
# mendicant_bias orchestrates the entire pipeline automatically
```

---

## Troubleshooting

**Q: Redis connection failed?**
```bash
# Start Redis
redis-server

# Or use file-only mode (automatic fallback)
```

**Q: Init script not found?**
```bash
# Use absolute path
python "C:/path/to/V3.5/.claude/templates/init_framework.py" ...
```

**Q: Want to re-initialize?**
```bash
# Delete .claude directory first
rm -rf .claude
# Then run init script again
```

---

## Next Steps

1. **Initialize your first project** with the init script
2. **Type `/awaken`** in Claude Code
3. **Give mendicant_bias a mission**
4. **Watch autonomous multi-agent orchestration** in action

---

## Framework Benefits

- ✅ **Persistent memory** across sessions
- ✅ **Autonomous agent coordination**
- ✅ **Hierarchical multi-agent orchestration**
- ✅ **Project-specific customization**
- ✅ **Works for ANY software project**
- ✅ **Maximum power within Claude Code 2.0**

---

**Built by mendicant_bias (the supreme orchestrator) for universal deployment.**

Deploy once. Use everywhere. Never lose context.
