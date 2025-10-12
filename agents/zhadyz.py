"""
ZHADYZ: Autonomous DevOps Agent

Runs in infinite loop:
1. Subscribe to Redis pub/sub for real-time events
2. Wait for dev_complete handoffs or check for ops tasks
3. Execute testing, documentation, deployment
4. Update state and trigger final handoffs
5. Repeat

Event-driven: Reacts instantly to dev handoffs via Redis pub/sub
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from infrastructure.redis_coordinator import RedisCoordinator


class ZhadyzAgent:
    """Autonomous DevOps agent with event-driven coordination"""

    def __init__(self):
        self.coordinator = RedisCoordinator()
        self.agent_id = "zhadyz"
        self.running = True

        print("[AGENT] ZHADYZ Agent initialized")
        print("   Role: DevOps (test, document, deploy)")
        print("   Mode: Autonomous event-driven operation")
        print("   Coordination: Redis pub/sub")

    def handle_event(self, event: dict):
        """
        Handle Redis pub/sub events in real-time.

        Event types:
        - handoff: Dev milestone complete → Start testing/docs
        - task_completed: Check if any of my tasks became unblocked
        - new_message: Check messages
        - state_changed: Refresh and check for work

        Args:
            event: Event dictionary from Redis pub/sub
        """
        event_type = event['event']

        print(f"\n[EVENT] [ZHADYZ] Event received: {event_type}")

        if event_type == 'handoff':
            data = event['data']
            handoff_key = data['key']
            handoff_value = data['value']

            print(f"   → Handoff: {handoff_key} = {handoff_value}")

            # React to milestone completions
            if 'dev_complete' in handoff_key and handoff_value:
                print("   [ALERT] DEV MILESTONE COMPLETE! Starting ops tasks...")
                self.check_for_work()

        elif event_type == 'task_completed':
            # Another task completed - check if mine became unblocked
            print("   → Checking for newly unblocked tasks...")
            self.check_for_work()

        elif event_type == 'new_message':
            data = event['data']
            if data['to'] == self.agent_id:
                print("   → New message for me!")
                self.check_messages()


    def check_for_work(self):
        """
        Check if there's DevOps work to do.

        Logic:
        1. Get pending tasks assigned to me
        2. Check dependencies
        3. Execute highest priority unblocked task
        4. Check if dev handoffs require action
        """
        state = self.coordinator.get_state()
        pending = self.coordinator.get_pending_tasks(self.agent_id)

        # Check for dev handoffs
        dev_ready = (
            state.get('milestone_2_dev_complete', False) or
            state.get('milestone_3_dev_complete', False)
        )

        if not pending:
            if dev_ready:
                print("[OK] [ZHADYZ] Dev code ready but no explicit tasks.")
                print("   Standing by for instructions...")
            else:
                print("[OK] [ZHADYZ] No pending tasks. Idle.")

            
            return

        # Sort by priority (lower number = higher priority)
        pending.sort(key=lambda t: t['priority'])

        # Find first unblocked task
        for task in pending:
            if self.coordinator.check_dependencies_met(task):
                print(f"\n[START] [ZHADYZ] Task ready: {task['id']}")
                self.execute_task(task)
                return

        # All tasks blocked by dependencies
        blocked_tasks = [t['id'] for t in pending]
        print(f"[PAUSE]  [ZHADYZ] Tasks blocked by dependencies: {blocked_tasks}")
        self.coordinator.update_agent_status(self.agent_id, 'blocked')

    def execute_task(self, task: dict):
        """
        Execute a DevOps task (testing, documentation, deployment).

        Hybrid approach:
        - Agent autonomously detects and coordinates
        - Human (Claude Code) performs actual work
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
        print("[START] ZHADYZ: DEVOPS TASK DETECTED")
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
        print("  1. Run tests and verify dev work")
        print("  2. Write/update documentation")
        print("  3. Create examples/demos")
        print("  4. Deploy if required")
        print("  5. Commit to git")
        print("\n  [PAUSE]  Agent paused. Press Enter when task is complete...")
        print("="*70)

        # Wait for human/Claude Code to complete work
        try:
            input()
        except EOFError:
            print("\n[WARN]  EOF detected (non-interactive mode). Auto-completing for demo...")
            time.sleep(2)

        # Mark complete
        print("\n[OK] [ZHADYZ] Marking task complete...")
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
        - ops-002 complete → milestone_2_docs_complete
        - ops-003 complete → milestone_3_docs_complete
        - ops-004 complete → portfolio_final_complete

        Args:
            completed_task_id: Just-completed task ID
        """
        state = self.coordinator.get_state()

        # Check milestone 2
        if completed_task_id == 'ops-002':
            print("\n[MILESTONE] Milestone 2 docs complete! Setting handoff...")
            self.coordinator.set_handoff('milestone_2_docs_complete', True)

        # Check milestone 3
        elif completed_task_id == 'ops-003':
            print("\n[MILESTONE] Milestone 3 docs complete! Setting handoff...")
            self.coordinator.set_handoff('milestone_3_docs_complete', True)

        # Check final portfolio
        elif completed_task_id == 'ops-004':
            print("\n[COMPLETE] PORTFOLIO FINALIZATION COMPLETE!")
            self.coordinator.set_handoff('portfolio_final_complete', True)

            # Send completion message
            self.coordinator.send_message(
                from_agent=self.agent_id,
                to_agent='hollowed_eyes',
                subject='PROJECT COMPLETE',
                body='All tasks complete. Portfolio ready for Booz Allen submission!'
            )

            print("\n" + "="*70)
            print("[COMPLETE] TACTICAL RAG IMPROVEMENTS: COMPLETE")
            print("="*70)
            print("\nAll milestones achieved:")
            print("  [OK] Milestone 1: Conversation Memory")
            print("  [OK] Milestone 2: Explainability Features")
            print("  [OK] Milestone 3: User Feedback System")
            print("  [OK] Milestone 4: Portfolio Finalization")
            print("\n[START] Ready for deployment and portfolio showcase!")
            print("="*70)

    def check_messages(self):
        """Check for new messages from other agents"""
        messages = self.coordinator.get_messages(self.agent_id, unread_only=True)

        if messages:
            print("\n[MSG] [ZHADYZ] New messages:")
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
        2. React to handoff events in real-time
        3. Check for work periodically
        4. Send heartbeats

        Ctrl+C to stop.
        """
        print("\n" + "="*70)
        print("[AGENT] ZHADYZ AGENT STARTING")
        print("="*70)
        print("[LOOP] Running autonomously...")
        print("[PUBSUB] Redis pub/sub: ACTIVE")
        print("[FAST] Event-driven coordination: ENABLED")
        print("[WAIT] Waiting for dev handoffs...")
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
            print("\n\n[STOP] ZHADYZ shutting down...")
            self.coordinator.update_agent_status(self.agent_id, 'idle')
            self.running = False


if __name__ == "__main__":
    agent = ZhadyzAgent()
    agent.run()
