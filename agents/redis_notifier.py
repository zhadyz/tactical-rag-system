"""
Redis Event Notifier - Background Watcher

Runs in background of Claude Code session.
Listens to Redis pub/sub and prints alerts when events occur.

Usage:
  python agents/redis_notifier.py --agent hollowed_eyes
  python agents/redis_notifier.py --agent zhadyz
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.redis_coordinator import RedisCoordinator


def main():
    parser = argparse.ArgumentParser(description='Redis event notifier for Claude Code sessions')
    parser.add_argument('--agent', required=True, choices=['hollowed_eyes', 'zhadyz'],
                        help='Agent name (which terminal)')
    args = parser.parse_args()

    agent_name = args.agent
    other_agent = 'zhadyz' if agent_name == 'hollowed_eyes' else 'hollowed_eyes'

    print(f"\n[REDIS NOTIFIER] Starting for {agent_name.upper()}")
    print(f"[REDIS NOTIFIER] Listening for events from {other_agent.upper()}...")
    print("[REDIS NOTIFIER] Running in background. This window will show alerts.\n")

    coordinator = RedisCoordinator()

    def handle_event(event):
        """Handle Redis pub/sub events"""
        event_type = event['event']
        data = event.get('data', {})

        # Filter: Only show events relevant to this agent
        if event_type == 'task_completed':
            task_id = data.get('task_id')
            state = coordinator.get_state()

            # Check if this unblocks any of my tasks
            my_tasks = [t for t in state['tasks'] if t['owner'] == agent_name and t['status'] == 'pending']

            for task in my_tasks:
                if task_id in task.get('dependencies', []):
                    print("\n" + "="*70)
                    print(f"[ALERT] Task {task_id} completed!")
                    print(f"[ALERT] Your task {task['id']} is now UNBLOCKED!")
                    print(f"[ALERT] Ready: {task['title']}")
                    print("="*70 + "\n")
                    break

        elif event_type == 'handoff':
            handoff_key = data.get('key')
            handoff_value = data.get('value')

            # Check if this handoff matters to me
            if handoff_value and 'dev_complete' in handoff_key and agent_name == 'zhadyz':
                print("\n" + "="*70)
                print(f"[ALERT] DEV MILESTONE COMPLETE!")
                print(f"[ALERT] Handoff: {handoff_key}")
                print(f"[ALERT] Check for ops tasks!")
                print("="*70 + "\n")

        elif event_type == 'new_message':
            to_agent = data.get('to')
            from_agent = data.get('from')
            subject = data.get('subject')

            if to_agent == agent_name:
                print("\n" + "="*70)
                print(f"[ALERT] New message from {from_agent.upper()}")
                print(f"[ALERT] Subject: {subject}")
                print(f"[ALERT] Check messages!")
                print("="*70 + "\n")

    # Subscribe and listen forever
    try:
        coordinator.subscribe_to_events(handle_event)
    except KeyboardInterrupt:
        print(f"\n[REDIS NOTIFIER] Shutting down for {agent_name}")


if __name__ == "__main__":
    main()
