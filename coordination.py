"""
Claude Code 2.0 Multi-Agent Coordination Helper

Simple functions for Claude Code sessions to coordinate via Redis.

Usage in Claude Code session:
  from coordination import start_notifier, complete_task, check_my_tasks

  # At start of session
  start_notifier('hollowed_eyes')

  # After completing work
  complete_task('dev-002')

  # Check what's ready
  check_my_tasks('hollowed_eyes')
"""

import subprocess
import sys
import os
from infrastructure.redis_coordinator import RedisCoordinator


def start_notifier(agent_name):
    """
    Start background Redis notifier for this terminal.

    Args:
        agent_name: 'hollowed_eyes' or 'zhadyz'

    This spawns a background process that prints alerts when
    the other agent completes tasks.
    """
    print(f"\n[COORDINATION] Starting background notifier for {agent_name.upper()}...")

    script_path = os.path.join(os.path.dirname(__file__), 'agents', 'redis_notifier.py')

    if sys.platform == 'win32':
        # Windows: Start in new background process
        subprocess.Popen(
            ['python', script_path, '--agent', agent_name],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        # Unix: Start with nohup
        subprocess.Popen(
            ['python', script_path, '--agent', agent_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    print(f"[COORDINATION] Background notifier started!")
    print(f"[COORDINATION] You will see alerts when tasks complete.\n")


def check_my_tasks(agent_name):
    """
    Check pending tasks for this agent.

    Args:
        agent_name: 'hollowed_eyes' or 'zhadyz'

    Returns:
        List of pending tasks with dependency status
    """
    coordinator = RedisCoordinator()
    state = coordinator.get_state()

    my_tasks = [t for t in state['tasks'] if t['owner'] == agent_name]

    print(f"\n{'='*70}")
    print(f"{agent_name.upper()} TASK STATUS")
    print(f"{'='*70}\n")

    ready_tasks = []
    blocked_tasks = []

    for task in my_tasks:
        status = task['status']

        if status == 'complete':
            print(f"[COMPLETE] {task['id']}: {task['title']}")
        elif status == 'in_progress':
            print(f"[IN PROGRESS] {task['id']}: {task['title']}")
        elif status == 'pending':
            # Check dependencies
            deps_met = coordinator.check_dependencies_met(task)

            if deps_met:
                print(f"[READY] {task['id']}: {task['title']}")
                print(f"   Priority: {task['priority']}")
                ready_tasks.append(task)
            else:
                print(f"[BLOCKED] {task['id']}: {task['title']}")
                print(f"   Waiting for: {task.get('dependencies', [])}")
                blocked_tasks.append(task)

    print(f"\n{'='*70}\n")

    if ready_tasks:
        print(f"[OK] {len(ready_tasks)} task(s) ready to start")
        return ready_tasks[0]  # Return highest priority ready task
    elif blocked_tasks:
        print(f"[WAITING] All tasks blocked by dependencies")
        return None
    else:
        print("[OK] All tasks complete!")
        return None


def complete_task(task_id, commit_hash=None):
    """
    Mark task as complete and notify other agents via Redis.

    Args:
        task_id: Task identifier (e.g., 'dev-002')
        commit_hash: Optional git commit hash

    This triggers Redis pub/sub event that alerts other terminals.
    """
    coordinator = RedisCoordinator()

    print(f"\n[COORDINATION] Marking {task_id} as complete...")
    coordinator.mark_task_complete(task_id)

    if commit_hash:
        state = coordinator.get_state()
        state['last_commit'] = commit_hash
        coordinator.update_state(state)

    print(f"[COORDINATION] [OK] Task {task_id} complete!")
    print(f"[COORDINATION] Redis pub/sub event sent - other agents notified")

    # Check if this triggers a milestone handoff
    if 'dev-002' in task_id:
        coordinator.set_handoff('milestone_2_dev_complete', True)
        print(f"[COORDINATION] [MILESTONE] Milestone 2 dev complete - ZHADYZ notified!")
    elif 'dev-003' in task_id:
        coordinator.set_handoff('milestone_3_dev_complete', True)
        print(f"[COORDINATION] [MILESTONE] Milestone 3 dev complete - ZHADYZ notified!")

    print()


def send_message(from_agent, to_agent, subject, body):
    """
    Send message to other agent.

    Triggers alert in other terminal via Redis pub/sub.
    """
    coordinator = RedisCoordinator()
    coordinator.send_message(from_agent, to_agent, subject, body)
    print(f"\n[COORDINATION] Message sent to {to_agent.upper()}")
    print(f"[COORDINATION] They will be notified immediately.\n")


def get_stats():
    """Get coordination statistics"""
    coordinator = RedisCoordinator()
    stats = coordinator.get_stats()

    print(f"\n{'='*70}")
    print("MULTI-AGENT COORDINATION STATS")
    print(f"{'='*70}")
    print(f"Total Tasks: {stats['total_tasks']}")
    print(f"Pending: {stats['pending']}")
    print(f"In Progress: {stats['in_progress']}")
    print(f"Complete: {stats['complete']}")
    print(f"State Version: {stats['state_version']}")
    print(f"{'='*70}\n")


# Quick start helper
def init(agent_name):
    """
    Quick initialization for Claude Code session.

    Usage:
      from coordination import init
      init('hollowed_eyes')  # or 'zhadyz'

    This starts background notifier and shows pending tasks.
    """
    print(f"\n[INIT] Initializing {agent_name.upper()} coordination...")
    start_notifier(agent_name)
    return check_my_tasks(agent_name)
