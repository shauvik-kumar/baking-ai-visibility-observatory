import re
import sqlite3

from config import DB_PATH


# Common words that should not be treated as entities.
STOPWORDS = {
    "The",
    "This",
    "These",
    "Those",
    "For",
    "With",
    "From",
    "Where",
    "What",
    "How",
    "Why",
    "Best",
    "Good",
    "India",
    "Noida",
    "Cake",
    "Cakes",
    "Baking",
    "Online",
    "Class",
    "Classes",
}


def extract_candidates(text):
    """
    Find simple capitalized multi-word phrases.

    This is intentionally a candidate extractor, not an
    NLP/entity-truth system. Human validation comes later.
    """

    if not text:
        return []

    pattern = r"\b[A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,4}\b"

    matches = re.findall(pattern, text)

    candidates = []

    for match in matches:
        value = match.strip()

        if value in STOPWORDS:
            continue

        if len(value) < 3:
            continue

        candidates.append(value)

    # Preserve order while removing duplicates.
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
            query_id,
            raw_response
        FROM responses
        WHERE response_status = 'success'
        ORDER BY response_id
        """
    ).fetchall()

    print("\nENTITY CANDIDATES")
    print("=" * 90)

    total = 0

    for row in rows:
        candidates = extract_candidates(row["raw_response"])

        print(f"\nResponse ID: {row['response_id']}")
        print(f"Query ID: {row['query_id']}")

        if candidates:
            for candidate in candidates:
                print(f"  - {candidate}")
                total += 1
        else:
            print("  No candidates found")

    print("\n" + "=" * 90)
    print(f"Candidate mentions found: {total}")

    connection.close()


if __name__ == "__main__":
    main()