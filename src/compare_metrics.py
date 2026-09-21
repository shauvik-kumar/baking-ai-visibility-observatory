import sqlite3

from config import DB_PATH


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute("""
        SELECT
            query_id,
            run_id,
            response_id,
            word_count,
            character_count,
            bullet_count,
            heading_count,
            bold_phrase_count,
            url_count
        FROM response_metrics
        WHERE engine = 'gemini'
        ORDER BY query_id, response_id
    """).fetchall()

    grouped = {}

    for row in rows:
        grouped.setdefault(row["query_id"], []).append(row)

    print("GEMINI RUN-TO-RUN STRUCTURAL COMPARISON")
    print("=" * 100)

    comparable = 0

    for query_id, observations in grouped.items():

        if len(observations) < 2:
            continue

        first = observations[0]
        second = observations[1]

        comparable += 1

        print(f"\nQUERY {query_id}")
        print("-" * 100)

        print(
            f"Words       : {first['word_count']} -> "
            f"{second['word_count']} "
            f"({second['word_count'] - first['word_count']:+d})"
        )

        print(
            f"Characters  : {first['character_count']} -> "
            f"{second['character_count']} "
            f"({second['character_count'] - first['character_count']:+d})"
        )

        print(
            f"Bullets     : {first['bullet_count']} -> "
            f"{second['bullet_count']} "
            f"({second['bullet_count'] - first['bullet_count']:+d})"
        )

        print(
            f"Headings    : {first['heading_count']} -> "
            f"{second['heading_count']} "
            f"({second['heading_count'] - first['heading_count']:+d})"
        )

        print(
            f"Bold phrases: {first['bold_phrase_count']} -> "
            f"{second['bold_phrase_count']} "
            f"({second['bold_phrase_count'] - first['bold_phrase_count']:+d})"
        )

        print(
            f"URLs        : {first['url_count']} -> "
            f"{second['url_count']} "
            f"({second['url_count'] - first['url_count']:+d})"
        )

    print("\n" + "=" * 100)
    print(f"COMPARABLE QUESTIONS = {comparable}")

    connection.close()


if __name__ == "__main__":
    main()