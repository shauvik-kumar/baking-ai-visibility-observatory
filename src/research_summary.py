import csv
import sqlite3
from pathlib import Path

from config import DB_PATH


OUTPUT_FILE = Path("research_summary.csv")


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            q.query_id,
            q.query,
            q.category,
            q.subcategory,
            q.intent,
            q.geography,
            q.commercial_intent,

            COUNT(r.response_id) AS observations,

            SUM(
                CASE
                    WHEN r.response_status = 'success'
                    THEN 1
                    ELSE 0
                END
            ) AS successful_observations,

            MIN(r.timestamp) AS first_observation,
            MAX(r.timestamp) AS latest_observation,

            MIN(
                CASE
                    WHEN r.response_status = 'success'
                    THEN r.latency_ms
                END
            ) AS fastest_latency_ms,

            MAX(
                CASE
                    WHEN r.response_status = 'success'
                    THEN r.latency_ms
                END
            ) AS slowest_latency_ms,

            AVG(
                CASE
                    WHEN r.response_status = 'success'
                    THEN r.latency_ms
                END
            ) AS average_latency_ms,

            MIN(
                CASE
                    WHEN r.response_status = 'success'
                    THEN LENGTH(r.raw_response)
                END
            ) AS shortest_response_chars,

            MAX(
                CASE
                    WHEN r.response_status = 'success'
                    THEN LENGTH(r.raw_response)
                END
            ) AS longest_response_chars

        FROM queries q

        LEFT JOIN responses r
            ON r.query_id = q.query_id

        GROUP BY
            q.query_id,
            q.query,
            q.category,
            q.subcategory,
            q.intent,
            q.geography,
            q.commercial_intent

        ORDER BY q.query_id
        """
    ).fetchall()

    fieldnames = [
        "query_id",
        "query",
        "category",
        "subcategory",
        "intent",
        "geography",
        "commercial_intent",
        "observations",
        "successful_observations",
        "first_observation",
        "latest_observation",
        "fastest_latency_ms",
        "slowest_latency_ms",
        "average_latency_ms",
        "shortest_response_chars",
        "longest_response_chars",
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

        for row in rows:
            writer.writerow(dict(row))

    connection.close()

    print(f"Research summary created: {OUTPUT_FILE}")
    print(f"Questions: {len(rows)}")


if __name__ == "__main__":
    main()