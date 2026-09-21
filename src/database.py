import sqlite3

from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_column_if_missing(
    conn,
    table_name,
    column_name,
    column_definition,
):
    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = {
        row[1]
        for row in columns
    }

    if column_name not in existing_columns:
        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


def create_base_tables(conn):
    conn.execute(
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
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            question_count INTEGER NOT NULL,
            experiment_id TEXT,
            experiment_version TEXT,
            question_set_version TEXT,
            prompt_mode TEXT
        )
        """
    )

    conn.execute(
        """
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
        )
        """
    )


def create_research_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL,
            entity_type TEXT,
            first_seen_at TEXT,
            last_seen_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS citations (
            citation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            domain TEXT,
            title TEXT,
            first_seen_at TEXT,
            last_seen_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_entities (
            response_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            mention_text TEXT,
            position INTEGER,
            PRIMARY KEY (response_id, entity_id, position),
            FOREIGN KEY (response_id) REFERENCES responses(response_id),
            FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_citations (
            response_id INTEGER NOT NULL,
            citation_id INTEGER NOT NULL,
            position INTEGER,
            PRIMARY KEY (response_id, citation_id, position),
            FOREIGN KEY (response_id) REFERENCES responses(response_id),
            FOREIGN KEY (citation_id) REFERENCES citations(citation_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS changes (
            change_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER NOT NULL,
            previous_response_id INTEGER,
            current_response_id INTEGER,
            change_type TEXT NOT NULL,
            change_summary TEXT,
            detected_at TEXT NOT NULL,
            FOREIGN KEY (query_id) REFERENCES queries(query_id),
            FOREIGN KEY (previous_response_id) REFERENCES responses(response_id),
            FOREIGN KEY (current_response_id) REFERENCES responses(response_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_metrics (
            response_id INTEGER PRIMARY KEY,
            run_id TEXT NOT NULL,
            query_id INTEGER NOT NULL,
            engine TEXT NOT NULL,
            model TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            character_count INTEGER NOT NULL,
            word_count INTEGER NOT NULL,
            bullet_count INTEGER NOT NULL,
            heading_count INTEGER NOT NULL,
            bold_phrase_count INTEGER NOT NULL,
            url_count INTEGER NOT NULL,
            FOREIGN KEY (response_id) REFERENCES responses(response_id),
            FOREIGN KEY (run_id) REFERENCES runs(run_id),
            FOREIGN KEY (query_id) REFERENCES queries(query_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_sentences (
            sentence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER NOT NULL,
            sentence_index INTEGER NOT NULL,
            sentence_text TEXT NOT NULL,
            sentence_hash TEXT NOT NULL,
            FOREIGN KEY (response_id) REFERENCES responses(response_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_entities_observed (
            observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER NOT NULL,
            query_id INTEGER NOT NULL,
            entity_text TEXT NOT NULL,
            canonical_entity TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            FOREIGN KEY (response_id) REFERENCES responses(response_id),
            FOREIGN KEY (query_id) REFERENCES queries(query_id)
        )
        """
    )


def migrate_existing_database(conn):
    """
    Preserve the existing database while adding any columns
    introduced after the original Phase 1 schema.
    """

    add_column_if_missing(
        conn,
        "runs",
        "experiment_id",
        "TEXT",
    )

    add_column_if_missing(
        conn,
        "runs",
        "experiment_version",
        "TEXT",
    )

    add_column_if_missing(
        conn,
        "runs",
        "question_set_version",
        "TEXT",
    )

    add_column_if_missing(
        conn,
        "runs",
        "prompt_mode",
        "TEXT",
    )

    add_column_if_missing(
        conn,
        "responses",
        "raw_interaction",
        "TEXT",
    )


def initialize_database():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)

    try:
        create_base_tables(conn)
        migrate_existing_database(conn)
        create_research_tables(conn)

        conn.commit()

    finally:
        conn.close()