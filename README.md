# TODO MCP Server

A simple todo manager built as an MCP (Model Context Protocol) server using FastMCP. This server exposes tools, resources, and prompts for managing TODO items, designed to integrate with Claude Code.

## Features

- **Tools**: Add, complete, update, delete, and list todos
- **Resources**: Access formatted views of all, pending, or completed todos
- **Prompts**: Generate todo summaries and daily planning prompts
- **In-memory storage**: Lightweight todo management for development and testing

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-todo-server
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Standalone Mode

Run the server directly:
```bash
python3 todo_server.py
```

### With Claude Code

The server is configured to work with Claude Code via the `.mcp.json` file. Once configured, Claude Code will automatically start the server and expose its tools.

## Available Tools

| Tool | Description |
|------|-------------|
| `add_todo` | Add a new todo with title and optional description |
| `complete_task` | Mark a todo as completed by ID |
| `delete_task` | Remove a todo from the list by ID |
| `update_task` | Update a todo's title or description |
| `list_tasks` | List all todos, optionally filtered by status |

## Available Resources

| Resource URI | Description |
|--------------|-------------|
| `tasks://all` | Formatted list of all todos |
| `tasks://pending` | Formatted list of pending todos |
| `tasks://completed` | Formatted list of completed todos |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `task_summary` | Generates a summary of current todo status |
| `daily_planning` | Generates a daily planning prompt based on pending todos |

## License

MIT
