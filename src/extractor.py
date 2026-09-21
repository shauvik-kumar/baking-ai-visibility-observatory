import re
import sqlite3

from config import DB_PATH


URL_PATTERN = re.compile(
    r"https?://[^\s)\]>]+",
    re.IGNORECASE,
)


def clean_url(url):
    return url.rstrip(".,;:!?)]}")


def extract_urls(text):
    if not text:
        return []

    urls = URL_PATTERN.findall(text)

    # Preserve order while removing duplicates.
    seen = set()
    result = []

    for url in urls:
        url = clean_url(url)

        if url not in seen:
            seen.add(url)
            result.append(url)

    return result


def extract_headings(text):
    if not text:
        return []

    headings = []

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("#"):
            heading = re.sub(r"^#+\s*", "", line).strip()

            if heading:
                headings.append(heading)

    return headings


def extract_bold_phrases(text):
    if not text:
        return []

    phrases = re.findall(r"\*\*(.+?)\*\*", text)

    seen = set()
    result = []

    for phrase in phrases:
        phrase = phrase.strip()

        if phrase and phrase not in seen:
            seen.add(phrase)
            result.append(phrase)

    return result


def inspect_responses():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            response_id,
            run_id,
            query_id,
            engine,
            model,
            timestamp,
            response_status,
            raw_response
        FROM responses
        WHERE response_status = 'success'
        ORDER BY response_id
        """
    ).fetchall()

    print(f"Successful responses found: {len(rows)}")
    print("=" * 80)

    for row in rows:
        text = row["raw_response"]

        urls = extract_urls(text)
        headings = extract_headings(text)
        bold_phrases = extract_bold_phrases(text)

        print(f"\nResponse ID: {row['response_id']}")
        print(f"Query ID: {row['query_id']}")
        print(f"Model: {row['model']}")
        print(f"Characters: {len(text)}")
        print(f"URLs found: {len(urls)}")
        print(f"Headings found: {len(headings)}")
        print(f"Bold phrases found: {len(bold_phrases)}")

        if urls:
            print("URLs:")
            for url in urls:
                print(f"  - {url}")

    connection.close()


if __name__ == "__main__":
    inspect_responses()