"""
MEDICANT_BIAS: Multi-Agent System Setup Script

Runs ONCE to:
1. Backup existing state.json
2. Migrate tasks from state.json to Redis
3. Initialize Redis state
4. Set up coordination infrastructure
5. Terminate (never runs again)

After running this, start the autonomous agents:
- Terminal 1: python agents/hollowed_eyes.py
- Terminal 2: python agents/zhadyz.py
- Terminal 3: python monitor.py
"""

import sys
import io

# Force UTF-8 output encoding (Windows compatibility)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import shutil
from datetime import datetime
from infrastructure.redis_coordinator import RedisCoordinator
from infrastructure.state import create_initial_state


def backup_state_json():
    """Backup existing state.json before migration"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"state.json.backup_{timestamp}"

        shutil.copy('state.json', backup_file)
        print(f"✅ Backed up state.json → {backup_file}")
        return True

    except FileNotFoundError:
        print("⚠️  No state.json found (creating new state)")
        return False


def load_existing_tasks():
    """Load tasks from existing state.json"""
    try:
        with open('state.json', 'r', encoding='utf-8') as f:
            old_state = json.load(f)

        print("✅ Loaded existing state.json")

        # Extract tasks from milestones
        tasks = []

        for milestone in old_state.get('tasks', []):
            for subtask in milestone.get('subtasks', []):
                # Skip already completed tasks (Milestone 1)
                if subtask['status'] == 'complete':
                    print(f"   ℹ️  Skipping completed task: {subtask['id']}")
                    continue

                # Convert to new format
                task = {
                    'id': subtask['id'],
                    'owner': subtask['owner'],
                    'title': subtask['title'],
                    'description': subtask['description'],
                    'status': subtask['status'],
                    'dependencies': subtask.get('dependencies', []),
                    'priority': milestone.get('priority', 1),
                    'acceptance_criteria': subtask.get('acceptance_criteria', []),
                    'files_to_modify': subtask.get('files_to_modify', [])
                }
                tasks.append(task)

                print(f"   ✅ Migrated: {task['id']} - {task['title']}")

        return tasks, old_state

    except FileNotFoundError:
        print("⚠️  No state.json found. Creating fresh project.")
        return [], {}


def migrate_to_redis(coordinator: RedisCoordinator, tasks: list, old_state: dict):
    """Migrate tasks to Redis"""
    # Get initial state
    state = create_initial_state()

    # Preserve project metadata from old state
    if old_state:
        state['project_name'] = old_state.get('project', {}).get('name', 'tactical-rag-improvements')
        state['project_description'] = old_state.get('project', {}).get('description', '')
        state['baseline_commit'] = old_state.get('project', {}).get('baseline_commit', 'e92802d')

        # Preserve completed handoffs
        handoffs = old_state.get('handoffs', {})
        state['milestone_1_dev_complete'] = handoffs.get('milestone_1_dev_complete', True)
        state['milestone_1_docs_complete'] = handoffs.get('milestone_1_docs_complete', True)

    # Add migrated tasks
    state['tasks'] = tasks

    # Save to Redis
    coordinator.update_state(state)

    print(f"\n✅ Migrated {len(tasks)} tasks to Redis")


def print_summary(coordinator: RedisCoordinator):
    """Print setup summary"""
    state = coordinator.get_state()
    stats = coordinator.get_stats()

    print("\n" + "="*70)
    print("🧠 MEDICANT_BIAS: SETUP COMPLETE")
    print("="*70)

    print(f"\n📊 Project: {state['project_name']}")
    print(f"📝 Description: {state['project_description']}")
    print(f"🔗 Baseline Commit: {state['baseline_commit']}")
    print(f"📍 Phase: {state['project_phase']}")

    print(f"\n📋 Tasks Migrated: {stats['total_tasks']}")
    print(f"   ⏸️  Pending: {stats['pending']}")
    print(f"   🟡 In Progress: {stats['in_progress']}")
    print(f"   ✅ Complete: {stats['complete']}")

    print("\n📂 Task Breakdown:")
    hollowed_tasks = [t for t in state['tasks'] if t['owner'] == 'hollowed_eyes']
    zhadyz_tasks = [t for t in state['tasks'] if t['owner'] == 'zhadyz']

    print(f"\n   💻 HOLLOWED_EYES (Development):")
    for task in hollowed_tasks:
        status_icon = "✅" if task['status'] == 'complete' else "🟡" if task['status'] == 'in_progress' else "⏸️"
        print(f"      {status_icon} {task['id']}: {task['title']}")

    print(f"\n   🚀 ZHADYZ (DevOps):")
    for task in zhadyz_tasks:
        status_icon = "✅" if task['status'] == 'complete' else "🟡" if task['status'] == 'in_progress' else "⏸️"
        print(f"      {status_icon} {task['id']}: {task['title']}")

    print("\n🤝 Handoffs:")
    print(f"   Milestone 1 Dev: {'✅' if state['milestone_1_dev_complete'] else '❌'}")
    print(f"   Milestone 1 Docs: {'✅' if state['milestone_1_docs_complete'] else '❌'}")
    print(f"   Milestone 2 Dev: {'✅' if state['milestone_2_dev_complete'] else '❌'}")
    print(f"   Milestone 2 Docs: {'✅' if state['milestone_2_docs_complete'] else '❌'}")

    print("\n" + "="*70)
    print("🚀 NEXT STEPS")
    print("="*70)
    print("\n1. Start Redis (if not running):")
    print("   docker run -d -p 6379:6379 --name multi-agent-redis redis:latest")
    print("\n2. Start HOLLOWED_EYES agent:")
    print("   python agents/hollowed_eyes.py")
    print("\n3. Start ZHADYZ agent:")
    print("   python agents/zhadyz.py")
    print("\n4. Monitor in real-time:")
    print("   python monitor.py")

    print("\n📡 Coordination: Redis pub/sub (real-time, millisecond latency)")
    print("🔄 Agents: Autonomous event-driven operation")
    print("🎯 Goal: Complete remaining milestones 2-4")

    print("\n" + "="*70)
    print("🧠 MEDICANT_BIAS: TERMINATING")
    print("="*70)
    print("\nMy work is done. Agents are now autonomous.")
    print("They will coordinate via Redis pub/sub without human intervention.")
    print("\nGood luck, HOLLOWED_EYES and ZHADYZ! 🚀")
    print("="*70 + "\n")


def main():
    """Main setup function"""
    print("\n" + "="*70)
    print("🧠 MEDICANT_BIAS: MULTI-AGENT SYSTEM SETUP")
    print("="*70)
    print("\nInitializing production-grade multi-agent infrastructure...")
    print("Framework: LangGraph + Redis pub/sub")
    print("Agents: HOLLOWED_EYES (dev) + ZHADYZ (devops)")
    print("="*70 + "\n")

    # Step 1: Backup existing state
    print("📦 Step 1: Backing up existing state...")
    backup_state_json()

    # Step 2: Load existing tasks
    print("\n📥 Step 2: Loading existing tasks from state.json...")
    tasks, old_state = load_existing_tasks()

    # Step 3: Initialize Redis
    print("\n🔧 Step 3: Initializing Redis coordinator...")
    try:
        coordinator = RedisCoordinator()
    except Exception as e:
        print(f"\n❌ ERROR: Could not connect to Redis!")
        print(f"   {str(e)}")
        print("\n🔧 Fix: Start Redis with:")
        print("   docker run -d -p 6379:6379 --name multi-agent-redis redis:latest")
        return

    # Step 4: Migrate to Redis
    print("\n🔄 Step 4: Migrating tasks to Redis...")
    migrate_to_redis(coordinator, tasks, old_state)

    # Step 5: Print summary
    print_summary(coordinator)


if __name__ == "__main__":
    main()
