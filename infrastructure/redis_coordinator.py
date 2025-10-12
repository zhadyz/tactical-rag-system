"""
Redis Pub/Sub Coordinator
Real-time event-driven agent coordination for autonomous operation

Replaces file-based state.json polling with millisecond-latency pub/sub
"""

import redis
import json
import time
from typing import Callable, Optional, List, Dict
from datetime import datetime
from infrastructure.state import MultiAgentState, create_initial_state


class RedisCoordinator:
    """
    Redis-based real-time coordination for autonomous agents.

    Features:
    - Pub/sub for instant event notification (no polling!)
    - State persistence in Redis
    - Agent heartbeat monitoring
    - Task queue with priorities
    - Handoff management
    - Agent-to-agent messaging

    Production patterns used by Netflix, Twitter, etc.
    """

    def __init__(self, host='localhost', port=6379, db=0):
        """
        Initialize Redis coordinator.

        Args:
            host: Redis host (default: localhost)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()

        # Test connection
        try:
            self.redis_client.ping()
            print("[OK] Redis connected successfully")
        except redis.ConnectionError as e:
            print("[ERROR] Redis not running!")
            print("   Start Redis with: docker run -d -p 6379:6379 redis:latest")
            raise

    # ===== STATE MANAGEMENT =====

    def get_state(self) -> Dict:
        """
        Get current state from Redis.

        Returns:
            Current multi-agent state dictionary
        """
        state_json = self.redis_client.get('agent_state')
        if state_json:
            return json.loads(state_json)

        # Create initial state if doesn't exist
        print("[WARN]  No state found. Creating initial state...")
        initial = create_initial_state()
        self.redis_client.set('agent_state', json.dumps(initial, indent=2))
        return initial

    def update_state(self, state: Dict):
        """
        Update state in Redis and notify all agents.

        Args:
            state: Updated state dictionary
        """
        state['version'] = state.get('version', 0) + 1
        self.redis_client.set('agent_state', json.dumps(state, indent=2))

        # Publish state change event (agents react instantly)
        self.publish_event('state_changed', {
            'version': state['version'],
            'timestamp': datetime.now().isoformat()
        })

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        current_task: str = "",
        ready_for_review: bool = False
    ):
        """
        Quick agent status update with heartbeat.

        Args:
            agent_id: Agent identifier (hollowed_eyes or zhadyz)
            status: Agent status (idle, working, blocked, complete)
            current_task: Current task ID
            ready_for_review: Flag for handoff readiness
        """
        state = self.get_state()
        state[agent_id]['status'] = status
        state[agent_id]['current_task'] = current_task
        state[agent_id]['last_heartbeat'] = datetime.now().isoformat()
        state[agent_id]['ready_for_review'] = ready_for_review
        self.update_state(state)

    # ===== TASK MANAGEMENT =====

    def get_pending_tasks(self, agent_id: str) -> List[Dict]:
        """
        Get pending tasks for specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of pending tasks assigned to agent
        """
        state = self.get_state()
        return [
            task for task in state['tasks']
            if task['owner'] == agent_id and task['status'] == 'pending'
        ]

    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Get specific task by ID"""
        state = self.get_state()
        for task in state['tasks']:
            if task['id'] == task_id:
                return task
        return None

    def mark_task_in_progress(self, task_id: str):
        """
        Mark task as in progress.

        Args:
            task_id: Task identifier
        """
        state = self.get_state()
        for task in state['tasks']:
            if task['id'] == task_id:
                task['status'] = 'in_progress'
                break
        self.update_state(state)

        # Notify other agents
        self.publish_event('task_started', {'task_id': task_id})

    def mark_task_complete(self, task_id: str):
        """
        Mark task as complete and notify all agents.

        Args:
            task_id: Task identifier
        """
        state = self.get_state()
        for task in state['tasks']:
            if task['id'] == task_id:
                task['status'] = 'complete'
                break
        self.update_state(state)

        # Notify other agents (unblocks dependent tasks)
        self.publish_event('task_completed', {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat()
        })

    def check_dependencies_met(self, task: Dict) -> bool:
        """
        Check if all task dependencies are complete.

        Args:
            task: Task dictionary

        Returns:
            True if all dependencies met, False otherwise
        """
        if not task.get('dependencies'):
            return True

        state = self.get_state()
        for dep_id in task['dependencies']:
            dep_task = next(
                (t for t in state['tasks'] if t['id'] == dep_id),
                None
            )
            if not dep_task or dep_task['status'] != 'complete':
                return False

        return True

    # ===== PUB/SUB EVENTS =====

    def publish_event(self, event_type: str, data: Dict):
        """
        Publish event to all agents via Redis pub/sub.

        Agents react within milliseconds (no polling delay).

        Args:
            event_type: Event type identifier
            data: Event payload
        """
        message = {
            'event': event_type,
            'data': data,
            'timestamp': time.time()
        }
        self.redis_client.publish('agent_events', json.dumps(message))

    def subscribe_to_events(self, callback: Callable):
        """
        Subscribe to agent events and call callback for each.

        This blocks and runs in the agent's main loop.
        Agents receive events instantly via Redis pub/sub.

        Args:
            callback: Function to call for each event
        """
        self.pubsub.subscribe('agent_events')
        print("[OK] Subscribed to agent events (real-time pub/sub active)...")

        for message in self.pubsub.listen():
            if message['type'] == 'message':
                event = json.loads(message['data'])
                callback(event)

    # ===== HANDOFFS =====

    def set_handoff(self, handoff_key: str, value: bool):
        """
        Set handoff flag and notify agents.

        Args:
            handoff_key: Handoff identifier (e.g., milestone_1_dev_complete)
            value: Handoff state
        """
        state = self.get_state()
        state[handoff_key] = value
        self.update_state(state)

        # Notify agents of handoff (triggers downstream work)
        self.publish_event('handoff', {
            'key': handoff_key,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })

    def check_handoff(self, handoff_key: str) -> bool:
        """
        Check if handoff is ready.

        Args:
            handoff_key: Handoff identifier

        Returns:
            Handoff state
        """
        state = self.get_state()
        return state.get(handoff_key, False)

    # ===== MESSAGES =====

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        subject: str,
        body: str
    ):
        """
        Send message from one agent to another.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            subject: Message subject
            body: Message body
        """
        state = self.get_state()
        message = {
            'from': from_agent,
            'to': to_agent,
            'subject': subject,
            'body': body,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        state['messages'].append(message)
        self.update_state(state)

        # Notify recipient instantly
        self.publish_event('new_message', {
            'to': to_agent,
            'from': from_agent,
            'subject': subject
        })

    def get_messages(self, agent_id: str, unread_only: bool = False) -> List[Dict]:
        """
        Get messages for agent.

        Args:
            agent_id: Agent identifier
            unread_only: Return only unread messages

        Returns:
            List of messages
        """
        state = self.get_state()
        messages = [msg for msg in state['messages'] if msg['to'] == agent_id]

        if unread_only:
            messages = [msg for msg in messages if not msg.get('read', False)]

        return messages

    def mark_message_read(self, message_index: int):
        """Mark message as read"""
        state = self.get_state()
        if message_index < len(state['messages']):
            state['messages'][message_index]['read'] = True
            self.update_state(state)

    # ===== HEARTBEAT =====

    def send_heartbeat(self, agent_id: str):
        """
        Send agent heartbeat.

        Args:
            agent_id: Agent identifier
        """
        state = self.get_state()
        if agent_id in state:
            state[agent_id]['last_heartbeat'] = datetime.now().isoformat()
            # Don't trigger full state update for just heartbeat
            self.redis_client.set('agent_state', json.dumps(state, indent=2))

    def get_agent_heartbeats(self) -> Dict:
        """
        Get all agent heartbeats.

        Returns:
            Dictionary of agent heartbeat timestamps
        """
        state = self.get_state()
        return {
            'hollowed_eyes': state['hollowed_eyes']['last_heartbeat'],
            'zhadyz': state['zhadyz']['last_heartbeat']
        }

    # ===== UTILITIES =====

    def cleanup(self):
        """
        Clear all Redis data (for testing/reset).

        WARNING: Destroys all state!
        """
        self.redis_client.flushdb()
        print("[CLEAN] Redis cleaned (all state destroyed)")

    def backup_state(self, filename: str = "state_backup.json"):
        """
        Backup current state to file.

        Args:
            filename: Backup file path
        """
        state = self.get_state()
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"[SAVE] State backed up to {filename}")

    def restore_state(self, filename: str = "state_backup.json"):
        """
        Restore state from file.

        Args:
            filename: Backup file path
        """
        with open(filename, 'r') as f:
            state = json.load(f)
        self.redis_client.set('agent_state', json.dumps(state, indent=2))
        print(f"[RESTORE] State restored from {filename}")

    def get_stats(self) -> Dict:
        """
        Get coordination statistics.

        Returns:
            Statistics dictionary
        """
        state = self.get_state()
        tasks = state['tasks']

        return {
            'total_tasks': len(tasks),
            'pending': len([t for t in tasks if t['status'] == 'pending']),
            'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
            'complete': len([t for t in tasks if t['status'] == 'complete']),
            'state_version': state['version'],
            'project_phase': state['project_phase'],
            'agents': {
                'hollowed_eyes': state['hollowed_eyes']['status'],
                'zhadyz': state['zhadyz']['status']
            }
        }
