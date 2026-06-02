"""
TODO MCP Server - A simple task tracker using FastMCP

Based on the Machine Learning Mastery tutorial for building MCP servers.
This server exposes tools, resources, and prompts for managing TODO items.
"""

import json
import os
from datetime import datetime
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("TodoManager")

# File path for persistent storage
DATA_FILE = "/Users/cajieh/Documents/projects/todos.json"

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

@mcp.tool()
def add_todo(title: str, description: str = "") -> dict:
    """
    Add a new task to the TODO list.

    Args:
        title: The title of the task
        description: Optional detailed description of the task

    Returns:
        The created task object
    """
    global task_id_counter

    task = {
        "id": task_id_counter,
        "title": title,
        "description": description,
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
def update_task(task_id: int, title: str = None, description: str = None) -> dict:
    """
    Update an existing task's title or description.

    Args:
        task_id: The ID of the task to update
        title: New title (optional)
        description: New description (optional)

    Returns:
        The updated task object or error message
    """
    for task in tasks:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if description is not None:
                task["description"] = description
            save_tasks()
            return {"message": f"Task {task_id} updated successfully", "task": task}

    return {"error": f"Task with ID {task_id} not found"}


@mcp.tool()
def list_tasks(status: str = None) -> dict:
    """
    List all tasks, optionally filtered by status.

    Args:
        status: Filter by status ('pending', 'completed', or None for all)

    Returns:
        List of tasks matching the filter
    """
    if status:
        filtered_tasks = [t for t in tasks if t["status"] == status]
    else:
        filtered_tasks = tasks

    return {
        "total": len(filtered_tasks),
        "tasks": filtered_tasks
    }


# ============== RESOURCES ==============

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
        lines.append(f"{status_icon} {task['id']}: {task['title']}")
        if task["description"]:
            lines.append(f"    Description: {task['description']}")
        lines.append(f"    Created: {task['created_at']}")
        if task["completed_at"]:
            lines.append(f"    Completed: {task['completed_at']}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("tasks://pending")
def get_pending_tasks() -> str:
    """
    Get a formatted list of pending (incomplete) tasks.
    """
    pending = [t for t in tasks if t["status"] == "pending"]

    if not pending:
        return "No pending tasks. You're all caught up!"

    lines = ["=== Pending Tasks ===\n"]
    for task in pending:
        lines.append(f"[ ] {task['id']}: {task['title']}")
        if task["description"]:
            lines.append(f"    Description: {task['description']}")
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
        lines.append(f"[x] {task['id']}: {task['title']}")
        if task["description"]:
            lines.append(f"    Description: {task['description']}")
        lines.append(f"    Completed: {task['completed_at']}")
        lines.append("")

    return "\n".join(lines)


# ============== PROMPTS ==============

@mcp.prompt()
def task_summary() -> str:
    """
    Generate a prompt for summarizing the current task status.
    """
    total = len(tasks)
    pending = len([t for t in tasks if t["status"] == "pending"])
    completed = len([t for t in tasks if t["status"] == "completed"])

    return f"""Please provide a summary of my TODO list:

Total tasks: {total}
Pending tasks: {pending}
Completed tasks: {completed}

Analyze the current state and provide recommendations for task prioritization."""


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


if __name__ == "__main__":
    # Run the server using stdio transport (for Claude Code integration)
    mcp.run()
