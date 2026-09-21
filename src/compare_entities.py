"""
Compare controlled entity visibility between the first two observations
of Q7 and Q9.

This measures entity-set change only.
It does not assign a subjective volatility score.
"""

import sqlite3

from config import DB_PATH


TARGET_QUERY_IDS = [7, 9]


def get_response_entities(connection, query_id):
    rows = connection.execute(
        """
        SELECT
            response_id,
            canonical_entity,
            entity_type
        FROM response_entities_observed
        WHERE query_id = ?
        ORDER BY response_id, observation_id
        """,
        (query_id,),
    ).fetchall()

    by_response = {}

    for row in rows:
        response_id = row[0]

        if response_id not in by_response:
            by_response[response_id] = {}

        by_response[response_id][row[1]] = row[2]

    return by_response


def compare_entities(run1, run2):
    entities1 = set(run1.keys())
    entities2 = set(run2.keys())

    retained = sorted(entities1 & entities2)
    removed = sorted(entities1 - entities2)
    added = sorted(entities2 - entities1)

    return retained, removed, added


def print_entity_list(title, entities, entity_map):
    print(f"\n{title} ({len(entities)})")

    if not entities:
        print("  None")
        return

    for entity in entities:
        print(f"  - {entity} [{entity_map[entity]}]")


def main():
    connection = sqlite3.connect(DB_PATH)

    print("\nCONTROLLED ENTITY COMPARISON")
    print("=" * 90)

    for query_id in TARGET_QUERY_IDS:

        responses = get_response_entities(connection, query_id)

        print(f"\nQUERY {query_id}")
        print("-" * 90)

        response_ids = sorted(responses.keys())

        if len(response_ids) < 2:
            print("Not enough responses for comparison.")
            continue

        response1_id = response_ids[0]
        response2_id = response_ids[1]

        run1 = responses[response1_id]
        run2 = responses[response2_id]

        retained, removed, added = compare_entities(run1, run2)

        print(f"Response 1: {response1_id}")
        print(f"Response 2: {response2_id}")

        print(f"\nEntity count — Response 1: {len(run1)}")
        print(f"Entity count — Response 2: {len(run2)}")

        print_entity_list(
            "RETAINED",
            retained,
            run1,
        )

        print_entity_list(
            "REMOVED FROM RESPONSE 2",
            removed,
            run1,
        )

        print_entity_list(
            "ADDED IN RESPONSE 2",
            added,
            run2,
        )

        total_unique = len(entities := set(run1) | set(run2))

        if total_unique:
            retention_pct = len(retained) / total_unique * 100
            changed_pct = (
                (len(removed) + len(added))
                / total_unique
                * 100
            )
        else:
            retention_pct = 0
            changed_pct = 0

        print("\nSET COMPARISON")
        print(f"  Unique entities across both responses: {total_unique}")
        print(f"  Retained entities: {len(retained)}")
        print(f"  Removed entities: {len(removed)}")
        print(f"  Added entities: {len(added)}")
        print(f"  Retained / union: {retention_pct:.1f}%")
        print(f"  Added + removed / union: {changed_pct:.1f}%")

    connection.close()


if __name__ == "__main__":
    main()