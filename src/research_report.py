import csv
import sqlite3
from pathlib import Path

from config import DB_PATH


OUTPUT_FILE = Path("research_report.csv")


def compare_text(old_text, new_text):
    import difflib

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    added = 0
    removed = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed += i2 - i1

        if tag in ("replace", "insert"):
            added += j2 - j1

    return matcher.ratio(), added, removed


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            r.response_id,
            r.run_id,
            r.query_id,
            q.query,
            q.category,
            q.subcategory,
            q.intent,
            q.geography,
            q.commercial_intent,
            r.engine,
            r.model,
            r.timestamp,
            r.response_status,
            r.latency_ms,
            r.raw_response,
            r.error_message,
            runs.experiment_id,
            runs.experiment_version,
            runs.question_set_version,
            runs.prompt_mode
        FROM responses r
        JOIN queries q
            ON q.query_id = r.query_id
        JOIN runs
            ON runs.run_id = r.run_id
        ORDER BY r.query_id, r.timestamp
        """
    ).fetchall()

    grouped = {}

    for row in rows:
        grouped.setdefault(row["query_id"], []).append(row)

    output_rows = []

    for query_id, observations in grouped.items():

        for index, row in enumerate(observations):

            similarity = ""
            lines_added = ""
            lines_removed = ""

            # Compare this successful observation with the previous
            # successful observation for the same question.
            previous = None

            for candidate in reversed(observations[:index]):
                if candidate["response_status"] == "success":
                    previous = candidate
                    break

            if (
                previous
                and row["response_status"] == "success"
            ):
                (
                    similarity_value,
                    added_value,
                    removed_value,
                ) = compare_text(
                    previous["raw_response"],
                    row["raw_response"],
                )

                similarity = round(similarity_value, 4)
                lines_added = added_value
                lines_removed = removed_value

            output_rows.append(
                {
                    "response_id": row["response_id"],
                    "run_id": row["run_id"],
                    "query_id": row["query_id"],
                    "query": row["query"],
                    "category": row["category"],
                    "subcategory": row["subcategory"],
                    "intent": row["intent"],
                    "geography": row["geography"],
                    "commercial_intent": row["commercial_intent"],
                    "engine": row["engine"],
                    "model": row["model"],
                    "timestamp": row["timestamp"],
                    "response_status": row["response_status"],
                    "latency_ms": row["latency_ms"],
                    "response_characters": (
                        len(row["raw_response"])
                        if row["raw_response"]
                        else 0
                    ),
                    "similarity_to_previous": similarity,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "experiment_id": row["experiment_id"] or "",
                    "experiment_version": row["experiment_version"] or "",
                    "question_set_version": (
                        row["question_set_version"] or ""
                    ),
                    "prompt_mode": row["prompt_mode"] or "",
                    "error_message": row["error_message"] or "",
                }
            )

    fieldnames = [
        "response_id",
        "run_id",
        "query_id",
        "query",
        "category",
        "subcategory",
        "intent",
        "geography",
        "commercial_intent",
        "engine",
        "model",
        "timestamp",
        "response_status",
        "latency_ms",
        "response_characters",
        "similarity_to_previous",
        "lines_added",
        "lines_removed",
        "experiment_id",
        "experiment_version",
        "question_set_version",
        "prompt_mode",
        "error_message",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(output_rows)

    connection.close()

    print(
        f"Research report created: {OUTPUT_FILE}"
    )
    print(
        f"Rows exported: {len(output_rows)}"
    )


if __name__ == "__main__":
    main()