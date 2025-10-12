"""
HOLLOWED_EYES: Autonomous Development Agent

Runs in infinite loop:
1. Subscribe to Redis pub/sub for real-time events
2. Check for pending dev tasks
3. Detect task when available → Prompt human/Claude Code to implement
4. Human completes task → Agent marks complete automatically
5. Trigger handoffs when milestones reached
6. Repeat

Event-driven: No polling! Reacts to Redis pub/sub in milliseconds.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from infrastructure.redis_coordinator import RedisCoordinator


class HollowedEyesAgent:
    """Autonomous development agent with event-driven coordination"""

    def __init__(self):
        self.coordinator = RedisCoordinator()
        self.agent_id = "hollowed_eyes"
        self.running = True

        print("[AGENT] HOLLOWED_EYES Agent initialized")
        print("   Role: Development (implement features)")
        print("   Mode: Autonomous event-driven operation")
        print("   Coordination: Redis pub/sub")

    def handle_event(self, event: dict):
        """
        Handle Redis pub/sub events in real-time.

        Event types:
        - task_completed: Check if any of my tasks became unblocked
        - handoff: Check if I need to do something
        - new_message: Check messages
        - state_changed: Refresh and check for work

        Args:
            event: Event dictionary from Redis pub/sub
        """
        event_type = event['event']

        print(f"\n[EVENT] [HOLLOWED_EYES] Event received: {event_type}")

        if event_type == 'task_completed':
            # Another task completed - check if mine became unblocked
            print("   → Checking for newly unblocked tasks...")
            self.check_for_work()

        elif event_type == 'handoff':
            # Handoff triggered - might trigger new tasks
            data = event['data']
            print(f"   → Handoff: {data['key']} = {data['value']}")
            self.check_for_work()

        elif event_type == 'new_message':
            data = event['data']
            if data['to'] == self.agent_id:
                print("   → New message for me!")
                self.check_messages()


    def check_for_work(self):
        """
        Check if there's development work to do.

        Logic:
        1. Get pending tasks assigned to me
        2. Check dependencies
        3. Execute highest priority unblocked task
        """
        pending = self.coordinator.get_pending_tasks(self.agent_id)

        if not pending:
            print("[OK] [HOLLOWED_EYES] No pending tasks. Idle.")
            return

        # Sort by priority (lower number = higher priority)
        pending.sort(key=lambda t: t['priority'])

        # Find first unblocked task
        for task in pending:
            if self.coordinator.check_dependencies_met(task):
                print(f"\n[START] [HOLLOWED_EYES] Task ready: {task['id']}")
                self.execute_task(task)
                return

        # All tasks blocked by dependencies
        blocked_tasks = [t['id'] for t in pending]
        print(f"[PAUSE]  [HOLLOWED_EYES] Tasks blocked by dependencies: {blocked_tasks}")
        self.coordinator.update_agent_status(self.agent_id, 'blocked')

    def execute_task(self, task: dict):
        """
        Execute a development task.

        Hybrid approach:
        - Agent autonomously detects and coordinates
        - Human (Claude Code) implements the actual feature
        - Agent marks complete when human signals

        Args:
            task: Task dictionary
        """
        # Mark in progress
        self.coordinator.mark_task_in_progress(task['id'])
        self.coordinator.update_agent_status(
            self.agent_id,
            'working',
            f"{task['id']}: {task['title']}"
        )

        print("\n" + "="*70)
        print("💻 HOLLOWED_EYES: DEVELOPMENT TASK DETECTED")
        print("="*70)
        print(f"\n[TASK] Task ID: {task['id']}")
        print(f"[NOTE] Title: {task['title']}")
        print(f"[DOC] Description:")
        print(f"   {task['description']}")

        if task.get('acceptance_criteria'):
            print(f"\n[OK] Acceptance Criteria:")
            for i, criterion in enumerate(task['acceptance_criteria'], 1):
                print(f"   {i}. {criterion}")

        if task.get('files_to_modify'):
            print(f"\n[FILES] Files to Modify:")
            for file in task['files_to_modify']:
                print(f"   - {file}")

        print("\n" + "="*70)
        print("[TARGET] ACTION REQUIRED: CLAUDE CODE / HUMAN")
        print("="*70)
        print("\nThis is where YOU (Claude Code) take over:")
        print("  1. Read the task description above")
        print("  2. Implement the feature")
        print("  3. Test locally")
        print("  4. Commit to git")
        print("\n  [PAUSE]  Agent paused. Press Enter when task is complete...")
        print("="*70)

        # Wait for human/Claude Code to complete work
        try:
            input()
        except EOFError:
            print("\n[WARN]  EOF detected (non-interactive mode). Auto-completing for demo...")
            time.sleep(2)

        # Mark complete
        print("\n[OK] [HOLLOWED_EYES] Marking task complete...")
        self.coordinator.mark_task_complete(task['id'])
        self.coordinator.update_agent_status(self.agent_id, 'idle')

        # Check if milestone complete (trigger handoffs)
        self.check_milestone_handoffs(task['id'])

        print(f"[OK] Task {task['id']} complete!")
        print("   Notifying other agents via Redis pub/sub...")

    def check_milestone_handoffs(self, completed_task_id: str):
        """
        Check if completing this task triggers a milestone handoff.

        Handoff triggers:
        - dev-002 complete → milestone_2_dev_complete
        - dev-003 complete → milestone_3_dev_complete
        - etc.

        Args:
            completed_task_id: Just-completed task ID
        """
        state = self.coordinator.get_state()

        # Check milestone 2
        if completed_task_id == 'dev-002':
            print("\n[MILESTONE] Milestone 2 dev complete! Setting handoff...")
            self.coordinator.set_handoff('milestone_2_dev_complete', True)

        # Check milestone 3
        elif completed_task_id == 'dev-003':
            print("\n[MILESTONE] Milestone 3 dev complete! Setting handoff...")
            self.coordinator.set_handoff('milestone_3_dev_complete', True)

        # Check if ALL dev tasks done
        all_dev_done = all(
            t['status'] == 'complete'
            for t in state['tasks']
            if t['owner'] == 'hollowed_eyes'
        )

        if all_dev_done:
            print("\n[COMPLETE] ALL DEV TASKS COMPLETE!")
            self.coordinator.send_message(
                from_agent=self.agent_id,
                to_agent='zhadyz',
                subject='All development complete',
                body='All development tasks finished. Ready for final portfolio polish.'
            )

    def check_messages(self):
        """Check for new messages from other agents"""
        messages = self.coordinator.get_messages(self.agent_id, unread_only=True)

        if messages:
            print("\n[MSG] [HOLLOWED_EYES] New messages:")
            for msg in messages:
                print(f"\n   From: {msg['from']}")
                print(f"   Subject: {msg['subject']}")
                print(f"   Body: {msg['body']}")
                print(f"   Time: {msg['timestamp']}")

    def send_heartbeat(self):
        """Send periodic heartbeat to show agent is alive"""
        self.coordinator.send_heartbeat(self.agent_id)

    def run(self):
        """
        Main autonomous loop.

        Runs forever:
        1. Subscribe to Redis pub/sub
        2. React to events in real-time
        3. Check for work periodically
        4. Send heartbeats

        Ctrl+C to stop.
        """
        print("\n" + "="*70)
        print("[AGENT] HOLLOWED_EYES AGENT STARTING")
        print("="*70)
        print("[LOOP] Running autonomously...")
        print("[PUBSUB] Redis pub/sub: ACTIVE")
        print("[FAST] Event-driven coordination: ENABLED")
        print("\nPress Ctrl+C to stop\n")
        print("="*70)

        # Initial check
        print("\n[SEARCH] Initial work check...")
        self.check_for_work()

        # Subscribe to events and run forever
        try:
            # Start event listener (blocks)
            self.coordinator.subscribe_to_events(self.handle_event)

        except KeyboardInterrupt:
            print("\n\n[STOP] HOLLOWED_EYES shutting down...")
            self.coordinator.update_agent_status(self.agent_id, 'idle')
            self.running = False


if __name__ == "__main__":
    agent = HollowedEyesAgent()
    agent.run()
