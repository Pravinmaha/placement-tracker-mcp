# Placement Tracker MCP Server

A Python-based MCP server that allows AI assistants like Claude to manage job applications, track interview dates, and review placement progress using natural language.

## Features

- Add and update job applications.
- Track application statuses: Applied, OA, Interview, Offer, Rejected.
- Schedule and view upcoming interviews within the next 7 days.
- Delete applications with error handling for invalid IDs.
- Retrieve application details for individual companies.
- View placement statistics and summaries.

## Tech Stack

- Python
- MCP SDK v2
- SQLite
- uv (Python package and project manager)
- Claude Desktop

## MCP Tools

| Tool | Description | Inputs |
|---|---|---|
| `add_application` | Add a new job application | company, role, notes |
| `update_status` | Update application status | app_id, status, notes |
| `list_applications` | List applications, optionally by status | status |
| `get_stats` | Get application statistics | None |
| `upcoming_interviews` | List interviews scheduled in the next 7 days | None |
| `delete_application` | Delete an application; raises an error for an unknown ID | app_id |
| `set_interview_date` | Set an interview date for an application | app_id, interview_date |

## Resources

| Resource URI | Description |
|---|---|
| `tracker://summary` | Overall placement tracker summary |
| `tracker://company/{name}` | Applications associated with a specific company |

## Prompt

- `weekly_review`: Helps review application progress and plan the next week's job-search activities.

## Setup

### 1. Install dependencies

```bash
uv add "mcp[cli]"
```

### 2. Run the MCP Inspector for development and testing

```bash
uv run mcp dev server.py
```

### 3. Install the server in Claude Desktop

```bash
uv run mcp install server.py
```

**Note:** If Claude Desktop is installed through the Microsoft Store (MSIX), automatic installation may not detect it. In that case, configure the server manually in Claude Desktop's MCP configuration file.

## Run Locally

```bash
uv run python server.py
```

## Demo

Add a 30-second screen recording or GIF here showing Claude performing these actions:

1. Adding a job application.
2. Updating its status.
3. Setting an interview date.
4. Checking upcoming interviews.

## Database

The project uses SQLite to store application details, including company, role, status, application date, notes, and interview date.

The database schema also supports migration of existing databases by adding the interview date column when needed.

## Project Highlights

- Custom MCP tools with typed inputs and descriptions.
- SQLite database integration.
- Input validation and error handling.
- Date-based interview tracking.
- Company-specific MCP resources.

## Future Improvements

- Streamable HTTP transport.
- Cloud deployment using PostgreSQL.
- Automated tests with pytest.

## MCP SDK Version

Built using **MCP SDK version 2**.