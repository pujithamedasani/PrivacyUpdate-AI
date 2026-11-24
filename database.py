import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from flask import g, has_app_context
from config import Config

def get_direct_db():
    """Create a standalone SQLite connection outside of Flask request context."""
    Config.ensure_directories()
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

def get_db():
    """Get or create SQLite connection attached to Flask g object if in app context."""
    if has_app_context():
        if 'db' not in g:
            Config.ensure_directories()
            g.db = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
            g.db.execute("PRAGMA journal_mode = WAL")
            g.db.execute("PRAGMA busy_timeout = 30000")
        return g.db
    return get_direct_db()

def close_db(e=None):
    """Close the database connection on request teardown."""
    if has_app_context():
        db = g.pop('db', None)
        if db is not None:
            db.close()

def query_db(query, args=(), one=False):
    """Execute a query and return rows as dictionary-like objects."""
    if has_app_context():
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (dict(rv[0]) if rv else None) if one else [dict(r) for r in rv]
    else:
        conn = get_direct_db()
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        conn.close()
        return (dict(rv[0]) if rv else None) if one else [dict(r) for r in rv]

def execute_db(query, args=(), commit=True):
    """Execute an INSERT, UPDATE, or DELETE query. Returns lastrowid."""
    if has_app_context():
        db = get_db()
        cur = db.execute(query, args)
        if commit:
            db.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id
    else:
        conn = get_direct_db()
        cur = conn.execute(query, args)
        if commit:
            conn.commit()
        last_id = cur.lastrowid
        cur.close()
        conn.close()
        return last_id

def init_db():
    """Initialize database tables with complete normalized schema."""
    Config.ensure_directories()
    conn = get_direct_db()
    cursor = conn.cursor()

    schema_statements = [
        """
        CREATE TABLE IF NOT EXISTS project_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            problem_statement TEXT NOT NULL,
            proposed_solution TEXT NOT NULL,
            objectives TEXT NOT NULL,
            scope TEXT NOT NULL,
            technologies TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            reg_number TEXT,
            role TEXT NOT NULL,
            email TEXT,
            responsibilities TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            start_date DATE NOT NULL,
            due_date DATE NOT NULL,
            completion_percentage INTEGER DEFAULT 0,
            status TEXT DEFAULT 'In Progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milestone_id INTEGER NOT NULL REFERENCES milestones(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            assigned_to INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
            priority TEXT DEFAULT 'Medium',
            start_date DATE,
            due_date DATE,
            status TEXT DEFAULT 'To Do',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            last_scanned_at TIMESTAMP,
            last_status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            version_tag TEXT NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            extraction_method TEXT DEFAULT 'Firecrawl',
            memento_archive_url TEXT,
            snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            old_snapshot_id INTEGER REFERENCES snapshots(id) ON DELETE SET NULL,
            new_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
            change_type TEXT NOT NULL,
            affected_section TEXT NOT NULL,
            previous_content TEXT,
            updated_content TEXT,
            category TEXT NOT NULL,
            ai_summary TEXT NOT NULL,
            privacy_implications TEXT NOT NULL,
            severity TEXT DEFAULT 'Medium',
            review_status TEXT DEFAULT 'Pending',
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_id INTEGER NOT NULL REFERENCES changes(id) ON DELETE CASCADE,
            reviewer_name TEXT NOT NULL,
            reviewer_id INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
            decision TEXT NOT NULL,
            comments TEXT,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER REFERENCES sources(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            extraction_tool TEXT DEFAULT 'Firecrawl',
            duration_seconds REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            doc_url TEXT,
            is_system INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS deliverables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            deadline DATE NOT NULL,
            assigned_to INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
            status TEXT DEFAULT 'Pending',
            file_path TEXT,
            file_name TEXT,
            submission_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]

    for stmt in schema_statements:
        cursor.execute(stmt)

    conn.commit()
    conn.close()

def backup_db():
    """Create a backup of the current SQLite database with a timestamp."""
    Config.ensure_directories()
    backup_dir = Config.DATABASE_PATH.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"privacyupdate_backup_{timestamp}.db"
    
    # Flush SQLite WAL/journal by connecting and closing
    conn = get_direct_db()
    conn.execute("PRAGMA wal_checkpoint(FULL);")
    conn.close()
    
    shutil.copy2(Config.DATABASE_PATH, backup_file)
    return backup_file
