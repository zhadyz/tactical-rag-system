# Tactical RAG System - Demo Script

**Duration**: 10-15 minutes
**Audience**: Technical recruiters, hiring managers, engineering teams
**Goal**: Demonstrate multi-agent development, enterprise RAG capabilities, and technical depth

---

## Pre-Demo Checklist

- [ ] System running: `deploy.bat` or `docker-compose up -d`
- [ ] Browser open to http://localhost:7860
- [ ] Documents indexed (check logs for "Indexing complete")
- [ ] Git history ready to display
- [ ] Performance dashboard visible
- [ ] IMPROVEMENTS.md open for reference

---

## Demo Flow

### 1. Introduction (2 minutes)

**Opening:**
> "I'd like to show you a Tactical RAG system I developed that demonstrates both advanced AI/ML capabilities and multi-agent software engineering. The system provides document intelligence for mission-critical operations, with features like conversation memory, explainability, and feedback loops."

**Key Points:**
- Enterprise-grade RAG for government/defense use cases
- Developed through multi-agent AI collaboration (unique portfolio piece)
- Production-ready with comprehensive testing and monitoring
- ~1,300 LOC added across 4 milestones

---

### 2. Multi-Agent Development Process (3 minutes)

**Show**: Open `IMPROVEMENTS.md` and git history

```bash
git log --oneline --graph --all
```

**Narration:**
> "What makes this project unique is the development process. I used three coordinated AI agents to iteratively improve the system:"

1. **medicant_bias** (Architect):
   - Designed the improvement roadmap
   - Defined milestones and acceptance criteria
   - Established coordination protocol (state.json + Redis)
   - Self-terminated after setup

2. **hollowed_eyes** (Engineer):
   - Implemented features (conversation memory, explainability, feedback)
   - Wrote unit tests for each component
   - Committed after each implementation

3. **zhadyz** (Tester/Docs):
   - Created integration tests (63 total)
   - Wrote comprehensive documentation
   - Polished for portfolio presentation

**Point Out:**
- Git history shows clear agent handoffs
- Each milestone: dev commit → docs commit → state update
- Coordination via state.json (show file briefly)
- Demonstrates LangGraph/CrewAI patterns without heavy dependencies

---

### 3. Core Feature Demo: Adaptive Retrieval (3 minutes)

**Navigate**: Web interface at http://localhost:7860

**Demo Sequence:**

#### Simple Query (should use simple_dense strategy)
```
Query: "What is RAG?"
```

**Point Out:**
- Fast response (~1-2s)
- Query type: "simple"
- Strategy: "simple_dense" (pure vector search)
- Top 3 results with relevance scores
- Source citations with document names

#### Moderate Query (should use hybrid_reranked strategy)
```
Query: "What are the deployment requirements and setup steps?"
```

**Point Out:**
- Moderate complexity (~2-4s)
- Query type: "moderate"
- Strategy: "hybrid_reranked" (RRF fusion + cross-encoder)
- Top 5 results after reranking
- GPU acceleration visible in performance dashboard

#### Complex Query (should use advanced_expanded strategy)
```
Query: "Why does the system use hybrid retrieval and what are the performance tradeoffs compared to simple vector search?"
```

**Point Out:**
- Complex analytical query (~4-6s)
- Query type: "complex"
- Strategy: "advanced_expanded" (multi-query expansion)
- LLM generates query variants, vote aggregation
- Comprehensive answer with multi-source citations

---

### 4. Conversation Memory Demo (2 minutes)

**Demo Sequence:**

```
Turn 1: "What retrieval strategies does this system use?"
→ System explains three-tier adaptive approach

Turn 2: "How does that compare to traditional search?"
→ Follow-up detected! Enhanced with context from Turn 1
→ System provides comparison using conversation history

Turn 3: "Tell me more about the GPU acceleration"
→ Another follow-up! References previous answers
→ Natural multi-turn conversation flow
```

**Technical Points:**
- Sliding window stores last 10 exchanges
- Automatic summarization after 5 exchanges (LLM-based)
- Follow-up detection via pattern matching
- +50-100ms latency (negligible overhead)
- ~20KB memory per conversation

**Show Code (optional):**
```python
# _src/conversation_memory.py
class ConversationMemory:
    def __init__(self, llm, max_exchanges=10, summarization_threshold=5):
        self.exchanges = deque(maxlen=max_exchanges)
        self.conversation_summary = None
```

---

### 5. Explainability Feature (2 minutes)

**Demo**: Run a complex query

```
Query: "Compare the three retrieval strategies and recommend one for medical documents"
```

**Show Explanation** (in UI or logs):
```
Query classified as COMPLEX (score: 6) because:
- length=13 words (+2)
- question_type=compare (+2)
- has_and_operator=yes (+1)
- imperative_verb=recommend (+1)

Thresholds: simple≤1, moderate≤3

Using advanced_expanded strategy.
Reasoning: High complexity requires query expansion and advanced fusion
```

**Technical Points:**
- Full transparency in AI decision-making
- Scoring breakdown shows all contributing factors
- Strategy selection explained
- Supports explainable AI requirements for government/enterprise
- <1ms overhead (negligible)

**Business Value:**
- Audit trail for compliance
- Debugging and optimization
- Builds user trust in AI system

---

### 6. Feedback System & Continuous Improvement (2 minutes)

**Demo**: Submit feedback on previous queries

1. Click **👍 Thumbs Up** on good answer
2. Click **👎 Thumbs Down** on poor answer (or simulate)
3. Navigate to **Settings Panel** → **Feedback Analytics**

**Show Statistics:**
```
Overall Satisfaction: 71%
Total Feedback: 45 ratings

By Query Type:
- Simple:    88% satisfaction (15/17) ✅
- Moderate:  71% satisfaction (12/17) 👍
- Complex:   45% satisfaction (5/11)  ⚠️

By Strategy:
- simple_dense:       88% (15/17) ✅
- hybrid_reranked:    73% (11/15) 👍
- advanced_expanded:  46% (6/13)  ⚠️ Needs improvement
```

**Technical Points:**
- JSON-based feedback storage (feedback.json)
- Real-time analytics dashboard
- Low-rated query identification
- Performance by query type and strategy
- <1ms to submit feedback (non-blocking)

**Data-Driven Optimization:**
> "Based on this feedback, I can see complex queries need improvement. The data shows advanced_expanded strategy underperforms - likely due to query expansion quality. I would tune the expansion prompts or reduce expansion count from 2 to 1."

**Business Value:**
- Continuous learning from user interactions
- Data-driven system tuning
- Quality assurance via satisfaction KPI
- User engagement (they shape the system)

---

### 7. Performance Monitoring (1 minute)

**Show**: Performance Dashboard (right panel)

**Point Out:**
- **GPU Utilization**: Real-time CUDA monitoring
- **VRAM Usage**: ~6-8 GB (llama3.1:8b loaded)
- **CPU Usage**: Multi-core utilization
- **Query Latency**: P50, P95, P99 percentiles
- **Cache Hit Rate**: Effectiveness of 3-layer cache

**Technical Stack:**
- PyTorch-based GPU monitoring (Docker-compatible, no nvidia-smi)
- Real-time updates (1 second interval)
- Prometheus-style metrics collection

---

### 8. Code Deep Dive (2 minutes - if time permits)

**Show Key Files:**

#### 1. Multi-Agent Coordination
```json
// state.json
{
  "handoffs": {
    "milestone_1_dev_complete": true,
    "milestone_1_docs_complete": true,
    "milestone_2_dev_complete": true,
    "milestone_2_docs_complete": true,
    "milestone_3_dev_complete": true,
    "milestone_3_docs_complete": true
  }
}
```

#### 2. Conversation Memory
```python
# _src/conversation_memory.py (line 45-60)
def add_exchange(self, query: str, response: str, ...):
    """Add query-response pair to memory with automatic summarization"""
    exchange = ConversationExchange(...)
    self.exchanges.append(exchange)

    if len(self.exchanges) >= self.summarization_threshold:
        self._trigger_summarization()  # LLM-based compression
```

#### 3. Explainability
```python
# _src/explainability.py
@dataclass
class QueryExplanation:
    query_type: str
    complexity_score: int
    scoring_breakdown: Dict[str, int]
    strategy_reasoning: str
```

#### 4. Feedback System
```python
# _src/feedback_system.py
class FeedbackManager:
    def add_feedback(self, query, answer, rating, query_type, strategy_used):
        entry = {...}
        self.feedback_data.append(entry)
        self._save_to_json()
```

---

### 9. Testing & Quality Assurance (1 minute)

**Show**: Test files

```bash
# Integration tests
_src/test_conversation_integration.py   # 15 tests
_src/test_explainability.py             # 12 tests
_src/test_feedback_integration.py       # 21 tests
# Total: 63+ integration tests
```

**Run Sample Test (optional):**
```bash
pytest _src/test_conversation_integration.py::TestConversationIntegration::test_five_turn_conversation_with_summarization -v
```

**Point Out:**
- Comprehensive test coverage for all major features
- Integration tests simulate real-world workflows
- Automated evaluation suite (evaluate.py)
- Grading system (A-F) for production readiness

---

### 10. Closing (1 minute)

**Summary:**
> "This project demonstrates three key areas:
>
> 1. **Multi-Agent AI Coordination**: Novel development process with three specialized agents, visible in git history
>
> 2. **Enterprise RAG System**: Production-ready document intelligence with conversation memory, explainability, feedback loops, and GPU acceleration
>
> 3. **Software Engineering Excellence**: Comprehensive testing (63 tests), documentation (IMPROVEMENTS.md, ARCHITECTURE.md), monitoring, and deployment automation
>
> The system evolved from v2.5 to v3.5.1 through 4 iterative milestones, adding ~1,300 LOC of production code. It showcases both AI/ML technical depth and coordinated development patterns relevant to enterprise systems at firms like Booz Allen Hamilton."

**Key Differentiators:**
- Multi-agent development (unique portfolio piece)
- Explainable AI for government/defense compliance
- Feedback-driven continuous improvement
- GPU-optimized performance
- Production-ready with Docker deployment

**Available Resources:**
- GitHub: https://github.com/zhadyz/tactical-rag-system
- IMPROVEMENTS.md: Full evolution timeline
- ARCHITECTURE.md: Technical deep dive
- Live demo: Can deploy and test with custom documents

---

## Q&A Preparation

### Common Questions

**Q: How does the multi-agent coordination work?**
> "Agents coordinate through state.json (task ownership, handoff triggers) and Redis pub/sub for real-time events. Each agent has a specific role: medicant_bias designed the roadmap, hollowed_eyes implemented features, zhadyz tested and documented. Git history shows clear progression: dev commit → docs commit → state update for each milestone."

**Q: What makes this RAG system enterprise-ready?**
> "Four key aspects: (1) Explainability - full transparency for compliance, (2) Conversation memory - natural multi-turn interactions, (3) Feedback loops - continuous learning from users, (4) Performance monitoring - real-time GPU/CPU metrics. Plus comprehensive testing, Docker deployment, and production documentation."

**Q: How does the adaptive retrieval work?**
> "Query classifier scores complexity using multiple factors: length, question type (who/what/why), operators (and/or). Score ≤1 → simple strategy (pure vector search), ≤3 → hybrid (RRF fusion + reranking), >3 → advanced (multi-query expansion). Each strategy optimized for its complexity level."

**Q: What was the biggest technical challenge?**
> "Conversation memory summarization. Need to compress history without losing context. Solution: LLM-based summarization every 5 exchanges, preserving key topics in <200 words. Follow-up detection via pattern matching plus short query heuristic. Maintains multi-turn context in ~20KB memory."

**Q: How would you deploy this in production?**
> "Already Docker-native with GPU passthrough. For production: (1) Add document-level access control, (2) Implement PII detection/redaction, (3) Scale with Kubernetes (horizontal pod autoscaling), (4) Add Redis for distributed caching, (5) Prometheus/Grafana for monitoring. All infrastructure defined in docker-compose.yml and Dockerfile."

**Q: Can you explain the feedback system's value?**
> "Provides data-driven optimization. Example: Feedback showed complex queries at 45% satisfaction vs 88% for simple queries. Root cause: advanced_expanded strategy underperforms. Action: Tune query expansion prompts or reduce expansion count. Feedback loop transforms RAG from static to learning system."

---

## Demo Variations

### Short Version (5 minutes)
1. Introduction (1 min)
2. Multi-agent coordination (git log) (1 min)
3. Adaptive retrieval demo (simple → complex) (2 min)
4. Closing highlights (1 min)

### Technical Deep Dive (20 minutes)
Add:
- Code walkthrough (5 min)
- Architecture diagrams (ARCHITECTURE.md) (3 min)
- Deployment process (docker-compose up) (2 min)

### Executive Version (7 minutes)
Focus on:
- Business value of multi-agent development
- Enterprise features (explainability, feedback)
- ROI: Continuous improvement vs static system
- Compliance (explainable AI for government)

---

## Backup Plans

**If system not running:**
- Show screenshots/recordings
- Walk through code and documentation
- Discuss architecture from ARCHITECTURE.md

**If demo breaks:**
- Git history shows full development progression
- IMPROVEMENTS.md documents all features
- Test output shows comprehensive coverage

**If short on time:**
- Skip code deep dive
- Focus on multi-agent coordination + one feature demo
- Direct to GitHub for full exploration

---

## Post-Demo Follow-Up

**Materials to share:**
- GitHub repository link
- IMPROVEMENTS.md (evolution document)
- ARCHITECTURE.md (technical details)
- Sample queries and expected outputs

**Talking points for interviews:**
- Multi-agent patterns applicable to team workflows
- RAG system design principles
- GPU optimization techniques
- Production deployment considerations
- Continuous improvement through feedback

---

**Demo prepared by**: zhadyz
**System version**: 3.5.1
**Last updated**: 2025-10-11

---

Good luck with your demo! 🚀
