"""
Memory System - Persistent storage for the assistant
Stores user preferences, conversation history, and important info
"""

import json
from pathlib import Path
from datetime import datetime
import sqlite3


class AssistantMemory:
    """Handles all persistent memory for the assistant"""
    
    def __init__(self, user_name="user"):
        self.user_name = user_name
        self.memory_dir = Path("assistant_memory")
        self.memory_dir.mkdir(exist_ok=True)
        
        # Files
        self.prefs_file = self.memory_dir / "preferences.json"
        self.facts_file = self.memory_dir / "user_facts.json"
        self.db_file = self.memory_dir / "conversations.db"
        
        # Load or create memory
        self.preferences = self.load_preferences()
        self.user_facts = self.load_user_facts()
        self.init_database()
        
        print(f"💾 Memory system initialized for {user_name}")
    
    # ========== PREFERENCES ==========
    
    def load_preferences(self):
        """Load user preferences"""
        if self.prefs_file.exists():
            with open(self.prefs_file, 'r') as f:
                return json.load(f)
        else:
            # Default preferences
            return {
                "name": self.user_name,
                "voice_speed": 0.95,
                "personality": "friendly",
                "favorite_apps": [],
                "work_directory": str(Path.home()),
                "reminders": [],
                "created": datetime.now().isoformat()
            }
    
    def save_preferences(self):
        """Save preferences to file"""
        with open(self.prefs_file, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def update_preference(self, key, value):
        """Update a specific preference"""
        self.preferences[key] = value
        self.save_preferences()
        return f"Updated {key} to {value}"
    
    def get_preference(self, key, default=None):
        """Get a preference value"""
        return self.preferences.get(key, default)
    
    # ========== USER FACTS ==========
    
    def load_user_facts(self):
        """Load stored facts about the user"""
        if self.facts_file.exists():
            with open(self.facts_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "name": self.user_name,
                "facts": [],
                "interests": [],
                "important_dates": {},
                "contacts": {},
                "notes": []
            }
    
    def save_user_facts(self):
        """Save user facts to file"""
        with open(self.facts_file, 'w') as f:
            json.dump(self.user_facts, f, indent=2)
    
    def add_fact(self, category, fact):
        """Add a fact about the user"""
        if category not in self.user_facts:
            self.user_facts[category] = []
        
        # Add with timestamp
        fact_entry = {
            "content": fact,
            "added": datetime.now().isoformat()
        }
        
        if isinstance(self.user_facts[category], list):
            self.user_facts[category].append(fact_entry)
        else:
            self.user_facts[category] = fact
        
        self.save_user_facts()
        return f"Remembered: {fact}"
    
    def get_facts(self, category=None):
        """Get facts about user"""
        if category:
            return self.user_facts.get(category, [])
        return self.user_facts
    
    def search_facts(self, query):
        """Search through stored facts"""
        query_lower = query.lower()
        results = []
        
        for category, items in self.user_facts.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and 'content' in item:
                        if query_lower in item['content'].lower():
                            results.append({
                                'category': category,
                                'content': item['content'],
                                'date': item.get('added', 'unknown')
                            })
        
        return results
    
    # ========== CONVERSATION HISTORY ==========
    
    def init_database(self):
        """Initialize SQLite database for conversation history"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_message TEXT,
                assistant_response TEXT,
                tools_used TEXT,
                session_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                status TEXT,
                created TEXT,
                completed TEXT,
                priority TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_msg, assistant_msg, tools_used=None, session_id=None):
        """Save a conversation turn"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (timestamp, user_message, assistant_response, tools_used, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            user_msg,
            assistant_msg,
            json.dumps(tools_used) if tools_used else None,
            session_id or "default"
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(self, limit=10):
        """Get recent conversation history"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, user_message, assistant_response
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': r[0],
                'user': r[1],
                'assistant': r[2]
            }
            for r in reversed(results)
        ]
    
    def search_conversations(self, query, limit=20):
        """Search through conversation history"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, user_message, assistant_response
            FROM conversations
            WHERE user_message LIKE ? OR assistant_response LIKE ?
            ORDER BY id DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': r[0],
                'user': r[1],
                'assistant': r[2]
            }
            for r in results
        ]
    
    # ========== TASKS & REMINDERS ==========
    
    def add_task(self, task, priority="medium"):
        """Add a task/reminder"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (task, status, created, priority)
            VALUES (?, ?, ?, ?)
        ''', (task, "pending", datetime.now().isoformat(), priority))
        
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        
        return f"Added task #{task_id}: {task}"
    
    def get_tasks(self, status="pending"):
        """Get tasks by status"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        if status == "all":
            cursor.execute('SELECT id, task, status, created, priority FROM tasks ORDER BY id DESC')
        else:
            cursor.execute('''
                SELECT id, task, status, created, priority
                FROM tasks
                WHERE status = ?
                ORDER BY id DESC
            ''', (status,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'task': r[1],
                'status': r[2],
                'created': r[3],
                'priority': r[4]
            }
            for r in results
        ]
    
    def complete_task(self, task_id):
        """Mark task as complete"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks
            SET status = ?, completed = ?
            WHERE id = ?
        ''', ("completed", datetime.now().isoformat(), task_id))
        
        conn.commit()
        conn.close()
        
        return f"Task #{task_id} marked as complete!"
    
    def delete_task(self, task_id):
        """Delete a task"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        
        conn.commit()
        conn.close()
        
        return f"Task #{task_id} deleted"
    
    # ========== CONTEXT BUILDING ==========
    
    def build_context_summary(self):
        """Build a summary of user context for AI"""
        context = []
        
        # User preferences
        name = self.preferences.get('name', 'friend')
        context.append(f"User's name: {name}")
        
        # Recent facts
        interests = self.user_facts.get('interests', [])
        if interests:
            recent_interests = [i['content'] for i in interests[-3:]] if isinstance(interests[0], dict) else interests[-3:]
            context.append(f"Interests: {', '.join(recent_interests)}")
        
        # Pending tasks
        tasks = self.get_tasks("pending")
        if tasks:
            task_list = [f"#{t['id']}: {t['task']}" for t in tasks[:3]]
            context.append(f"Pending tasks: {', '.join(task_list)}")
        
        # Recent conversation topics (last 3)
        recent = self.get_recent_conversations(3)
        if recent:
            topics = [r['user'][:50] for r in recent]
            context.append(f"Recent topics: {', '.join(topics)}")
        
        return "\n".join(context) if context else "No stored context yet"
    
    # ========== UTILITY ==========
    
    def clear_old_conversations(self, days=30):
        """Clear conversations older than X days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM conversations WHERE timestamp < ?', (cutoff_iso,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return f"Cleared {deleted} old conversations"
    
    def export_memory(self, output_file="memory_export.json"):
        """Export all memory to JSON file"""
        export_data = {
            "preferences": self.preferences,
            "user_facts": self.user_facts,
            "recent_conversations": self.get_recent_conversations(50),
            "tasks": self.get_tasks("all"),
            "exported": datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return f"Memory exported to {output_file}"
