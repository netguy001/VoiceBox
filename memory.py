# -*- coding: utf-8 -*-
"""
Memory System - OPTIMIZED VERSION
Persistent storage for the assistant - Fast and efficient
"""

import json
from pathlib import Path
from datetime import datetime
import sqlite3


class AssistantMemory:
    """Handles all persistent memory for the assistant"""

    def __init__(self, user_name="friend"):
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

        print(f"💾 Memory system ready for {user_name}")

    # ========== PREFERENCES ==========

    def load_preferences(self):
        """Load user preferences"""
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        return {
            "name": self.user_name,
            "voice_speed": 0.95,
            "personality": "friendly",
            "favorite_apps": [],
            "work_directory": str(Path.home()),
            "reminders": [],
            "created": datetime.now().isoformat(),
        }

    def save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.prefs_file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save preferences: {e}")

    def update_preference(self, key, value):
        """Update a specific preference"""
        self.preferences[key] = value
        self.save_preferences()
        return f"✅ Updated {key}"

    def get_preference(self, key, default=None):
        """Get a preference value"""
        return self.preferences.get(key, default)

    # ========== USER FACTS ==========

    def load_user_facts(self):
        """Load stored facts about the user"""
        if self.facts_file.exists():
            try:
                with open(self.facts_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        return {
            "name": self.user_name,
            "facts": [],
            "interests": [],
            "important_dates": {},
            "contacts": {},
            "notes": [],
        }

    def save_user_facts(self):
        """Save user facts to file"""
        try:
            with open(self.facts_file, "w", encoding="utf-8") as f:
                json.dump(self.user_facts, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save facts: {e}")

    def add_fact(self, category, fact):
        """Add a fact about the user"""
        if category not in self.user_facts:
            self.user_facts[category] = []

        fact_entry = {"content": fact, "added": datetime.now().isoformat()}

        if isinstance(self.user_facts[category], list):
            self.user_facts[category].append(fact_entry)
        else:
            self.user_facts[category] = fact

        self.save_user_facts()
        return f"✅ Remembered: {fact}"

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
                    if isinstance(item, dict) and "content" in item:
                        if query_lower in item["content"].lower():
                            results.append(
                                {
                                    "category": category,
                                    "content": item["content"],
                                    "date": item.get("added", "unknown"),
                                }
                            )

        return results

    # ========== CONVERSATION HISTORY ==========

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                tools_used TEXT,
                session_id TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON conversations(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_session 
            ON conversations(session_id)
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                created TEXT NOT NULL,
                completed TEXT,
                priority TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_task_status 
            ON tasks(status)
        """
        )

        conn.commit()
        conn.close()

    def save_conversation(
        self, user_msg, assistant_msg, tools_used=None, session_id=None
    ):
        """Save a conversation turn"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO conversations (timestamp, user_message, assistant_response, tools_used, session_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    user_msg[:500],
                    assistant_msg[:1000],
                    json.dumps(tools_used) if tools_used else None,
                    session_id or "default",
                ),
            )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️  Could not save conversation: {e}")

    def get_recent_conversations(self, limit=5):
        """Get recent conversation history"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT timestamp, user_message, assistant_response
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = cursor.fetchall()
            conn.close()

            return [
                {
                    "timestamp": r[0],
                    "user": r[1],
                    "assistant": r[2][:200],
                }
                for r in reversed(results)
            ]
        except Exception as e:
            print(f"⚠️  Could not get conversations: {e}")
            return []

    def search_conversations(self, query, limit=10):
        """Search through conversation history"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT timestamp, user_message, assistant_response
                FROM conversations
                WHERE user_message LIKE ? OR assistant_response LIKE ?
                ORDER BY id DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            results = cursor.fetchall()
            conn.close()

            return [
                {"timestamp": r[0], "user": r[1][:100], "assistant": r[2][:100]}
                for r in results
            ]
        except Exception as e:
            print(f"⚠️  Could not search conversations: {e}")
            return []

    # ========== TASKS & REMINDERS ==========

    def add_task(self, task, priority="medium"):
        """Add a task/reminder"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO tasks (task, status, created, priority)
                VALUES (?, ?, ?, ?)
            """,
                (task, "pending", datetime.now().isoformat(), priority),
            )

            conn.commit()
            task_id = cursor.lastrowid
            conn.close()

            return f"✅ Added task #{task_id}: {task}"
        except Exception as e:
            return f"❌ Could not add task: {e}"

    def get_tasks(self, status="pending"):
        """Get tasks by status"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            if status == "all":
                cursor.execute(
                    """
                    SELECT id, task, status, created, priority 
                    FROM tasks 
                    ORDER BY id DESC 
                    LIMIT 50
                """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, task, status, created, priority
                    FROM tasks
                    WHERE status = ?
                    ORDER BY id DESC
                    LIMIT 50
                """,
                    (status,),
                )

            results = cursor.fetchall()
            conn.close()

            return [
                {
                    "id": r[0],
                    "task": r[1],
                    "status": r[2],
                    "created": r[3],
                    "priority": r[4],
                }
                for r in results
            ]
        except Exception as e:
            print(f"⚠️  Could not get tasks: {e}")
            return []

    def complete_task(self, task_id):
        """Mark task as complete"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE tasks
                SET status = ?, completed = ?
                WHERE id = ?
            """,
                ("completed", datetime.now().isoformat(), task_id),
            )

            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()

            if rows_affected > 0:
                return f"✅ Task #{task_id} completed!"
            else:
                return f"❌ Task #{task_id} not found"
        except Exception as e:
            return f"❌ Could not complete task: {e}"

    def delete_task(self, task_id):
        """Delete a task"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()

            if rows_affected > 0:
                return f"✅ Task #{task_id} deleted"
            else:
                return f"❌ Task #{task_id} not found"
        except Exception as e:
            return f"❌ Could not delete task: {e}"

    # ========== CONTEXT BUILDING ==========

    def build_context_summary(self):
        """Build context summary - SHORT"""
        context = []

        name = self.preferences.get("name", "friend")
        context.append(f"User: {name}")

        tasks = self.get_tasks("pending")
        if tasks:
            urgent_tasks = [t for t in tasks if t.get("priority") == "high"]
            if urgent_tasks:
                context.append(f"Urgent task: {urgent_tasks[0]['task'][:40]}")
            elif len(tasks) <= 3:
                task_list = ", ".join([t["task"][:30] for t in tasks[:2]])
                context.append(f"Tasks: {task_list}")

        interests = self.user_facts.get("interests", [])
        if interests and len(interests) > 0:
            recent = interests[-2:] if len(interests) >= 2 else interests
            if isinstance(recent[0], dict):
                interest_str = ", ".join([i["content"][:20] for i in recent])
            else:
                interest_str = ", ".join([str(i)[:20] for i in recent])
            context.append(f"Interests: {interest_str}")

        if context:
            return " | ".join(context)
        else:
            return "New user"

    # ========== UTILITY ==========

    def clear_old_conversations(self, days=30):
        """Clear conversations older than X days"""
        try:
            cutoff = datetime.now().timestamp() - (days * 24 * 3600)
            cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM conversations WHERE timestamp < ?", (cutoff_iso,)
            )
            deleted = cursor.rowcount

            conn.commit()
            conn.close()

            return f"✅ Cleared {deleted} old conversations"
        except Exception as e:
            return f"❌ Could not clear conversations: {e}"

    def get_stats(self):
        """Get memory statistics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_convos = cursor.fetchone()[0]

            cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            task_stats = dict(cursor.fetchall())

            conn.close()

            stats = [
                f"📊 Memory Statistics:",
                f"   💬 Conversations: {total_convos}",
                f"   📋 Pending tasks: {task_stats.get('pending', 0)}",
                f"   ✅ Completed tasks: {task_stats.get('completed', 0)}",
                f"   🧠 Stored facts: {len(self.user_facts.get('facts', []))}",
            ]

            return "\n".join(stats)
        except Exception as e:
            return f"❌ Could not get stats: {e}"
