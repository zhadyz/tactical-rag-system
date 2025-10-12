"""
Real-Time Multi-Agent Monitoring Dashboard

Displays live status of:
- Agent states (idle, working, blocked)
- Task progress
- Handoffs
- Recent events
- System statistics

Refreshes every 2 seconds. Press Ctrl+C to exit.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
from datetime import datetime
from infrastructure.redis_coordinator import RedisCoordinator


def clear_screen():
    """Clear terminal screen (cross-platform)"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_time_since(timestamp_str: str) -> str:
    """Get human-readable time since timestamp"""
    try:
        ts = datetime.fromisoformat(timestamp_str)
        delta = datetime.now() - ts
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds/60)}m ago"
        else:
            return f"{int(seconds/3600)}h ago"
    except:
        return "unknown"


def render_dashboard(coordinator: RedisCoordinator):
    """Render the monitoring dashboard"""
    clear_screen()

    state = coordinator.get_state()
    stats = coordinator.get_stats()

    # Header
    print("=" * 80)
    print("🤖 MULTI-AGENT SYSTEM - REAL-TIME DASHBOARD")
    print("=" * 80)
    print(f"📊 Project: {state['project_name']}")
    print(f"🔗 Baseline: {state['baseline_commit']}")
    print(f"📍 Phase: {state['project_phase']}")
    print(f"🔢 State Version: {state['version']}")
    print(f"⏰ Refreshed: {datetime.now().strftime('%H:%M:%S')}")

    # Agent Status
    print("\n" + "─" * 80)
    print("🤖 AGENT STATUS")
    print("─" * 80)

    # HOLLOWED_EYES
    he_status = state['hollowed_eyes']
    status_color = {
        'idle': '⚪',
        'working': '🟢',
        'blocked': '🔴',
        'complete': '✅'
    }
    status_icon = status_color.get(he_status['status'], '❓')

    print(f"\n💻 HOLLOWED_EYES (Development)")
    print(f"   Status: {status_icon} {he_status['status'].upper()}")
    print(f"   Current Task: {he_status['current_task'] or 'None'}")
    print(f"   Last Heartbeat: {get_time_since(he_status['last_heartbeat'])}")
    print(f"   Ready for Review: {'✅' if he_status.get('ready_for_review') else '❌'}")

    # ZHADYZ
    z_status = state['zhadyz']
    status_icon = status_color.get(z_status['status'], '❓')

    print(f"\n🚀 ZHADYZ (DevOps)")
    print(f"   Status: {status_icon} {z_status['status'].upper()}")
    print(f"   Current Task: {z_status['current_task'] or 'None'}")
    print(f"   Last Heartbeat: {get_time_since(z_status['last_heartbeat'])}")
    print(f"   Ready for Review: {'✅' if z_status.get('ready_for_review') else '❌'}")

    # Task Progress
    print("\n" + "─" * 80)
    print("📋 TASK PROGRESS")
    print("─" * 80)

    print(f"\n📊 Overview:")
    print(f"   Total: {stats['total_tasks']}")
    print(f"   ⏸️  Pending: {stats['pending']}")
    print(f"   🟡 In Progress: {stats['in_progress']}")
    print(f"   ✅ Complete: {stats['complete']}")

    if stats['total_tasks'] > 0:
        completion = (stats['complete'] / stats['total_tasks']) * 100
        bar_length = 40
        filled = int(bar_length * completion / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\n   Progress: [{bar}] {completion:.1f}%")

    # Task List
    print("\n📝 Tasks:")
    for task in state['tasks']:
        status_icons = {
            'pending': '⏸️',
            'in_progress': '🟡',
            'complete': '✅'
        }
        icon = status_icons.get(task['status'], '❓')
        owner_icon = '💻' if task['owner'] == 'hollowed_eyes' else '🚀'

        print(f"   {icon} {owner_icon} {task['id']}: {task['title']}")
        if task['status'] == 'in_progress':
            print(f"      └─ 🔄 ACTIVE")

    # Handoffs
    print("\n" + "─" * 80)
    print("🤝 HANDOFFS (Milestone Coordination)")
    print("─" * 80)

    handoffs = [
        ('Milestone 1 Dev', state.get('milestone_1_dev_complete', False)),
        ('Milestone 1 Docs', state.get('milestone_1_docs_complete', False)),
        ('Milestone 2 Dev', state.get('milestone_2_dev_complete', False)),
        ('Milestone 2 Docs', state.get('milestone_2_docs_complete', False)),
        ('Milestone 3 Dev', state.get('milestone_3_dev_complete', False)),
        ('Milestone 3 Docs', state.get('milestone_3_docs_complete', False)),
        ('Portfolio Final', state.get('portfolio_final_complete', False)),
    ]

    for name, status in handoffs:
        icon = '✅' if status else '❌'
        print(f"   {icon} {name}")

    # Messages
    messages = state.get('messages', [])
    if messages:
        print("\n" + "─" * 80)
        print(f"📬 MESSAGES ({len(messages)} total)")
        print("─" * 80)

        # Show last 3 messages
        recent = messages[-3:]
        for msg in recent:
            read_icon = '📭' if msg.get('read') else '📬'
            print(f"\n   {read_icon} From: {msg['from']} → To: {msg['to']}")
            print(f"      Subject: {msg['subject']}")
            print(f"      Time: {msg['timestamp']}")

    # Notes
    if state.get('notes'):
        print("\n" + "─" * 80)
        print("📝 NOTES")
        print("─" * 80)
        print(f"   {state['notes']}")

    # Footer
    print("\n" + "=" * 80)
    print("📡 Coordination: Redis pub/sub (real-time)")
    print("🔄 Autonomous operation: ACTIVE")
    print("⏱️  Refresh rate: 2 seconds")
    print("\nPress Ctrl+C to exit")
    print("=" * 80)


def monitor():
    """Main monitoring loop"""
    print("\n🤖 Starting Multi-Agent Monitor...")
    print("📡 Connecting to Redis...")

    try:
        coordinator = RedisCoordinator()
    except Exception as e:
        print(f"\n❌ ERROR: Could not connect to Redis!")
        print(f"   {str(e)}")
        print("\n🔧 Fix: Start Redis with:")
        print("   docker run -d -p 6379:6379 --name multi-agent-redis redis:latest")
        return

    print("✅ Connected to Redis")
    print("🚀 Starting dashboard...\n")

    time.sleep(2)

    try:
        while True:
            render_dashboard(coordinator)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("🛑 MONITOR STOPPED")
        print("=" * 80)
        print("\nFinal Statistics:")

        stats = coordinator.get_stats()
        print(f"   Total Tasks: {stats['total_tasks']}")
        print(f"   Completed: {stats['complete']}")
        print(f"   Pending: {stats['pending']}")
        print(f"   State Version: {stats['state_version']}")

        print("\n👋 Monitor shutdown complete")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    monitor()
