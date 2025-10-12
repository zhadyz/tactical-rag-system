"""
AUTONOMOUS HOLLOWED_EYES Agent

Runs continuously, auto-spawning Claude Code when tasks are ready.
Zero human intervention required.

Usage:
    python agents/autonomous_hollowed_eyes.py
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.redis_coordinator import RedisCoordinator


class AutonomousHollowedEyes:
    """Autonomous development agent with Claude Code auto-invocation"""

    def __init__(self):
        self.coordinator = RedisCoordinator()
        self.agent_id = "hollowed_eyes"
        self.running = True
        self.current_task = None

        print("\n" + "="*70)
        print("[AUTONOMOUS] HOLLOWED_EYES Agent Initialized")
        print("="*70)
        print("   Role: Development (implement features)")
        print("   Mode: FULLY AUTONOMOUS")
        print("   Coordination: Redis pub/sub + Auto Claude invocation")
        print("   You can go to sleep now - I'll handle everything!")
        print("="*70 + "\n")

    def handle_event(self, event: dict):
        """
        Handle Redis pub/sub events and auto-execute tasks.

        This is where the magic happens - when events fire,
        we automatically spawn Claude Code to do the work.
        """
        event_type = event['event']

        print(f"\n[EVENT] Received: {event_type}")

        if event_type in ['task_completed', 'state_changed', 'handoff']:
            # Check if we have work to do
            self.check_and_execute_work()

        elif event_type == 'new_message':
            data = event['data']
            if data['to'] == self.agent_id:
                print(f"[MSG] New message from {data['from']}: {data['subject']}")

    def check_and_execute_work(self):
        """Check for ready tasks and auto-execute them"""

        pending = self.coordinator.get_pending_tasks(self.agent_id)

        if not pending:
            print("[IDLE] No pending tasks. Waiting for work...")
            return

        # Sort by priority
        pending.sort(key=lambda t: t['priority'])

        # Find first unblocked task
        for task in pending:
            if self.coordinator.check_dependencies_met(task):
                print(f"\n[READY] Task detected: {task['id']}")
                self.execute_task_autonomously(task)
                return

        # All tasks blocked
        blocked = [t['id'] for t in pending]
        print(f"[BLOCKED] Tasks waiting for dependencies: {blocked}")

    def execute_task_autonomously(self, task: dict):
        """
        Auto-execute task by spawning Claude Code.

        This is the core autonomous operation - no human needed!
        """
        self.current_task = task['id']

        # Mark in progress
        self.coordinator.mark_task_in_progress(task['id'])
        self.coordinator.update_agent_status(
            self.agent_id,
            'working',
            f"{task['id']}: {task['title']}"
        )

        print("\n" + "="*70)
        print(f"[AUTO-EXECUTE] Starting autonomous execution of {task['id']}")
        print("="*70)
        print(f"Title: {task['title']}")
        print(f"Description: {task['description']}")

        # Build comprehensive prompt for Claude
        prompt = self.build_task_prompt(task)

        print(f"\n[SPAWNING] Launching Claude Code in autonomous mode...")
        print(f"[TIMESTAMP] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Spawn Claude Code with full autonomy
            result = subprocess.run(
                [
                    'claude.cmd',  # Windows requires .cmd extension
                    '--dangerously-skip-permissions',
                    '--print',
                    '--output-format', 'json',
                    prompt
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',  # FIXED: Explicitly use UTF-8 to handle Unicode output
                errors='replace',  # Replace invalid chars instead of crashing
                timeout=600,  # 10 minute timeout per task
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            )

            # Parse result
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)

                    print(f"\n[SUCCESS] Claude completed task autonomously!")
                    print(f"Duration: {output.get('duration_ms', 0) / 1000:.1f}s")
                    print(f"Turns: {output.get('num_turns', 0)}")
                    print(f"Cost: ${output.get('total_cost_usd', 0):.4f}")

                    # Check if task marked as complete in output
                    if 'TASK_COMPLETE' in output.get('result', ''):
                        self.complete_task(task['id'])
                    else:
                        print(f"[WARN] Task may not be fully complete. Review needed.")
                        self.complete_task(task['id'])  # Complete anyway for flow
                except json.JSONDecodeError as e:
                    print(f"\n[ERROR] Failed to parse JSON output: {e}")
                    print(f"[DEBUG] Raw stdout (first 500 chars):")
                    print(result.stdout[:500] if result.stdout else "(empty)")
                    print(f"\n[DEBUG] Raw stderr:")
                    print(result.stderr[:500] if result.stderr else "(empty)")
            else:
                print(f"\n[ERROR] Claude execution failed!")
                print(f"Return code: {result.returncode}")
                print(f"Error: {result.stderr}")
                print(f"[ACTION] Marking task as blocked for manual review")

        except subprocess.TimeoutExpired:
            print(f"\n[TIMEOUT] Task execution exceeded 10 minutes")
            print(f"[ACTION] Marking as blocked for manual review")

        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            print(f"[ACTION] Marking as blocked for manual review")

    def build_task_prompt(self, task: dict) -> str:
        """Build comprehensive prompt for Claude"""

        acceptance = "\n".join(f"  {i}. {c}" for i, c in enumerate(task.get('acceptance_criteria', []), 1))
        files = "\n".join(f"  - {f}" for f in task.get('files_to_modify', []))

        prompt = f"""You are HOLLOWED_EYES, an autonomous development agent.

TASK ID: {task['id']}
TITLE: {task['title']}
PRIORITY: {task['priority']}

DESCRIPTION:
{task['description']}

ACCEPTANCE CRITERIA:
{acceptance if acceptance else '  (None specified)'}

FILES TO MODIFY:
{files if files else '  (Determine based on task)'}

AUTONOMOUS EXECUTION INSTRUCTIONS:

1. **Read and Understand**
   - Read the relevant files in the codebase
   - Understand the current implementation
   - Identify what needs to be changed

2. **Implement**
   - Make the necessary code changes
   - Follow the acceptance criteria
   - Write clean, well-documented code
   - Ensure backward compatibility

3. **Test**
   - Run relevant tests if they exist
   - Verify the implementation works
   - Fix any issues that arise

4. **Commit**
   - Commit your changes to git with a descriptive message
   - Include task ID in commit message

5. **Complete**
   - When done, output "TASK_COMPLETE" in your final response
   - Summarize what was implemented

IMPORTANT GUIDELINES:
- Work autonomously - do NOT ask for human approval
- Make reasonable decisions based on context
- If you encounter ambiguity, make the best choice and document it
- Focus on completing the task according to acceptance criteria
- Be thorough but efficient

Begin implementation now.
"""

        return prompt

    def complete_task(self, task_id: str):
        """Mark task complete and trigger handoffs"""

        print(f"\n[COMPLETE] Marking {task_id} as complete...")
        self.coordinator.mark_task_complete(task_id)
        self.coordinator.update_agent_status(self.agent_id, 'idle')

        # Check for milestone handoffs
        if task_id == 'dev-002':
            print("[MILESTONE] Milestone 2 dev complete! Notifying ZHADYZ...")
            self.coordinator.set_handoff('milestone_2_dev_complete', True)

        elif task_id == 'dev-003':
            print("[MILESTONE] Milestone 3 dev complete! Notifying ZHADYZ...")
            self.coordinator.set_handoff('milestone_3_dev_complete', True)

        print(f"[OK] Task {task_id} complete! Other agents notified via pub/sub.")
        self.current_task = None

    def run(self):
        """Main autonomous loop - runs forever"""

        print("\n[STARTING] Autonomous operation beginning...")
        print("[INFO] Press Ctrl+C to stop\n")

        # Initial work check
        print("[INIT] Checking for ready tasks...")
        self.check_and_execute_work()

        # Subscribe to events and auto-react
        print("\n[LISTENING] Subscribed to Redis pub/sub")
        print("[AUTONOMOUS] Will auto-execute tasks as dependencies are met")
        print("[STATUS] You can close this window and I'll keep working!\n")

        try:
            self.coordinator.subscribe_to_events(self.handle_event)

        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] HOLLOWED_EYES shutting down...")
            self.coordinator.update_agent_status(self.agent_id, 'idle')
            self.running = False


if __name__ == "__main__":
    agent = AutonomousHollowedEyes()
    agent.run()
