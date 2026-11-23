
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


mcp = MCPServer("Placement Tracker")

# Database file sits next to this file
DB_PATH = Path(__file__).parent / "applications.db"

STATUSES = ["applied", "oa", "interview", "offer", "rejected"]


# --------------------------------------------------
# DATABASE CONNECTION AND MIGRATION
# --------------------------------------------------

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute(
        """CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            applied_on TEXT NOT NULL,
            notes TEXT DEFAULT '',
            interview_date TEXT
        )"""
    )

    # Migration for existing databases
    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(applications)")
    ]

    if "interview_date" not in columns:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN interview_date TEXT"
        )

    return conn


# --------------------------------------------------
# TOOL 1: ADD APPLICATION
# --------------------------------------------------

@mcp.tool()
def add_application(company: str, role: str, notes: str = "") -> str:
    """Save a new job or internship application. Status starts as applied."""

    with db() as conn:
        cur = conn.execute(
            """INSERT INTO applications
            (company, role, status, applied_on, notes)
            VALUES (?, ?, ?, ?, ?)""",
            (company, role, "applied", date.today().isoformat(), notes),
        )

    return f"Saved: {company} - {role} (id {cur.lastrowid})"


# --------------------------------------------------
# TOOL 2: UPDATE APPLICATION STATUS
# --------------------------------------------------

@mcp.tool()
def update_status(app_id: int, status: str, notes: str = "") -> str:
    """Change application status. Valid statuses:
    applied, oa, interview, offer, rejected."""

    status = status.lower()

    if status not in STATUSES:
        raise ToolError(f"Status must be one of {STATUSES}")

    with db() as conn:
        cur = conn.execute(
            """UPDATE applications
            SET status = ?, notes = ?
            WHERE id = ?""",
            (status, notes, app_id),
        )

        if cur.rowcount == 0:
            raise ToolError(f"No application with id {app_id}")

    return f"Application {app_id} is now '{status}'"


# --------------------------------------------------
# TOOL 3: LIST APPLICATIONS
# --------------------------------------------------

@mcp.tool()
def list_applications(status: str = "") -> list[dict]:
    """List applications, newest first. Optionally filter by status."""

    with db() as conn:
        if status:
            rows = conn.execute(
                """SELECT * FROM applications
                WHERE status = ?
                ORDER BY id DESC""",
                (status.lower(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY id DESC"
            ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# TOOL 4: APPLICATION STATISTICS
# --------------------------------------------------

@mcp.tool()
def get_stats() -> dict:
    """Count applications by status and calculate reply rate."""

    with db() as conn:
        rows = conn.execute(
            """SELECT status, COUNT(*) AS n
            FROM applications
            GROUP BY status"""
        ).fetchall()

    counts = {status: 0 for status in STATUSES}
    counts.update({row["status"]: row["n"] for row in rows})

    total = sum(counts.values())
    replied = counts["oa"] + counts["interview"] + counts["offer"]

    return {
        "total": total,
        "by_status": counts,
        "reply_rate_percent": round(100 * replied / total) if total else 0,
    }


# --------------------------------------------------
# TOOL 5: UPCOMING INTERVIEWS
# --------------------------------------------------

@mcp.tool()
def upcoming_interviews() -> list[dict]:
    """List interviews scheduled from today through the next 7 days."""

    today = date.today()
    next_week = today + timedelta(days=7)

    with db() as conn:
        rows = conn.execute(
            """SELECT *
            FROM applications
            WHERE interview_date BETWEEN ? AND ?
            ORDER BY interview_date ASC""",
            (today.isoformat(), next_week.isoformat()),
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# TOOL 6: DELETE APPLICATION
# --------------------------------------------------

@mcp.tool()
def delete_application(app_id: int) -> str:
    """Delete an application using its ID. Raises an error if not found."""

    with db() as conn:
        cur = conn.execute(
            "DELETE FROM applications WHERE id = ?",
            (app_id,),
        )

        if cur.rowcount == 0:
            raise ToolError(f"No application found with id {app_id}")

    return f"Application {app_id} deleted successfully"


# --------------------------------------------------
# TOOL 7: SET INTERVIEW DATE
# --------------------------------------------------

@mcp.tool()
def set_interview_date(app_id: int, interview_date: str) -> str:
    """Set an interview date using YYYY-MM-DD format."""

    try:
        parsed_date = datetime.strptime(
            interview_date, "%Y-%m-%d"
        ).date()
    except ValueError:
        raise ToolError("Invalid date. Use YYYY-MM-DD format.")

    if parsed_date < date.today():
        raise ToolError("Interview date cannot be in the past.")

    with db() as conn:
        cur = conn.execute(
            """UPDATE applications
            SET interview_date = ?, status = 'interview'
            WHERE id = ?""",
            (parsed_date.isoformat(), app_id),
        )

        if cur.rowcount == 0:
            raise ToolError(f"No application found with id {app_id}")

    return f"Interview date for application {app_id} set to {interview_date}"


# --------------------------------------------------
# RESOURCE 1: TRACKER SUMMARY
# --------------------------------------------------

@mcp.resource("tracker://summary")
def summary() -> str:
    """A one-line summary of the whole tracker."""

    stats = get_stats()

    return (
        f"{stats['total']} applications, "
        f"{stats['reply_rate_percent']}% got a reply"
    )


# --------------------------------------------------
# RESOURCE 2: COMPANY APPLICATIONS
# --------------------------------------------------

@mcp.resource("tracker://company/{name}")
def company_applications(name: str) -> str:
    """Return all applications for a particular company."""

    with db() as conn:
        rows = conn.execute(
            """SELECT *
            FROM applications
            WHERE company = ? COLLATE NOCASE
            ORDER BY id DESC""",
            (name,),
        ).fetchall()

    if not rows:
        return f"No applications found for {name}."

    return "\n".join(
        [
            f"ID: {row['id']} | "
            f"Company: {row['company']} | "
            f"Role: {row['role']} | "
            f"Status: {row['status']} | "
            f"Applied: {row['applied_on']} | "
            f"Interview: {row['interview_date'] or 'Not scheduled'}"
            for row in rows
        ]
    )


# --------------------------------------------------
# PROMPT: WEEKLY REVIEW
# --------------------------------------------------

@mcp.prompt()
def weekly_review() -> str:
    """Ask the AI to review this week's applications and suggest next steps."""

    return (
        "Use my placement tracker tools. Show my stats, list "
        "applications still in 'applied' for more than 7 days, "
        "and suggest which ones to follow up on and what to prepare next."
    )


# --------------------------------------------------
# START MCP SERVER
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run()
