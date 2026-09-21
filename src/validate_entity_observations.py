"""
Validate controlled entity observations against raw responses.

Read-only research QA:
- Checks every stored observation exists in the corresponding raw response.
- Reports any false positives.
- Reports controlled entities that were expected but not observed.
"""

import sqlite3

from config import DB_PATH
from entity_dictionary import get_entities_for_query


TARGET_QUERY_IDS = [7, 9]


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    total_checked = 0
    false_positives = 0

    print("\nENTITY OBSERVATION VALIDATION")
    print("=" * 90)

    for query_id in TARGET_QUERY_IDS:

        print(f"\nQUERY {query_id}")
        print("-" * 90)

        responses = connection.execute(
            """
            SELECT response_id, raw_response
            FROM responses
            WHERE query_id = ?
              AND response_status = 'success'
              AND raw_response IS NOT NULL
            ORDER BY response_id
            """,
            (query_id,),
        ).fetchall()

        dictionary = get_entities_for_query(query_id)

        for response in responses:

            response_id = response["response_id"]
            raw_text = response["raw_response"].lower()

            observations = connection.execute(
                """
                SELECT
                    entity_text,
                    canonical_entity
                FROM response_entities_observed
                WHERE response_id = ?
                ORDER BY observation_id
                """,
                (response_id,),
            ).fetchall()

            print(f"\nResponse {response_id}")

            # Validate stored observations.
            for observation in observations:

                entity_text = observation["entity_text"]
                canonical = observation["canonical_entity"]

                total_checked += 1

                if entity_text.lower() in raw_text:
                    print(f"  OK       | {entity_text} -> {canonical}")
                else:
                    print(
                        f"  FALSE    | {entity_text} -> {canonical}"
                    )
                    false_positives += 1

            # Determine which controlled entities are actually present
            # but have no stored observation.
            observed_canonicals = {
                row["canonical_entity"]
                for row in observations
            }

            missing_observations = []

            for canonical, aliases in dictionary.items():

                if canonical in observed_canonicals:
                    continue

                matched_alias = None

                for alias in aliases:
                    if alias.lower() in raw_text:
                        matched_alias = alias
                        break

                if matched_alias:
                    missing_observations.append(
                        (canonical, matched_alias)
                    )

            if missing_observations:
                print("  MISSING OBSERVATION:")
                for canonical, alias in missing_observations:
                    print(
                        f"    {alias} -> {canonical}"
                    )

    print("\n" + "=" * 90)
    print(f"OBSERVATIONS CHECKED = {total_checked}")
    print(f"FALSE POSITIVES      = {false_positives}")

    connection.close()


if __name__ == "__main__":
    main()