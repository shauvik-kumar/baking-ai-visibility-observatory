import csv
import sqlite3
from pathlib import Path

from config import DB_PATH
from entity_extractor import extract_candidates


OUTPUT_FILE = Path("entity_candidates.csv")


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            response_id,
            run_id,
            query_id,
            raw_response
        FROM responses
        WHERE response_status = 'success'
        ORDER BY response_id
        """
    ).fetchall()

    output = []

    for row in rows:
        candidates = extract_candidates(row["raw_response"])

        for candidate in candidates:
            output.append(
                {
                    "response_id": row["response_id"],
                    "run_id": row["run_id"],
                    "query_id": row["query_id"],
                    "candidate": candidate,
                    "validated": "",
                    "entity_type": "",
                    "notes": "",
                }
            )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "response_id",
                "run_id",
                "query_id",
                "candidate",
                "validated",
                "entity_type",
                "notes",
            ],
        )

        writer.writeheader()
        writer.writerows(output)

    connection.close()

    print(f"Created: {OUTPUT_FILE}")
    print(f"Candidate rows: {len(output)}")


if __name__ == "__main__":
    main()