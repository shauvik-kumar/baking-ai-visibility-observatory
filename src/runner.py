import uuid
from datetime import datetime, timezone

from database import get_connection, initialize_database
from gemini_adapter import ask_gemini
from questions import QUESTIONS

from experiment import (
    EXPERIMENT_ID,
    EXPERIMENT_VERSION,
    QUESTION_SET_VERSION,
    PROMPT_MODE,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_run():
    return str(uuid.uuid4())


def seed_questions(connection):
    for item in QUESTIONS:
        connection.execute(
            """
            INSERT OR IGNORE INTO queries (
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                item["query"],
                item["category"],
                item["subcategory"],
                item["intent"],
                item["geography"],
                item["commercial_intent"],
                item["entity_type"],
                item["difficulty"],
                utc_now(),
            ),
        )

    connection.commit()


def run_experiment():
    initialize_database()

    connection = get_connection()

    seed_questions(connection)

    run_id = create_run()
    started_at = utc_now()

    connection.execute(
        """
        INSERT INTO runs (
            run_id,
            started_at,
            status,
            question_count,
            experiment_id,
            experiment_version,
            question_set_version,
            prompt_mode
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                run_id,
                started_at,
                "running",
                len(QUESTIONS),
                EXPERIMENT_ID,
                EXPERIMENT_VERSION,
                QUESTION_SET_VERSION,
                PROMPT_MODE,
            )
        ),
    )

    connection.commit()

    print(f"\nRUN ID: {run_id}")
    print(f"Questions: {len(QUESTIONS)}")
    print("-" * 60)

    rate_limit = False

    for index, item in enumerate(QUESTIONS, start=1):

        print(f"\n[{index}/{len(QUESTIONS)}] {item['query']}")

        query_row = connection.execute(
            """
            SELECT query_id
            FROM queries
            WHERE query = ?
            """,
            (item["query"],),
        ).fetchone()

        result = ask_gemini(item["query"])

        connection.execute(
            """
            INSERT INTO responses (
                run_id,
                query_id,
                engine,
                model,
                timestamp,
                response_status,
                latency_ms,
                raw_response,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                query_row["query_id"],
                "gemini",
                "gemini-3.6-flash",
                utc_now(),
                result["status"],
                result["latency_ms"],
                result["text"],
                result["error"],
            ),
        )

        connection.commit()

        if result["status"] == "success":
            print(f"Success | {result['latency_ms']} ms")

        elif result["error_type"] == "rate_limit":
            print("RATE LIMIT REACHED")
            print("Stopping this run safely.")
            rate_limit = True
            break

        else:
            print(f"ERROR | {result['error']}")

    completed_at = utc_now()

    final_status = "completed"

    # If the loop was stopped because of a rate limit,
    # this run is partial rather than completed.
    if "rate_limit" in locals() and rate_limit:
        final_status = "partial"

    connection.execute(
        """
        UPDATE runs
        SET completed_at = ?,
            status = ?
        WHERE run_id = ?
        """,
        (
            completed_at,
            final_status,
            run_id,
        ),
    )

    connection.commit()
    connection.close()

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print(f"RUN ID: {run_id}")
    print("=" * 60)


if __name__ == "__main__":
    run_experiment()