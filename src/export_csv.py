import csv
import sqlite3

from config import DB_PATH


OUTPUT_FILE = "observatory_responses.csv"


def export_responses():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            r.response_id,
            r.run_id,
            q.query_id,
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
            r.error_message
        FROM responses r
        JOIN queries q
            ON q.query_id = r.query_id
        ORDER BY r.response_id
        """
    ).fetchall()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
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
            "raw_response",
            "error_message",
        ])

        for row in rows:
            writer.writerow([
                row["response_id"],
                row["run_id"],
                row["query_id"],
                row["query"],
                row["category"],
                row["subcategory"],
                row["intent"],
                row["geography"],
                row["commercial_intent"],
                row["engine"],
                row["model"],
                row["timestamp"],
                row["response_status"],
                row["latency_ms"],
                row["raw_response"],
                row["error_message"],
            ])

    connection.close()

    print(f"Exported {len(rows)} responses to {OUTPUT_FILE}")


if __name__ == "__main__":
    export_responses()