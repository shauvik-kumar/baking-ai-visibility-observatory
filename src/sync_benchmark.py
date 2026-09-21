import sqlite3
from datetime import datetime, timezone

from benchmark_loader import get_active_questions
from config import DB_PATH


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sync_benchmark():
    questions = get_active_questions()

    conn = sqlite3.connect(DB_PATH)

    inserted = 0
    updated = 0

    try:
        for question in questions:

            existing = conn.execute(
                """
                SELECT query_id
                FROM queries
                WHERE query = ?
                """,
                (question["query"],),
            ).fetchone()

            if existing:

                conn.execute(
                    """
                    UPDATE queries
                    SET
                        category = ?,
                        subcategory = ?,
                        intent = ?,
                        geography = ?,
                        commercial_intent = ?,
                        entity_type = ?,
                        difficulty = ?,
                        active = ?
                    WHERE query_id = ?
                    """,
                    (
                        question["category"],
                        question["subcategory"],
                        question["intent"],
                        question["geography"],
                        question["commercial_intent"],
                        question["entity_type"],
                        question["difficulty"],
                        question["active"],
                        existing[0],
                    ),
                )

                updated += 1

            else:

                conn.execute(
                    """
                    INSERT INTO queries (
                        query,
                        category,
                        subcategory,
                        intent,
                        geography,
                        commercial_intent,
                        entity_type,
                        difficulty,
                        active,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        question["query"],
                        question["category"],
                        question["subcategory"],
                        question["intent"],
                        question["geography"],
                        question["commercial_intent"],
                        question["entity_type"],
                        question["difficulty"],
                        question["active"],
                        utc_now(),
                    ),
                )

                inserted += 1

        conn.commit()

    finally:
        conn.close()

    print("BENCHMARK SYNC COMPLETE")
    print("=" * 60)
    print(f"Benchmark questions : {len(questions)}")
    print(f"Inserted             : {inserted}")
    print(f"Updated              : {updated}")


if __name__ == "__main__":
    sync_benchmark()