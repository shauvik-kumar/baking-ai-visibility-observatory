import sys
from datetime import datetime

from database import get_connection


def get_latest_run(conn):
    return conn.execute(
        """
        SELECT
            run_id,
            started_at,
            completed_at,
            status,
            question_count,
            experiment_id,
            experiment_version,
            question_set_version,
            prompt_mode
        FROM runs
        ORDER BY started_at DESC
        LIMIT 1
        """
    ).fetchone()


def get_run_responses(conn, run_id):
    return conn.execute(
        """
        SELECT
            r.response_id,
            r.query_id,
            q.query,
            q.category,
            q.subcategory,
            r.engine,
            r.model,
            r.timestamp,
            r.response_status,
            r.latency_ms,
            r.raw_response,
            r.error_message
        FROM responses r
        JOIN queries q
          ON q.query_id = r.query_id
        WHERE r.run_id = ?
        ORDER BY r.query_id
        """,
        (run_id,),
    ).fetchall()


def count_headings(text):
    if not text:
        return 0

    count = 0

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("#"):
            count += 1
        elif stripped.startswith("**") and stripped.endswith("**"):
            count += 1

    return count


def count_bullets(text):
    if not text:
        return 0

    count = 0

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith(("-", "*", "•")):
            count += 1

        elif len(stripped) >= 3:
            first = stripped.split(".", 1)[0]

            if first.isdigit():
                count += 1

    return count


def count_urls(text):
    if not text:
        return 0

    count = 0

    for token in text.split():
        if token.startswith(("http://", "https://")):
            count += 1

    return count


def get_previous_response(conn, query_id, current_timestamp):
    return conn.execute(
        """
        SELECT
            response_id,
            timestamp,
            raw_response
        FROM responses
        WHERE query_id = ?
          AND response_status = 'success'
          AND timestamp < ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (query_id, current_timestamp),
    ).fetchone()


def similarity_percentage(current_text, previous_text):
    if not current_text or not previous_text:
        return None

    current_words = set(current_text.lower().split())
    previous_words = set(previous_text.lower().split())

    if not current_words or not previous_words:
        return None

    intersection = len(current_words & previous_words)
    union = len(current_words | previous_words)

    if union == 0:
        return None

    return round((intersection / union) * 100, 2)


def print_report():
    conn = get_connection()

    try:
        run = get_latest_run(conn)

        if not run:
            print("No experiment runs found.")
            return

        responses = get_run_responses(conn, run["run_id"])

        successful = [
            r for r in responses
            if r["response_status"] == "success"
        ]

        errors = [
            r for r in responses
            if r["response_status"] != "success"
        ]

        print()
        print("BAKING AI VISIBILITY OBSERVATORY")
        print("=" * 72)

        print(f"Run ID                  : {run['run_id']}")
        print(f"Started                 : {run['started_at']}")
        print(f"Completed               : {run['completed_at']}")
        print(f"Status                  : {run['status']}")
        print(f"Questions               : {run['question_count']}")
        print(f"Successful              : {len(successful)}")
        print(f"Errors                  : {len(errors)}")

        experiment_id = run["experiment_id"] or "Not recorded in historical run"
        experiment_version = (
            run["experiment_version"] or "Not recorded in historical run"
        )
        question_set_version = (
            run["question_set_version"] or "Not recorded in historical run"
        )
        prompt_mode = run["prompt_mode"] or "Not recorded in historical run"

        print(f"Experiment              : {experiment_id}")
        print(f"Experiment version      : {experiment_version}")
        print(f"Question set version    : {question_set_version}")
        print(f"Prompt mode             : {prompt_mode}")

        print()
        print("-" * 72)
        print("QUESTION RESULTS")
        print("-" * 72)

        for row in responses:
            print()
            print(f"Q{row['query_id']}")
            print(f"Question: {row['query']}")
            print(
                f"Category: {row['category']} | "
                f"Subcategory: {row['subcategory']}"
            )

            print(f"Engine: {row['engine']} | Model: {row['model']}")
            print(f"Status: {row['response_status']}")

            if row["response_status"] != "success":
                print(f"Error: {row['error_message']}")
                continue

            text = row["raw_response"] or ""

            previous = get_previous_response(
                conn,
                row["query_id"],
                row["timestamp"],
            )

            similarity = None

            if previous:
                similarity = similarity_percentage(
                    text,
                    previous["raw_response"],
                )

            print(f"Response characters: {len(text):,}")
            print(f"Headings/sections:   {count_headings(text)}")
            print(f"Bullets/lists:       {count_bullets(text)}")
            print(f"Explicit URLs:       {count_urls(text)}")
            print(f"Latency:             {row['latency_ms']} ms")

            if previous:
                print(
                    f"Previous response:  {previous['response_id']}"
                )

                if similarity is not None:
                    print(
                    f"Token-set overlap:   {similarity}%"
                )
            else:
                print("Previous response:  none")

            preview = " ".join(text.split())

            if len(preview) > 300:
                preview = preview[:300] + "..."

            print()
            print("Answer preview:")
            print(preview)

        print()
        print("=" * 72)
        print("REPORT COMPLETE")
        print("=" * 72)
        print()

    finally:
        conn.close()


if __name__ == "__main__":
    print_report()