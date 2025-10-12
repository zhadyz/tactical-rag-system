"""
LangGraph Workflow Definition
Defines the agent workflow as a StateGraph for Tactical RAG improvements

This demonstrates production-grade multi-agent orchestration using LangGraph.
"""

from langgraph.graph import StateGraph, END
from infrastructure.state import MultiAgentState
from infrastructure.redis_coordinator import RedisCoordinator
from typing import Literal

# Initialize coordinator (shared across all nodes)
coordinator = RedisCoordinator()


def medicant_bias_node(state: MultiAgentState) -> MultiAgentState:
    """
    MEDICANT_BIAS: Setup node
    Runs once to initialize architecture, migrate tasks, and terminate.

    This node:
    - Reads existing state.json
    - Migrates remaining tasks to Redis
    - Sets up coordination infrastructure
    - Terminates (never runs again)
    """
    print("\n🧠 MEDICANT_BIAS: Initializing project...")
    print("   Migrating tasks from state.json to Redis...")
    print("   Setting up LangGraph workflow...")

    # Setup is handled by setup.py, this is just a placeholder node
    state['project_phase'] = 'development'
    state['notes'] = 'MEDICANT_BIAS setup complete. Agents running autonomously.'

    return state


def hollowed_eyes_node(state: MultiAgentState) -> MultiAgentState:
    """
    HOLLOWED_EYES: Development node
    Executes when there are pending dev tasks

    Triggered by:
    - Initial task assignment
    - Task completion (checks for newly unblocked tasks)
    - Handoff signals

    NOTE: The actual Claude Code work happens in agents/hollowed_eyes.py
    This node just updates the state graph.
    """
    # Check for pending tasks
    pending = [
        t for t in state['tasks']
        if t['owner'] == 'hollowed_eyes' and t['status'] == 'pending'
    ]

    if not pending:
        state['hollowed_eyes']['status'] = 'idle'
        return state

    # Task execution happens in autonomous agent
    # This node just tracks state transitions
    state['hollowed_eyes']['status'] = 'working'

    return state


def zhadyz_node(state: MultiAgentState) -> MultiAgentState:
    """
    ZHADYZ: DevOps node
    Executes when:
    - Code ready handoff triggered
    - There are pending ops tasks

    Triggered by:
    - milestone_N_dev_complete handoff
    - Task completion (checks for newly unblocked tasks)

    NOTE: The actual work happens in agents/zhadyz.py
    This node just updates the state graph.
    """
    # Check for pending tasks
    pending = [
        t for t in state['tasks']
        if t['owner'] == 'zhadyz' and t['status'] == 'pending'
    ]

    # Check if dev code ready for testing
    dev_ready = (
        state.get('milestone_1_dev_complete', False) or
        state.get('milestone_2_dev_complete', False) or
        state.get('milestone_3_dev_complete', False)
    )

    if not pending and not dev_ready:
        state['zhadyz']['status'] = 'idle'
        return state

    # Task execution happens in autonomous agent
    state['zhadyz']['status'] = 'working'

    return state


def should_continue(state: MultiAgentState) -> Literal["hollowed_eyes", "zhadyz", "end"]:
    """
    Router: Decide which agent should execute next

    Decision logic:
    1. If all tasks complete and final handoff done → END
    2. If HOLLOWED_EYES has pending tasks → hollowed_eyes
    3. If ZHADYZ has pending tasks or code ready → zhadyz
    4. Otherwise → END

    Returns:
        Next node to execute
    """
    # Check if project complete
    all_complete = all(t['status'] == 'complete' for t in state['tasks'])
    if all_complete and state.get('portfolio_final_complete', False):
        return 'end'

    # Check HOLLOWED_EYES tasks
    hollowed_tasks = [
        t for t in state['tasks']
        if t['owner'] == 'hollowed_eyes' and t['status'] == 'pending'
    ]
    if hollowed_tasks:
        return 'hollowed_eyes'

    # Check ZHADYZ tasks (or code ready handoffs)
    zhadyz_tasks = [
        t for t in state['tasks']
        if t['owner'] == 'zhadyz' and t['status'] == 'pending'
    ]

    dev_ready = (
        state.get('milestone_1_dev_complete', False) or
        state.get('milestone_2_dev_complete', False) or
        state.get('milestone_3_dev_complete', False)
    )

    if zhadyz_tasks or dev_ready:
        return 'zhadyz'

    return 'end'


# ===== BUILD LANGGRAPH WORKFLOW =====

# Create StateGraph
workflow = StateGraph(MultiAgentState)

# Add nodes (agent execution points)
workflow.add_node("medicant_bias", medicant_bias_node)
workflow.add_node("hollowed_eyes", hollowed_eyes_node)
workflow.add_node("zhadyz", zhadyz_node)

# Set entry point (starts with MEDICANT_BIAS setup)
workflow.set_entry_point("medicant_bias")

# Add conditional edges (routing logic)
workflow.add_conditional_edges(
    "medicant_bias",
    should_continue,
    {
        "hollowed_eyes": "hollowed_eyes",
        "zhadyz": "zhadyz",
        "end": END
    }
)

workflow.add_conditional_edges(
    "hollowed_eyes",
    should_continue,
    {
        "hollowed_eyes": "hollowed_eyes",  # Can loop back to self
        "zhadyz": "zhadyz",
        "end": END
    }
)

workflow.add_conditional_edges(
    "zhadyz",
    should_continue,
    {
        "hollowed_eyes": "hollowed_eyes",
        "zhadyz": "zhadyz",  # Can loop back to self
        "end": END
    }
)

# Compile the workflow
app = workflow.compile()

print("[OK] LangGraph workflow compiled successfully")
print("   Nodes: medicant_bias -> hollowed_eyes <-> zhadyz -> END")
print("   Routing: Conditional based on task ownership and dependencies")
