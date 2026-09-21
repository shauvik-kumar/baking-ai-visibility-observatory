import sqlite3
import difflib

from config import DB_PATH


def get_successful_responses(connection):
    rows = connection.execute(
        """
        SELECT
            r.response_id,
            r.run_id,
            r.query_id,
            q.query,
            r.timestamp,
            r.raw_response
        FROM responses r
        JOIN queries q
            ON q.query_id = r.query_id
        WHERE r.response_status = 'success'
        ORDER BY r.query_id, r.timestamp
        """
    ).fetchall()

    return rows


def compare_text(old_text, new_text):
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

    similarity = matcher.ratio()

    return similarity, added, removed


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = get_successful_responses(connection)

    grouped = {}

    for row in rows:
        grouped.setdefault(row["query_id"], []).append(row)

    print("\nRUN-TO-RUN RESPONSE COMPARISON")
    print("=" * 90)

    comparisons = 0

    for query_id, responses in grouped.items():

        if len(responses) < 2:
            continue

        old = responses[-2]
        new = responses[-1]

        similarity, added, removed = compare_text(
            old["raw_response"],
            new["raw_response"],
        )

        print(f"\nQuery {query_id}: {old['query']}")
        print(f"Old run: {old['run_id']}")
        print(f"New run: {new['run_id']}")
        print(f"Similarity: {similarity:.2%}")
        print(f"Lines added: {added}")
        print(f"Lines removed: {removed}")

        comparisons += 1

    print("\n" + "=" * 90)
    print(f"Questions compared: {comparisons}")

    connection.close()


if __name__ == "__main__":
    main()