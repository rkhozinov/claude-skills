#!/usr/bin/env python3
"""Things 3 helper. Write via URL scheme, read via SQLite."""
import glob, json, os, sqlite3, subprocess, sys, urllib.parse

DB_PATTERN = os.path.expanduser(
    "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-*/Things Database.thingsdatabase/main.sqlite"
)

def _db():
    paths = glob.glob(DB_PATTERN)
    if not paths:
        print("Error: Things 3 database not found", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(paths[0])
    conn.row_factory = sqlite3.Row
    return conn

# --- Write commands (URL scheme) ---

def add_todo(**params):
    encoded = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    subprocess.run(["open", f"things:///add?{encoded}"])

def add_json(data):
    encoded = urllib.parse.quote(json.dumps(data, ensure_ascii=False))
    subprocess.run(["open", f"things:///json?data={encoded}"])

def show(list_id="today"):
    subprocess.run(["open", f"things:///show?id={list_id}"])

# --- Read commands (SQLite) ---

LIST_FILTERS = {
    "today":    "t.start=1 AND t.status=0 AND t.trashed=0 AND t.type=0",
    "inbox":    "t.start=0 AND t.status=0 AND t.trashed=0 AND t.type=0 AND t.project IS NULL AND t.area IS NULL",
    "upcoming": "t.start=1 AND t.startDate IS NOT NULL AND t.status=0 AND t.trashed=0 AND t.type=0",
    "anytime":  "t.start=1 AND t.startDate IS NULL AND t.status=0 AND t.trashed=0 AND t.type=0",
    "someday":  "t.start=2 AND t.status=0 AND t.trashed=0 AND t.type=0",
    "logbook":  "t.status=3 AND t.trashed=0 AND t.type=0",
    "projects": "t.status=0 AND t.trashed=0 AND t.type=1",
    "trash":    "t.trashed=1",
}

def list_todos(list_name="today", limit=50):
    filt = LIST_FILTERS.get(list_name)
    if not filt:
        print(f"Unknown list: {list_name}. Available: {', '.join(LIST_FILTERS)}", file=sys.stderr)
        sys.exit(1)
    db = _db()
    rows = db.execute(f"""
        SELECT t.uuid, t.title, t.notes, t.startDate, t.deadline, t.status,
               p.title as project_title, a.title as area_title,
               GROUP_CONCAT(tag.title, ', ') as tags
        FROM TMTask t
        LEFT JOIN TMTask p ON t.project = p.uuid
        LEFT JOIN TMArea a ON t.area = a.uuid
        LEFT JOIN TMTaskTag tt ON t.uuid = tt.tasks
        LEFT JOIN TMTag tag ON tt.tags = tag.uuid
        WHERE {filt}
        GROUP BY t.uuid
        ORDER BY t.todayIndex, t."index"
        LIMIT ?
    """, (limit,)).fetchall()
    db.close()
    results = []
    for r in rows:
        item = {"title": r["title"]}
        if r["notes"]:        item["notes"] = r["notes"][:200]
        if r["project_title"]: item["project"] = r["project_title"]
        if r["area_title"]:   item["area"] = r["area_title"]
        if r["tags"]:         item["tags"] = r["tags"]
        if r["deadline"]:     item["deadline"] = r["deadline"]
        results.append(item)
    print(json.dumps(results, ensure_ascii=False, indent=2))

def search_todos(query, limit=20):
    db = _db()
    rows = db.execute("""
        SELECT t.title, t.notes, t.status,
               p.title as project_title, a.title as area_title
        FROM TMTask t
        LEFT JOIN TMTask p ON t.project = p.uuid
        LEFT JOIN TMArea a ON t.area = a.uuid
        WHERE t.trashed=0 AND t.type=0 AND (t.title LIKE ? OR t.notes LIKE ?)
        ORDER BY t.userModificationDate DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", limit)).fetchall()
    db.close()
    results = []
    for r in rows:
        item = {"title": r["title"], "status": "open" if r["status"] == 0 else "done"}
        if r["project_title"]: item["project"] = r["project_title"]
        if r["area_title"]:   item["area"] = r["area_title"]
        results.append(item)
    print(json.dumps(results, ensure_ascii=False, indent=2))

# --- Modify commands (AppleScript) ---

def _osascript(script):
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()

def move_todos(source, dest):
    """Move all todos from one list to another via AppleScript (loops to avoid bulk failures)."""
    count = _osascript(f'''
        set movedCount to 0
        tell application "Things3"
            set todoList to every to do of list "{source}"
            repeat with t in todoList
                try
                    move t to list "{dest}"
                    set movedCount to movedCount + 1
                end try
            end repeat
        end tell
        return movedCount
    ''')
    print(f"{count} todos moved from {source} to {dest}")

def delete_todos(list_name, title_filter=None):
    """Delete todos from a list, optionally filtering by title substring."""
    if title_filter:
        condition = f'name of t contains "{title_filter}"'
    else:
        condition = "true"
    count = _osascript(f'''
        set deletedCount to 0
        tell application "Things3"
            set todoList to to dos of list "{list_name}"
            repeat with t in todoList
                if {condition} then
                    delete t
                    set deletedCount to deletedCount + 1
                end if
            end repeat
        end tell
        return deletedCount
    ''')
    print(f"{count} todos deleted from {list_name}" + (f" matching '{title_filter}'" if title_filter else ""))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "add":
        params = {}
        for arg in sys.argv[2:]:
            k, _, v = arg.partition("=")
            params[k.lstrip("-")] = v
        add_todo(**params)

    elif cmd == "json":
        add_json(json.loads(sys.argv[2]))

    elif cmd == "show":
        show(sys.argv[2] if len(sys.argv) > 2 else "today")

    elif cmd == "list":
        name = sys.argv[2] if len(sys.argv) > 2 else "today"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        list_todos(name, limit)

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: things3.py search QUERY", file=sys.stderr)
            sys.exit(1)
        search_todos(sys.argv[2])

    elif cmd == "move":
        if len(sys.argv) < 4:
            print("Usage: things3.py move SOURCE DEST", file=sys.stderr)
            sys.exit(1)
        move_todos(sys.argv[2], sys.argv[3])

    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("Usage: things3.py delete LIST [title_filter]", file=sys.stderr)
            sys.exit(1)
        title_filter = sys.argv[3] if len(sys.argv) > 3 else None
        delete_todos(sys.argv[2], title_filter)

    else:
        print("Usage:")
        print("  things3.py add --title=TEXT [--when=<prefix>E] [--tags=T1,T2] ...")
        print("  things3.py json '[{\"type\":\"to-do\",\"attributes\":{\"title\":\"...\"}}]'")
        print("  things3.py show [inbox|today|upcoming|anytime|someday]")
        print("  things3.py list [today|inbox|upcoming|anytime|someday|logbook|projects|trash] [limit]")
        print("  things3.py search QUERY")
        print("  things3.py move SOURCE DEST")
        print("  things3.py delete LIST [title_filter]")
