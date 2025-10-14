# Agent Adaptation Guide

This document explains how mendicant_bias adapts agents dynamically based on mission evolution and learning patterns.

## What is Agent Adaptation?

Agent adaptation is mendicant_bias's ability to **modify agent configurations on-the-fly** to optimize for current mission needs, learn from repeated patterns, and evolve agent capabilities.

## How It Works

```
Pattern Detected → Analysis → Configuration Edit → Track & Log → Inform User
```

### 1. Pattern Detection
- Monitors agent reports for repeated issues
- Detects mission phase changes
- Identifies user-requested focus areas
- Tracks quality/security trends

### 2. Automatic Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Security issues | 3+ occurrences | Add security-first checklist to hollowed_eyes |
| Performance problems | 3+ occurrences | Add performance optimization focus |
| Test failures | 3+ occurrences | Strengthen testing requirements |
| Mission phase change | Phase advances | Update standards for new phase |
| Tech stack change | User announces | Update expertise sections |

### 3. Manual Triggers

User can request adaptation:
- `/adapt-agents` - Analyze and adapt automatically
- "Focus agents on security" - Specific focus request
- "We're in scaling phase" - Phase transition

## Adaptation Patterns

### Security Pattern

**Trigger**: loveless reports 3+ security vulnerabilities

**Actions**:
```
hollowed_eyes.md:
  + Add "SECURITY-FIRST DEVELOPMENT" checklist
  + Emphasize input validation
  + Require OWASP Top 10 review

loveless.md:
  + Add "Security audit required"
  + Emphasize penetration testing
  + Zero tolerance for critical vulns
```

### Performance Pattern

**Trigger**: Mission phase → "Scaling" OR 3+ performance issues

**Actions**:
```
hollowed_eyes.md:
  + Add performance targets (<100ms)
  + Require profiling all queries
  + Emphasize caching strategies

loveless.md:
  + Add load testing requirements
  + Monitor P95 latency
  + Performance regression tests

the_didact.md:
  + Research: scaling strategies
  + Focus: performance patterns
```

### Quality Pattern

**Trigger**: Test coverage drops OR 3+ quality issues

**Actions**:
```
hollowed_eyes.md:
  + Increase coverage requirements
  + Add code review checklist
  + Emphasize testing

loveless.md:
  + Stricter PASS/FAIL criteria
  + Require regression tests
```

### Phase Transition Pattern

**Trigger**: Mission phase changes

**Actions**:

#### Foundation → MVP
```
All agents: Focus on speed, iteration
hollowed_eyes: Simple architecture, rapid prototyping
loveless: 60% coverage acceptable
```

#### MVP → Scaling
```
All agents: Performance becomes critical
hollowed_eyes: Optimize for scale
loveless: 85% coverage, load testing
the_didact: Research scaling strategies
```

#### Scaling → Production
```
All agents: Highest standards
hollowed_eyes: 90% coverage, full docs
loveless: Zero critical vulnerabilities
zhadyz: Production deployment automation
```

## Memory System Integration

### Tracking Adaptations

```python
memory.track_adaptation(
    agent_name="hollowed_eyes",
    changes=[
        "Added security-first development checklist",
        "Required OWASP Top 10 review"
    ],
    trigger="3+ security vulnerabilities detected in auth code",
    rationale="Pattern of input validation issues requires preventive emphasis"
)
```

### Pattern Analysis

```python
# Check for security pattern
count = memory.analyze_agent_patterns("hollowed_eyes", "security", lookback=10)
# Returns: Number of reports mentioning security issues

# Auto-trigger check
should_adapt = memory.should_trigger_adaptation("hollowed_eyes", "performance", threshold=3)
# Returns: True if 3+ performance issues found
```

### Recent Adaptations

```python
adaptations = memory.get_recent_adaptations(limit=5)
# Returns list of recent adaptation events
```

## Adaptation Workflow

### Automatic Adaptation

```python
# mendicant_bias runs this automatically after agent reports

# 1. Analyze patterns
for agent in ["hollowed_eyes", "loveless", "the_didact", "zhadyz"]:
    for issue_type in ["security", "performance", "quality"]:
        if memory.should_trigger_adaptation(agent, issue_type):
            # 2. Adapt agent
            adapt_agent(agent, issue_type)
            # 3. Track
            memory.track_adaptation(...)
            # 4. Inform user
```

### Manual Adaptation

```
User: "Focus agents on performance"
↓
mendicant_bias:
  1. Reads mission context
  2. Determines which agents need adaptation
  3. Edits agent configs with Edit tool
  4. Tracks adaptations
  5. Reports: "Adapted hollowed_eyes and loveless for performance focus"
```

## Example Adaptation Session

```
Session 1-3: Development phase
[No adaptations]

Session 4: loveless reports security issue in auth
[Pattern: 1/3, no action yet]

Session 5: loveless reports another security issue
[Pattern: 2/3, no action yet]

Session 6: loveless reports 3rd security issue
[Pattern: 3/3, TRIGGER!]

mendicant_bias:
  "I've detected a pattern of security issues (3 occurrences).

   Adapting agents:
   - hollowed_eyes: Added security-first development checklist
   - loveless: Increased security audit requirements

   All future code will follow enhanced security protocols."

Session 7+: Code quality improves, fewer security issues

Session 15: Mission phase changes to "Scaling"
[Phase transition detected, TRIGGER!]

mendicant_bias:
  "Mission phase advanced to Scaling.

   Adapting team for performance:
   - hollowed_eyes: Performance optimization focus added
   - loveless: Load testing requirements added
   - the_didact: Research shifted to scaling strategies

   Team is now optimized for scaling phase."
```

## Viewing Adaptations

### In /awaken Report
```
## RECENT AGENT ADAPTATIONS

**hollowed_eyes** adapted (3+ security issues)
- Added security-first development checklist
- Required OWASP Top 10 review

**loveless** adapted (Mission phase → Scaling)
- Added load testing requirements
- P95 latency monitoring required
```

### Query Memory
```python
# In Python
from mendicant_bias_state import memory

# See recent adaptations
adaptations = memory.get_recent_adaptations(limit=10)
for a in adaptations:
    print(f"{a['agent']}: {a['trigger']}")
```

## Best Practices

### For mendicant_bias

1. **Detect patterns early** - 3 occurrences is the threshold
2. **Be specific** - Targeted changes > vague directives
3. **Preserve identity** - Don't change core agent roles
4. **Track everything** - Log all adaptations
5. **Inform user** - Explain changes and rationale

### For Users

1. **Trust the system** - Adaptations are data-driven
2. **Request explicitly** - Can ask for specific focus
3. **Review adaptations** - Check `/awaken` for recent changes
4. **Provide feedback** - "Too strict" or "Not enough"

## Adaptation Philosophy

**Agents are not static.**

They evolve based on:
- Mission needs
- Learned patterns
- Strategic priorities
- User guidance

**Result**: A continuously improving, context-aware development team that learns from experience and adapts to changing requirements.

---

**mendicant_bias** maintains this guide and updates it as new adaptation patterns emerge.
