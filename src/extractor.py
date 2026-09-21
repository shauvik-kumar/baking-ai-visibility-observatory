import hashlib
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

def save_metrics():
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute("""
        SELECT
            response_id,
            run_id,
            query_id,
            engine,
            model,
            timestamp,
            raw_response
        FROM responses
        WHERE response_status = 'success'
          AND raw_response IS NOT NULL
        ORDER BY response_id
    """).fetchall()

    saved = 0

    for row in rows:
        (
            response_id,
            run_id,
            query_id,
            engine,
            model,
            timestamp,
            text,
        ) = row

        urls = extract_urls(text)
        headings = extract_headings(text)
        bold_phrases = extract_bold_phrases(text)
        word_count = count_words(text)
        bullet_count = count_bullets(text)

        connection.execute("""
            INSERT OR REPLACE INTO response_metrics (
                response_id,
                run_id,
                query_id,
                engine,
                model,
                timestamp,
                character_count,
                word_count,
                bullet_count,
                heading_count,
                bold_phrase_count,
                url_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            response_id,
            run_id,
            query_id,
            engine,
            model,
            timestamp,
            len(text),
            word_count,
            bullet_count,
            len(headings),
            len(bold_phrases),
            len(urls),
        ))

        saved += 1

    connection.commit()
    connection.close()

    print(f"METRICS SAVED = {saved}")

def split_sentences(text):
    """
    Simple deterministic sentence splitter for research purposes.
    Preserves the original sentence text.
    """
    if not text:
        return []

    text = text.strip()

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def save_sentences():
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute("""
        SELECT
            response_id,
            raw_response
        FROM responses
        WHERE response_status = 'success'
          AND raw_response IS NOT NULL
        ORDER BY response_id
    """).fetchall()

    saved = 0

    for response_id, text in rows:

        sentences = split_sentences(text)

        # Make the operation idempotent.
        connection.execute(
            "DELETE FROM response_sentences WHERE response_id = ?",
            (response_id,)
        )

        for index, sentence in enumerate(sentences, start=1):

            sentence_hash = hashlib.sha256(
                sentence.encode("utf-8")
            ).hexdigest()

            connection.execute("""
                INSERT INTO response_sentences (
                    response_id,
                    sentence_index,
                    sentence_text,
                    sentence_hash
                )
                VALUES (?, ?, ?, ?)
            """, (
                response_id,
                index,
                sentence,
                sentence_hash
            ))

            saved += 1

    connection.commit()
    connection.close()

    print(f"SENTENCES SAVED = {saved}")

def count_words(text):
    if not text:
        return 0

    return len(re.findall(r"\b\w+\b", text))


def count_bullets(text):
    if not text:
        return 0

    count = 0

    for line in text.splitlines():
        line = line.strip()

        if re.match(r"^[-*+]\s+", line):
            count += 1

    return count


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

        if not text:
            print("No raw response text — skipping extraction.")
            continue

        urls = extract_urls(text)
        headings = extract_headings(text)
        bold_phrases = extract_bold_phrases(text)

        word_count = count_words(text)
        bullet_count = count_bullets(text)

        print(f"\nResponse ID: {row['response_id']}")
        print(f"Query ID: {row['query_id']}")
        print(f"Model: {row['model']}")
        print(f"Characters: {len(text)}")

        print(f"Words: {word_count}")
        print(f"Bullets: {bullet_count}")

        print(f"URLs found: {len(urls)}")
        print(f"Headings found: {len(headings)}")
        print(f"Bold phrases found: {len(bold_phrases)}")

        if urls:
            print("URLs:")
            for url in urls:
                print(f"  - {url}")

    connection.close()


if __name__ == "__main__":
    save_metrics()
    save_sentences()