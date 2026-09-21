"""
Populate controlled entity observations for selected benchmark questions.

This is deliberately separate from entity_extractor.py.

entity_extractor.py
    -> experimental candidate discovery

This script
    -> controlled research observations
"""

import sqlite3

from config import DB_PATH
from entity_dictionary import get_all_aliases, get_entities_for_query


# Controlled entity types for the current research questions.
ENTITY_TYPES = {
    7: {
        "Lavonne Academy": "academy",
        "Academy of Pastry & Culinary Arts": "academy",
        "Bake with Shivesh": "baking_provider",
        "La Folie Academy": "academy",
        "Chef Sanjana Patel": "person",
        "Truffle Nation": "baking_provider",
        "Udemy": "platform",
        "Skillshare": "platform",
        "Alpa Pereira": "person",
        "Deepali Arora": "person",
        "Reema's Swad Cooking Classes": "baking_provider",
        "Truffles 'n' Hazelnut": "baking_provider",
        "Sonali Garewal": "person",
        "Anyone Can Cook with Rashmi": "baking_provider",
        "Gokul Kitchen": "baking_provider",
    },
    9: {
        "Borosil Prima 42L": "product",
        "Borosil Prima 60L": "product",
        "Borosil PRO 30L": "product",
        "Borosil PRO 60L": "product",
        "Philips HD6976/00": "product",
        "Agaro Marvel 28L": "product",
        "Agaro Grand 40L / 48L": "product",
        "Bajaj Majestic 28L": "product",
        "Morphy Richards 52RCSS": "product",
        "Morphy Richards 60L (Besto / RCSS)": "product",
        "Morphy Richards Bestron 60RCSS": "product",
        "IFB 30L Convection Microwave": "product",
        "Samsung 28L Convection Microwave": "product",
    },
}


TARGET_QUERY_IDS = [7, 9]


def find_aliases(text, alias_map):
    """
    Find controlled entity aliases in the raw response.

    Matching is case-insensitive, but the returned entity_text is the
    exact substring as it appeared in the raw response.

    Longer aliases are preferred so compound mentions such as
    "Agaro Grand 40L / 48L OTG" are captured as one observation.
    """
    if not text:
        return []

    matches = []

    # Longest aliases first prevents shorter aliases from being
    # selected inside a longer, more specific entity mention.
    sorted_aliases = sorted(
        alias_map.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias_lower, canonical_entity in sorted_aliases:
        start = 0

        while True:
            position = text.lower().find(alias_lower, start)

            if position == -1:
                break

            end = position + len(alias_lower)

            # Preserve the exact wording from the raw response.
            observed_text = text[position:end]

            matches.append(
                (
                    position,
                    end,
                    observed_text,
                    canonical_entity,
                )
            )

            start = end

    # Earlier position first; for overlapping matches, longer match first.
    matches.sort(
        key=lambda item: (
            item[0],
            -(item[1] - item[0]),
        )
    )

    # Remove overlapping matches.
    selected = []
    occupied_until = -1

    for match in matches:
        position, end, observed_text, canonical_entity = match

        if position < occupied_until:
            continue

        selected.append(match)
        occupied_until = end

    return selected


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        DELETE FROM response_entities_observed
        WHERE query_id IN (?, ?)
        """,
        tuple(TARGET_QUERY_IDS),
    )

    connection.commit()

    print("\nExisting Q7/Q9 controlled observations cleared.")

    total_inserted = 0

    print("\nCONTROLLED ENTITY OBSERVATIONS")
    print("=" * 90)

    for query_id in TARGET_QUERY_IDS:

        alias_map = get_all_aliases(query_id)
        entity_types = ENTITY_TYPES[query_id]

        rows = connection.execute(
            """
            SELECT response_id, query_id, raw_response
            FROM responses
            WHERE query_id = ?
              AND response_status = 'success'
              AND raw_response IS NOT NULL
            ORDER BY response_id
            """,
            (query_id,),
        ).fetchall()

        print(f"\nQUERY {query_id}")
        print("-" * 90)

        for row in rows:

            response_id = row["response_id"]
            text = row["raw_response"]

            matches = find_aliases(text, alias_map)

            # One observation per canonical entity per response.
            seen = set()

            for _, _, observed_text, canonical_entity in matches:

                if canonical_entity in seen:
                    continue

                seen.add(canonical_entity)

                entity_type = entity_types[canonical_entity]

                existing = connection.execute(
                    """
                    SELECT observation_id
                    FROM response_entities_observed
                    WHERE response_id = ?
                      AND canonical_entity = ?
                    """,
                    (
                        response_id,
                        canonical_entity,
                    ),
                ).fetchone()

                if existing:
                    continue

                connection.execute(
                    """
                    INSERT INTO response_entities_observed (
                        response_id,
                        query_id,
                        entity_text,
                        canonical_entity,
                        entity_type
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        response_id,
                        query_id,
                        observed_text,
                        canonical_entity,
                        entity_type,
                    ),
                )

                total_inserted += 1

                print(
                    f"Response {response_id}: "
                    f"{observed_text} -> "
                    f"{canonical_entity} "
                    f"[{entity_type}]"
                )

    connection.commit()

    print("\n" + "=" * 90)
    print(f"OBSERVATIONS INSERTED = {total_inserted}")

    connection.close()


if __name__ == "__main__":
    main()