import re
import sqlite3
import csv
from pathlib import Path

from config import DB_PATH


OUTPUT_FILE = Path("recommendation_candidates.csv")


# Phrases that commonly introduce recommendations.
INTRO_PATTERNS = [
    r"(?:^|\n)\s*\d+\.\s+(.+)",
    r"(?:^|\n)\s*[-*]\s+(.+)",
    r"(?:recommended|recommendations include|popular options include|examples include|some options include)\s*:?\s*(.+)",
]


def clean_candidate(text):
    text = text.strip()

    # Remove markdown emphasis.
    text = re.sub(r"[*_`]", "", text)

    # Remove leading numbering.
    text = re.sub(r"^\d+[.)]\s*", "", text)

    # Remove leading bullet.
    text = re.sub(r"^[-*]\s*", "", text)

    return text.strip()


def extract_recommendation_lines(text):
    if not text:
        return []

    candidates = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # Numbered recommendation.
        if re.match(r"^\d+[.)]\s+", line):
            candidates.append(clean_candidate(line))
            continue

        # Bullet recommendation.
        if re.match(r"^[-*]\s+", line):
            candidates.append(clean_candidate(line))
            continue

    # Preserve order and remove duplicates.
    seen = set()
    unique = []

    for candidate in candidates:
        key = candidate.lower()

        if key not in seen:
            seen.add(key)
            unique.append(candidate)

    return unique


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
        candidates = extract_recommendation_lines(
            row["raw_response"]
        )

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
    print(f"Recommendation candidates: {len(output)}")


if __name__ == "__main__":
    main()