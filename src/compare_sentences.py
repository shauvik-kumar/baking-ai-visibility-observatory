import sqlite3

from config import DB_PATH


def get_sentences(connection, response_id):
    rows = connection.execute(
        """
        SELECT sentence_hash, sentence_text
        FROM response_sentences
        WHERE response_id = ?
        ORDER BY sentence_index
        """,
        (response_id,),
    ).fetchall()

    return rows


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            r.response_id,
            r.query_id,
            r.run_id
        FROM responses r
        WHERE r.engine = 'gemini'
          AND r.response_status = 'success'
          AND r.raw_response IS NOT NULL
        ORDER BY r.query_id, r.response_id
        """
    ).fetchall()

    grouped = {}

    for row in rows:
        grouped.setdefault(row["query_id"], []).append(row)

    print("GEMINI SENTENCE-LEVEL RUN COMPARISON")
    print("=" * 100)

    comparable = 0

    for query_id, observations in grouped.items():

        if len(observations) < 2:
            continue

        first = observations[0]
        second = observations[1]

        first_sentences = get_sentences(
            connection,
            first["response_id"]
        )

        second_sentences = get_sentences(
            connection,
            second["response_id"]
        )

        first_hashes = {
            row["sentence_hash"]
            for row in first_sentences
        }

        second_hashes = {
            row["sentence_hash"]
            for row in second_sentences
        }

        retained = first_hashes & second_hashes
        removed = first_hashes - second_hashes
        added = second_hashes - first_hashes

        total_unique = len(first_hashes | second_hashes)

        overlap_pct = (
            len(retained) / total_unique * 100
            if total_unique
            else 0
        )

        change_pct = 100 - overlap_pct

        comparable += 1

        print(f"\nQUERY {query_id}")
        print("-" * 100)

        print(f"Run 1 sentences       : {len(first_sentences)}")
        print(f"Run 2 sentences       : {len(second_sentences)}")
        print(f"Retained sentences    : {len(retained)}")
        print(f"Removed sentences     : {len(removed)}")
        print(f"New sentences         : {len(added)}")
        print(f"Sentence overlap      : {overlap_pct:.1f}%")
        print(f"Content change        : {change_pct:.1f}%")

    print("\n" + "=" * 100)
    print(f"COMPARABLE QUESTIONS = {comparable}")

    connection.close()


if __name__ == "__main__":
    main()