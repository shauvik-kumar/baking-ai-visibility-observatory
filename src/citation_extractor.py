import re
import sqlite3
from urllib.parse import urlparse

from config import DB_PATH


URL_PATTERN = re.compile(
    r"https?://[^\s<>\[\]()\"]+"
)


MARKDOWN_LINK_PATTERN = re.compile(
    r"\[[^\]]+\]\((https?://[^)\s]+)\)"
)


def clean_url(url):
    """
    Remove punctuation that commonly follows a URL in prose.
    """

    return url.rstrip(
        ".,;:!?)]}>\"'"
    )


def extract_urls(text):
    """
    Extract only explicit HTTP/HTTPS URLs.

    This deliberately does NOT infer websites from names
    or domains mentioned in prose.
    """

    if not text:
        return []

    urls = []

    # Markdown links
    for match in MARKDOWN_LINK_PATTERN.finditer(text):
        urls.append(clean_url(match.group(1)))

    # Plain URLs
    for match in URL_PATTERN.finditer(text):
        urls.append(clean_url(match.group(0)))

    # Preserve order while removing duplicates
    seen = set()
    unique_urls = []

    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def get_domain(url):
    """
    Extract hostname from a URL.
    """

    parsed = urlparse(url)

    return parsed.netloc.lower()


def get_successful_responses(conn):
    return conn.execute(
        """
        SELECT
            response_id,
            raw_response
        FROM responses
        WHERE response_status = 'success'
          AND raw_response IS NOT NULL
        ORDER BY response_id
        """
    ).fetchall()


def get_or_create_citation(
    conn,
    url,
    timestamp,
):
    existing = conn.execute(
        """
        SELECT citation_id
        FROM citations
        WHERE url = ?
        """,
        (url,),
    ).fetchone()

    if existing:
        citation_id = existing[0]

        conn.execute(
            """
            UPDATE citations
            SET last_seen_at = ?
            WHERE citation_id = ?
            """,
            (
                timestamp,
                citation_id,
            ),
        )

        return citation_id

    domain = get_domain(url)

    cursor = conn.execute(
        """
        INSERT INTO citations (
            url,
            domain,
            title,
            first_seen_at,
            last_seen_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            url,
            domain,
            None,
            timestamp,
            timestamp,
        ),
    )

    return cursor.lastrowid


def extract_and_store():
    conn = sqlite3.connect(DB_PATH)

    total_responses = 0
    responses_with_urls = 0
    total_urls = 0

    try:
        responses = get_successful_responses(conn)

        for response_id, raw_response in responses:

            total_responses += 1

            urls = extract_urls(raw_response)

            if urls:
                responses_with_urls += 1

            total_urls += len(urls)

            timestamp = conn.execute(
                """
                SELECT timestamp
                FROM responses
                WHERE response_id = ?
                """,
                (response_id,),
            ).fetchone()[0]

            for position, url in enumerate(urls):

                citation_id = get_or_create_citation(
                    conn,
                    url,
                    timestamp,
                )

                existing_link = conn.execute(
                    """
                    SELECT 1
                    FROM response_citations
                    WHERE response_id = ?
                      AND citation_id = ?
                      AND position = ?
                    """,
                    (
                        response_id,
                        citation_id,
                        position,
                    ),
                ).fetchone()

                if not existing_link:

                    conn.execute(
                        """
                        INSERT INTO response_citations (
                            response_id,
                            citation_id,
                            position
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            response_id,
                            citation_id,
                            position,
                        ),
                    )

        conn.commit()

    finally:
        conn.close()

    print("CITATION EXTRACTION COMPLETE")
    print("=" * 60)
    print(
        f"Successful responses : {total_responses}"
    )
    print(
        f"Responses with URLs  : {responses_with_urls}"
    )
    print(
        f"URLs extracted       : {total_urls}"
    )


if __name__ == "__main__":
    extract_and_store()