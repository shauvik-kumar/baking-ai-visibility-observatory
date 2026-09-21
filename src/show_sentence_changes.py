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
            response_id,
            query_id,
            run_id
        FROM responses
        WHERE engine = 'gemini'
          AND response_status = 'success'
          AND raw_response IS NOT NULL
        ORDER BY query_id, response_id
        """
    ).fetchall()

    grouped = {}

    for row in rows:
        grouped.setdefault(row["query_id"], []).append(row)

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

        first_by_hash = {
            row["sentence_hash"]: row["sentence_text"]
            for row in first_sentences
        }

        second_by_hash = {
            row["sentence_hash"]: row["sentence_text"]
            for row in second_sentences
        }

        removed = [
            text
            for sentence_hash, text in first_by_hash.items()
            if sentence_hash not in second_by_hash
        ]

        added = [
            text
            for sentence_hash, text in second_by_hash.items()
            if sentence_hash not in first_by_hash
        ]

        print("\n" + "=" * 100)
        print(f"QUERY {query_id}")
        print("=" * 100)

        print("\nREMOVED / NOT REPEATED IN RUN 2")
        print("-" * 100)

        for sentence in removed:
            print(f"- {sentence}")

        print("\nADDED / NEW IN RUN 2")
        print("-" * 100)

        for sentence in added:
            print(f"+ {sentence}")

    connection.close()


if __name__ == "__main__":
    main()