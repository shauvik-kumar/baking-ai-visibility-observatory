import argparse
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone

from config import DB_PATH, GEMINI_MODEL
from openrouter_adapter import OPENROUTER_MODEL
from database import initialize_database

from experiment import (
    EXPERIMENT_ID,
    EXPERIMENT_VERSION,
    QUESTION_SET_VERSION,
    PROMPT_MODE,
)

from gemini_adapter import ask_gemini
from openrouter_adapter import ask_openrouter
from benchmark_loader import get_active_questions


ENGINE = os.getenv("OBSERVATORY_ENGINE", "gemini")


if ENGINE == "gemini":
    MODEL = GEMINI_MODEL
    ASK_ENGINE = ask_gemini

elif ENGINE == "openrouter":
    MODEL = OPENROUTER_MODEL
    ASK_ENGINE = ask_openrouter

else:
    raise RuntimeError(
        f"Unknown OBSERVATORY_ENGINE: {ENGINE}"
    )


QUESTIONS = get_active_questions()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_run(question_count=None):
    run_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO runs (
            run_id,
            started_at,
            status,
            question_count,
            experiment_id,
            experiment_version,
            question_set_version,
            prompt_mode,
            engine,
            model
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            utc_now(),
            "running",
            (
                question_count
                if question_count is not None
                else len(QUESTIONS)
            ),
            EXPERIMENT_ID,
            EXPERIMENT_VERSION,
            QUESTION_SET_VERSION,
            PROMPT_MODE,
            ENGINE,
            MODEL,
        ),
    )

    conn.commit()
    conn.close()

    return run_id


def get_completed_query_ids(run_id):
    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute(
        """
        SELECT query_id
        FROM responses
        WHERE run_id = ?
          AND response_status = 'success'
        """,
        (run_id,),
    ).fetchall()

    conn.close()

    return {row[0] for row in rows}


def get_or_create_run(question_count=None):
    """
    Create a new run for the current engine/model.
    """

    run_id = create_run(question_count)

    print(f"NEW RUN = {run_id}")

    return run_id


def save_response(
    run_id,
    query_id,
    status,
    latency_ms,
    raw_response,
    raw_interaction,
    error_message,
):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO responses (
            run_id,
            query_id,
            engine,
            model,
            timestamp,
            response_status,
            latency_ms,
            raw_response,
            raw_interaction,
            error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            query_id,
            ENGINE,
            MODEL,
            utc_now(),
            status,
            latency_ms,
            raw_response,
            raw_interaction,
            error_message,
        ),
    )

    conn.commit()
    conn.close()


def update_run_status(run_id, status):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        UPDATE runs
        SET
            status = ?,
            completed_at = ?
        WHERE run_id = ?
        """,
        (
            status,
            utc_now(),
            run_id,
        ),
    )

    conn.commit()
    conn.close()


def run(limit=None):
    initialize_database()

    questions = QUESTIONS[:limit] if limit else QUESTIONS

    run_id = get_or_create_run(
        question_count=len(questions)
    )

    completed_query_ids = get_completed_query_ids(run_id)

    print(
        f"EXPERIMENT = {EXPERIMENT_ID} "
        f"v{EXPERIMENT_VERSION}"
    )

    print(
        f"ENGINE = {ENGINE}"
    )

    print(
        f"MODEL = {MODEL}"
    )

    print(
        f"QUESTION SET = {QUESTION_SET_VERSION}"
    )

    print(
        f"QUESTIONS SELECTED = {len(questions)}"
    )

    print(
        f"QUESTIONS ALREADY COMPLETED = "
        f"{len(completed_query_ids)}"
    )

    run_had_error = False

    for question in questions:

        query_id = question["query_id"]

        if query_id in completed_query_ids:
            print(
                f"SKIP — ALREADY COMPLETE | "
                f"Q{query_id} | {question['query']}"
            )
            continue

        print()

        print(
            f"RUNNING | Q{query_id} | "
            f"{question['query']}"
        )

        result = ASK_ENGINE(question["query"])

        save_response(
            run_id=run_id,
            query_id=query_id,
            status=result["status"],
            latency_ms=result["latency_ms"],
            raw_response=result["text"],
            raw_interaction=result["raw_interaction"],
            error_message=result["error"],
        )

        if result["status"] == "success":

            print(
                f"SUCCESS | Q{query_id} | "
                f"{result['latency_ms']} ms"
            )

        else:

            run_had_error = True

            print(
                f"ERROR | Q{query_id} | "
                f"{result['error_type']}"
            )

            if result["error_type"] == "rate_limit":

                print()

                print(
                    "RATE LIMIT REACHED — "
                    "stopping run safely."
                )

                rate_limit = True

                break

        time.sleep(1)

    if run_had_error:

        update_run_status(
            run_id,
            "partial"
        )

        print()

        print("RUN STATUS = PARTIAL")
        print("Completed observations have been preserved.")
        print("The next run can resume this run.")

    else:

        update_run_status(
            run_id,
            "completed"
        )

        print()

        print("RUN STATUS = COMPLETED")

    print()

    print(f"RUN ID = {run_id}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of benchmark questions to run.",
    )

    args = parser.parse_args()

    run(limit=args.limit)