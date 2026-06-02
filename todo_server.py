"""
TODO MCP Server - A simple task tracker using FastMCP

This server exposes tools, resources, and prompts for managing TODO items.
"""

import json
import os
from datetime import datetime
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("TodoManager")

# File path for persistent storage (configurable via environment variable)
DATA_FILE = os.environ.get("TODO_DATA_FILE", "todos.json")

# In-memory storage for tasks
tasks: list[dict] = []
task_id_counter: int = 1


def load_tasks() -> None:
    """Load tasks from the JSON file."""
    global tasks, task_id_counter

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                tasks = data.get("todos", [])
                task_id_counter = data.get("next_id", 1)
        except (json.JSONDecodeError, IOError):
            tasks = []
            task_id_counter = 1


def save_tasks() -> None:
    """Save tasks to the JSON file."""
    data = {
        "todos": tasks,
        "next_id": task_id_counter
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Load tasks on startup
load_tasks()


# ============== TOOLS ==============

VALID_PRIORITIES = ["high", "medium", "low"]


@mcp.tool()
def add_todo(title: str, description: str = "", priority: str = "medium", deadline: str = None) -> dict:
    """
    Add a new task to the TODO list.

    Args:
        title: The title of the task
        description: Optional detailed description of the task
        priority: Task priority level ('high', 'medium', or 'low'). Defaults to 'medium'
        deadline: Optional deadline in ISO format (e.g., '2026-06-15' or '2026-06-15T14:00:00')

    Returns:
        The created task object
    """
    global task_id_counter

    if priority not in VALID_PRIORITIES:
        return {"error": f"Invalid priority '{priority}'. Must be one of: {VALID_PRIORITIES}"}

    task = {
        "id": task_id_counter,
        "title": title,
        "description": description,
        "priority": priority,
        "deadline": deadline,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }

    tasks.append(task)
    task_id_counter += 1
    save_tasks()

    return {"message": f"Task '{title}' added successfully", "task": task}


@mcp.tool()
def complete_task(task_id: int) -> dict:
    """
    Mark a task as completed.

    Args:
        task_id: The ID of the task to complete

    Returns:
        The updated task object or error message
    """
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            save_tasks()
            return {"message": f"Task {task_id} marked as completed", "task": task}

    return {"error": f"Task with ID {task_id} not found"}


@mcp.tool()
def delete_task(task_id: int) -> dict:
    """
    Delete a task from the TODO list.

    Args:
        task_id: The ID of the task to delete

    Returns:
        Success or error message
    """
    global tasks

    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            deleted_task = tasks.pop(i)
            save_tasks()
            return {"message": f"Task '{deleted_task['title']}' deleted successfully"}

    return {"error": f"Task with ID {task_id} not found"}


@mcp.tool()
def update_task(task_id: int, title: str = None, description: str = None, priority: str = None, deadline: str = None) -> dict:
    """
    Update an existing task's title, description, priority, or deadline.

    Args:
        task_id: The ID of the task to update
        title: New title (optional)
        description: New description (optional)
        priority: New priority level - 'high', 'medium', or 'low' (optional)
        deadline: New deadline in ISO format (optional)

    Returns:
        The updated task object or error message
    """
    if priority is not None and priority not in VALID_PRIORITIES:
        return {"error": f"Invalid priority '{priority}'. Must be one of: {VALID_PRIORITIES}"}

    for task in tasks:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if description is not None:
                task["description"] = description
            if priority is not None:
                task["priority"] = priority
            if deadline is not None:
                task["deadline"] = deadline
            save_tasks()
            return {"message": f"Task {task_id} updated successfully", "task": task}

    return {"error": f"Task with ID {task_id} not found"}


@mcp.tool()
def list_tasks(status: str = None, priority: str = None) -> dict:
    """
    List all tasks, optionally filtered by status and/or priority.

    Args:
        status: Filter by status ('pending', 'completed', or None for all)
        priority: Filter by priority ('high', 'medium', 'low', or None for all)

    Returns:
        List of tasks matching the filter
    """
    filtered_tasks = tasks

    if status:
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.get("priority") == priority]

    return {
        "total": len(filtered_tasks),
        "tasks": filtered_tasks
    }


# ============== RESOURCES ==============

def _format_priority(priority: str) -> str:
    """Format priority with visual indicator."""
    icons = {"high": "[!!!]", "medium": "[!!]", "low": "[!]"}
    return icons.get(priority, "[?]")


@mcp.resource("tasks://all")
def get_all_tasks() -> str:
    """
    Get a formatted list of all tasks.
    """
    if not tasks:
        return "No tasks found."

    lines = ["=== All Tasks ===\n"]
    for task in tasks:
        status_icon = "[x]" if task["status"] == "completed" else "[ ]"
        priority = task.get("priority", "medium")
        priority_icon = _format_priority(priority)
        lines.append(f"{status_icon} {priority_icon} {task['id']}: {task['title']}")
        if task["description"]:
            lines.append(f"    Description: {task['description']}")
        lines.append(f"    Priority: {priority.upper()}")
        if task.get("deadline"):
            lines.append(f"    Deadline: {task['deadline']}")
        lines.append(f"    Created: {task['created_at']}")
        if task["completed_at"]:
            lines.append(f"    Completed: {task['completed_at']}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("tasks://pending")
def get_pending_tasks() -> str:
    """
    Get a formatted list of pending (incomplete) tasks, sorted by priority.
    """
    pending = [t for t in tasks if t["status"] == "pending"]

    if not pending:
        return "No pending tasks. You're all caught up!"

    # Sort by priority (high first, then medium, then low)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    pending.sort(key=lambda t: priority_order.get(t.get("priority", "medium"), 1))

    lines = ["=== Pending Tasks ===\n"]
    for task in pending:
        priority = task.get("priority", "medium")
        priority_icon = _format_priority(priority)
        lines.append(f"[ ] {priority_icon} {task['id']}: {task['title']}")
        if task["description"]:
            lines.append(f"    Description: {task['description']}")
        lines.append(f"    Priority: {priority.upper()}")
        if task.get("deadline"):
            lines.append(f"    Deadline: {task['deadline']}")
        lines.append(f"    Created: {task['created_at']}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("tasks://completed")
def get_completed_tasks() -> str:
    """
    Get a formatted list of completed tasks.
    """
    completed = [t for t in tasks if t["status"] == "completed"]

    if not completed:
        return "No completed tasks yet."

    lines = ["=== Completed Tasks ===\n"]
    for task in completed:
        priority = task.get("priority", "medium")
        priority_icon = _format_priority(priority)
        lines.append(f"[x] {priority_icon} {task['id']}: {task['title']}")
        if task["description"]:
            lines.append(f"    Description: {task['description']}")
        lines.append(f"    Priority: {priority.upper()}")
        lines.append(f"    Completed: {task['completed_at']}")
        lines.append("")

    return "\n".join(lines)


# ============== PROMPTS ==============

@mcp.prompt()
def task_summary() -> str:
    """
    Generate a purely statistical summary of task metrics.
    Focuses on counts, completion rates, aging analysis, and priority distribution.
    """
    from datetime import datetime

    total = len(tasks)
    pending_tasks = [t for t in tasks if t["status"] == "pending"]
    completed_tasks = [t for t in tasks if t["status"] == "completed"]
    pending = len(pending_tasks)
    completed = len(completed_tasks)

    # Completion rate
    completion_rate = (completed / total * 100) if total > 0 else 0

    # Priority distribution (pending only)
    high_priority = len([t for t in pending_tasks if t.get("priority") == "high"])
    medium_priority = len([t for t in pending_tasks if t.get("priority") == "medium"])
    low_priority = len([t for t in pending_tasks if t.get("priority") == "low"])

    # Aging analysis
    now = datetime.now()
    aging_info = []
    for task in pending_tasks:
        created = datetime.fromisoformat(task["created_at"])
        age_days = (now - created).days
        aging_info.append({"id": task["id"], "title": task["title"], "age_days": age_days})

    # Sort by age (oldest first)
    aging_info.sort(key=lambda x: x["age_days"], reverse=True)

    oldest_tasks = ""
    if aging_info:
        oldest_tasks = "\n".join([f"  - Task #{t['id']} '{t['title']}': {t['age_days']} days old" for t in aging_info[:5]])
    else:
        oldest_tasks = "  No pending tasks"

    # Overdue tasks (tasks past deadline)
    overdue_tasks = []
    for task in pending_tasks:
        if task.get("deadline"):
            try:
                deadline = datetime.fromisoformat(task["deadline"].split("T")[0])
                if deadline < now:
                    days_overdue = (now - deadline).days
                    overdue_tasks.append({"id": task["id"], "title": task["title"], "days_overdue": days_overdue})
            except ValueError:
                pass

    overdue_info = ""
    if overdue_tasks:
        overdue_info = f"\nOVERDUE TASKS ({len(overdue_tasks)}):\n" + "\n".join(
            [f"  - Task #{t['id']} '{t['title']}': {t['days_overdue']} days overdue" for t in overdue_tasks]
        )

    return f"""Provide a statistical analysis of my TODO list based on these metrics:

=== TASK COUNTS ===
Total tasks: {total}
Pending tasks: {pending}
Completed tasks: {completed}
Completion rate: {completion_rate:.1f}%

=== PRIORITY DISTRIBUTION (Pending) ===
High priority: {high_priority}
Medium priority: {medium_priority}
Low priority: {low_priority}

=== AGING ANALYSIS (Oldest Pending Tasks) ===
{oldest_tasks}
{overdue_info}

Present these statistics clearly. Calculate averages if helpful. Identify any concerning trends (e.g., low completion rate, many old tasks, overdue items)."""


@mcp.prompt()
def daily_planning() -> str:
    """
    Generate a prompt for daily task planning.
    """
    pending = [t for t in tasks if t["status"] == "pending"]

    task_list = "\n".join([f"- {t['title']}: {t['description']}" for t in pending]) if pending else "No pending tasks"

    return f"""Help me plan my day based on these pending tasks:

{task_list}

Please suggest:
1. Which tasks to prioritize
2. Estimated time for each task
3. Any tasks that could be delegated or deferred"""


@mcp.prompt()
def task_review_workflow(focus_priority: str = "high") -> str:
    """
    Action-oriented task review workflow for batch operations and deadline enforcement.
    Filters by priority and identifies actionable items requiring immediate attention.
    """
    from datetime import datetime

    now = datetime.now()
    pending_tasks = [t for t in tasks if t["status"] == "pending"]

    # Filter by priority
    priority_tasks = [t for t in pending_tasks if t.get("priority") == focus_priority]

    # Identify overdue tasks
    overdue_tasks = []
    for task in pending_tasks:
        if task.get("deadline"):
            try:
                deadline = datetime.fromisoformat(task["deadline"].split("T")[0])
                if deadline < now:
                    days_overdue = (now - deadline).days
                    overdue_tasks.append({
                        "id": task["id"],
                        "title": task["title"],
                        "priority": task.get("priority", "medium"),
                        "days_overdue": days_overdue
                    })
            except ValueError:
                pass

    # Identify tasks approaching deadline (within 3 days)
    approaching_deadline = []
    for task in pending_tasks:
        if task.get("deadline"):
            try:
                deadline = datetime.fromisoformat(task["deadline"].split("T")[0])
                days_until = (deadline - now).days
                if 0 <= days_until <= 3:
                    approaching_deadline.append({
                        "id": task["id"],
                        "title": task["title"],
                        "priority": task.get("priority", "medium"),
                        "days_until": days_until
                    })
            except ValueError:
                pass

    # Build task lists for prompt
    priority_list = "\n".join([
        f"  - [{t['id']}] {t['title']} (deadline: {t.get('deadline', 'none')})"
        for t in priority_tasks
    ]) if priority_tasks else "  No tasks at this priority level"

    overdue_list = "\n".join([
        f"  - [{t['id']}] {t['title']} ({t['priority'].upper()}) - {t['days_overdue']} days overdue"
        for t in overdue_tasks
    ]) if overdue_tasks else "  No overdue tasks"

    approaching_list = "\n".join([
        f"  - [{t['id']}] {t['title']} ({t['priority'].upper()}) - {t['days_until']} days remaining"
        for t in approaching_deadline
    ]) if approaching_deadline else "  No tasks approaching deadline"

    # All pending task IDs for batch operations
    all_pending_ids = [t["id"] for t in pending_tasks]
    priority_task_ids = [t["id"] for t in priority_tasks]

    return f"""You are a task operations manager executing a review workflow.

=== FOCUS: {focus_priority.upper()} PRIORITY TASKS ===
{priority_list}

=== DEADLINE ENFORCEMENT ===
OVERDUE (Requires immediate action):
{overdue_list}

APPROACHING DEADLINE (Within 3 days):
{approaching_list}

=== AVAILABLE BATCH OPERATIONS ===
You can perform these operations using the available tools:

1. COMPLETE TASKS: Use complete_task(task_id) for each task
   - Priority task IDs: {priority_task_ids}
   - All pending IDs: {all_pending_ids}

2. UPDATE PRIORITY: Use update_task(task_id, priority="high|medium|low")
   - Escalate overdue tasks to high priority
   - Adjust priorities based on urgency

3. SET/UPDATE DEADLINES: Use update_task(task_id, deadline="YYYY-MM-DD")
   - Add deadlines to tasks without them
   - Extend deadlines if needed

4. DELETE TASKS: Use delete_task(task_id)
   - Remove obsolete or duplicate tasks

=== WORKFLOW INSTRUCTIONS ===
1. List all {focus_priority.upper()} priority tasks with their status
2. Flag any overdue tasks and recommend priority escalation
3. Identify tasks approaching deadline that need attention
4. Propose specific batch operations (with exact task IDs)
5. Wait for user confirmation before executing any changes
6. Execute approved operations and report results

Always ask for explicit user confirmation before making any changes."""


if __name__ == "__main__":
    # Run the server using stdio transport (for Claude Code integration)
    mcp.run()
