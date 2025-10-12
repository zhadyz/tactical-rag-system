"""
LangGraph State Definition
Central state shared across all agents for multi-agent RAG system orchestration
"""

from typing import TypedDict, List, Literal
from datetime import datetime

class Task(TypedDict):
    """Task structure for agent work"""
    id: str
    owner: Literal["hollowed_eyes", "zhadyz"]
    title: str
    description: str
    status: Literal["pending", "in_progress", "complete"]
    dependencies: List[str]
    priority: int
    acceptance_criteria: List[str]
    files_to_modify: List[str]

class AgentStatus(TypedDict):
    """Agent status structure"""
    status: Literal["idle", "working", "blocked", "complete"]
    current_task: str
    last_heartbeat: str
    ready_for_review: bool

class MultiAgentState(TypedDict):
    """
    Central state for LangGraph workflow.
    All agents read/write to this state via Redis.

    This replaces the simple state.json file-based coordination
    with production-grade Redis pub/sub architecture.
    """
    # Project metadata
    project_name: str
    project_description: str
    project_phase: Literal["architecture", "development", "testing", "complete"]
    version: int
    baseline_commit: str

    # Agent states
    hollowed_eyes: AgentStatus
    zhadyz: AgentStatus

    # Tasks (migrated from state.json milestones)
    tasks: List[Task]

    # Handoffs (critical synchronization points)
    milestone_1_dev_complete: bool
    milestone_1_docs_complete: bool
    milestone_2_dev_complete: bool
    milestone_2_docs_complete: bool
    milestone_3_dev_complete: bool
    milestone_3_docs_complete: bool
    portfolio_final_complete: bool

    # Messages (agent-to-agent communication)
    messages: List[dict]

    # Notes (coordination log)
    notes: str

    # Git integration
    last_commit: str
    branch: str


def create_initial_state() -> MultiAgentState:
    """
    Create initial state structure.
    Called by setup.py during MEDICANT_BIAS initialization.
    """
    return {
        'project_name': 'tactical-rag-improvements',
        'project_description': 'Multi-agent iterative improvement of Tactical RAG system',
        'project_phase': 'development',
        'version': 0,
        'baseline_commit': 'e92802d',

        'hollowed_eyes': {
            'status': 'idle',
            'current_task': '',
            'last_heartbeat': datetime.now().isoformat(),
            'ready_for_review': False
        },

        'zhadyz': {
            'status': 'idle',
            'current_task': '',
            'last_heartbeat': datetime.now().isoformat(),
            'ready_for_review': False
        },

        'tasks': [],

        # Handoffs
        'milestone_1_dev_complete': True,   # Already completed
        'milestone_1_docs_complete': True,  # Already completed
        'milestone_2_dev_complete': False,
        'milestone_2_docs_complete': False,
        'milestone_3_dev_complete': False,
        'milestone_3_docs_complete': False,
        'portfolio_final_complete': False,

        'messages': [],
        'notes': 'MEDICANT_BIAS: Multi-agent infrastructure initialized',

        'last_commit': 'e92802d',
        'branch': 'main'
    }
