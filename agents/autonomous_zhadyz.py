"""
AUTONOMOUS ZHADYZ Agent

Runs continuously, auto-spawning Claude Code when ops tasks are ready.
Handles testing, documentation, and deployment autonomously.

Usage:
    python agents/autonomous_zhadyz.py
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


class AutonomousZhadyz:
    """Autonomous DevOps agent with Claude Code auto-invocation"""

    def __init__(self):
        self.coordinator = RedisCoordinator()
        self.agent_id = "zhadyz"
        self.running = True
        self.current_task = None

        print("\n" + "="*70)
        print("[AUTONOMOUS] ZHADYZ Agent Initialized")
        print("="*70)
        print("   Role: DevOps (test, document, deploy)")
        print("   Mode: FULLY AUTONOMOUS")
        print("   Coordination: Redis pub/sub + Auto Claude invocation")
        print("   You can go to sleep now - I'll handle everything!")
        print("="*70 + "\n")

    def handle_event(self, event: dict):
        """
        Handle Redis pub/sub events and auto-execute tasks.
        """
        event_type = event['event']

        print(f"\n[EVENT] Received: {event_type}")

        if event_type == 'handoff':
            data = event['data']
            if 'dev_complete' in data.get('key', ''):
                print(f"[HANDOFF] Dev milestone complete! Checking for ops work...")
                self.check_and_execute_work()

        elif event_type in ['task_completed', 'state_changed']:
            self.check_and_execute_work()

        elif event_type == 'new_message':
            data = event['data']
            if data['to'] == self.agent_id:
                print(f"[MSG] New message from {data['from']}: {data['subject']}")

    def check_and_execute_work(self):
        """Check for ready tasks and auto-execute them"""

        pending = self.coordinator.get_pending_tasks(self.agent_id)

        if not pending:
            print("[IDLE] No pending ops tasks. Waiting for dev work...")
            return

        # Sort by priority
        pending.sort(key=lambda t: t['priority'])

        # Find first unblocked task
        for task in pending:
            if self.coordinator.check_dependencies_met(task):
                print(f"\n[READY] Ops task detected: {task['id']}")
                self.execute_task_autonomously(task)
                return

        # All tasks blocked
        blocked = [t['id'] for t in pending]
        print(f"[BLOCKED] Ops tasks waiting for dependencies: {blocked}")

    def execute_task_autonomously(self, task: dict):
        """Auto-execute ops task by spawning Claude Code"""

        self.current_task = task['id']

        # Mark in progress
        self.coordinator.mark_task_in_progress(task['id'])
        self.coordinator.update_agent_status(
            self.agent_id,
            'working',
            f"{task['id']}: {task['title']}"
        )

        print("\n" + "="*70)
        print(f"[AUTO-EXECUTE] Starting autonomous ops execution of {task['id']}")
        print("="*70)
        print(f"Title: {task['title']}")
        print(f"Description: {task['description']}")

        # Build ops-specific prompt
        prompt = self.build_ops_prompt(task)

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
                timeout=600,  # 10 minute timeout
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            )

            # Parse result
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)

                    print(f"\n[SUCCESS] Claude completed ops task autonomously!")
                    print(f"Duration: {output.get('duration_ms', 0) / 1000:.1f}s")
                    print(f"Turns: {output.get('num_turns', 0)}")
                    print(f"Cost: ${output.get('total_cost_usd', 0):.4f}")

                    # Complete task
                    self.complete_task(task['id'])
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

        except subprocess.TimeoutExpired:
            print(f"\n[TIMEOUT] Ops task exceeded 10 minutes")

        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")

    def build_ops_prompt(self, task: dict) -> str:
        """Build ops-specific prompt for Claude"""

        acceptance = "\n".join(f"  {i}. {c}" for i, c in enumerate(task.get('acceptance_criteria', []), 1))
        files = "\n".join(f"  - {f}" for f in task.get('files_to_modify', []))

        prompt = f"""You are ZHADYZ, an autonomous DevOps agent.

TASK ID: {task['id']}
TITLE: {task['title']}
PRIORITY: {task['priority']}

DESCRIPTION:
{task['description']}

ACCEPTANCE CRITERIA:
{acceptance if acceptance else '  (None specified)'}

FILES TO CHECK/MODIFY:
{files if files else '  (Determine based on task)'}

AUTONOMOUS EXECUTION INSTRUCTIONS:

1. **Verify Development Work**
   - Review the code changes from the corresponding dev task
   - Check that implementation matches requirements
   - Run any existing tests to verify functionality

2. **Testing**
   - Run the test suite if it exists
   - If tests don't exist, manually verify the feature works
   - Check Docker deployment if applicable
   - Document test results

3. **Documentation**
   - Update or create documentation for the feature
   - Add code comments where needed
   - Create examples or usage guides
   - Update README if applicable

4. **Validation**
   - Ensure all acceptance criteria are met
   - Verify no regressions were introduced
   - Check that feature integrates properly

5. **Commit**
   - Commit documentation updates to git
   - Include task ID in commit message
   - Use descriptive commit messages

6. **Complete**
   - When done, output "TASK_COMPLETE" in your final response
   - Summarize testing/documentation work completed

IMPORTANT GUIDELINES:
- Work autonomously - do NOT ask for human approval
- Focus on quality assurance and documentation
- If tests fail, document the issues clearly
- Make reasonable judgments about completeness
- Be thorough in verification

Begin ops work now.
"""

        return prompt

    def complete_task(self, task_id: str):
        """Mark task complete and trigger handoffs"""

        print(f"\n[COMPLETE] Marking {task_id} as complete...")
        self.coordinator.mark_task_complete(task_id)
        self.coordinator.update_agent_status(self.agent_id, 'idle')

        # Check for milestone handoffs
        if task_id == 'ops-002':
            print("[MILESTONE] Milestone 2 docs complete! Notifying HOLLOWED_EYES...")
            self.coordinator.set_handoff('milestone_2_docs_complete', True)

        elif task_id == 'ops-003':
            print("[MILESTONE] Milestone 3 docs complete!")
            self.coordinator.set_handoff('milestone_3_docs_complete', True)

        elif task_id == 'ops-004':
            print("[COMPLETE] PORTFOLIO FINALIZATION COMPLETE!")
            self.coordinator.set_handoff('portfolio_final_complete', True)

            # Send completion message
            self.coordinator.send_message(
                from_agent=self.agent_id,
                to_agent='hollowed_eyes',
                subject='PROJECT COMPLETE',
                body='All ops tasks complete. Portfolio ready!'
            )

        print(f"[OK] Ops task {task_id} complete! Other agents notified via pub/sub.")
        self.current_task = None

    def run(self):
        """Main autonomous loop - runs forever"""

        print("\n[STARTING] Autonomous ops operation beginning...")
        print("[INFO] Press Ctrl+C to stop\n")

        # Initial work check
        print("[INIT] Checking for ready ops tasks...")
        self.check_and_execute_work()

        # Subscribe to events and auto-react
        print("\n[LISTENING] Subscribed to Redis pub/sub")
        print("[AUTONOMOUS] Will auto-execute ops tasks as dev work completes")
        print("[STATUS] You can close this window and I'll keep working!\n")

        try:
            self.coordinator.subscribe_to_events(self.handle_event)

        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] ZHADYZ shutting down...")
            self.coordinator.update_agent_status(self.agent_id, 'idle')
            self.running = False


if __name__ == "__main__":
    agent = AutonomousZhadyz()
    agent.run()
