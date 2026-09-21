import sqlite3

from config import DB_PATH


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def add_column_if_missing(connection, table, column, definition):
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }

    if column not in columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def initialize_database():
    connection = get_connection()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS queries (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL UNIQUE,
            category TEXT,
            subcategory TEXT,
            intent TEXT,
            geography TEXT,
            commercial_intent TEXT,
            entity_type TEXT,
            difficulty TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            question_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            query_id INTEGER NOT NULL,
            engine TEXT NOT NULL,
            model TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            response_status TEXT NOT NULL,
            latency_ms INTEGER,
            raw_response TEXT,
            error_message TEXT,

            FOREIGN KEY (run_id) REFERENCES runs(run_id),
            FOREIGN KEY (query_id) REFERENCES queries(query_id)
        );
        """
    )

    # Add experiment metadata to existing databases.
    add_column_if_missing(
        connection,
        "runs",
        "experiment_id",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "runs",
        "experiment_version",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "runs",
        "question_set_version",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "runs",
        "prompt_mode",
        "TEXT",
    )

    connection.commit()
    connection.close()