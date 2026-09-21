import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = PROJECT_ROOT / "benchmark" / "questions.csv"


REQUIRED_COLUMNS = [
    "question_id",
    "question",
    "category",
    "subcategory",
    "intent",
    "geography",
    "commercial_intent",
    "entity_type",
    "difficulty",
    "active",
]


def load_questions(path=BENCHMARK_PATH):
    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(
                "Benchmark columns do not match "
                "the required schema.\n"
                f"Expected: {REQUIRED_COLUMNS}\n"
                f"Found: {reader.fieldnames}"
            )

        questions = []

        for row in reader:

            question_id = int(row["question_id"])
            active = int(row["active"])

            if active not in (0, 1):
                raise ValueError(
                    f"Invalid active value for "
                    f"question {question_id}"
                )

            questions.append(
                {
                    "query_id": question_id,
                    "query": row["question"],
                    "category": row["category"],
                    "subcategory": row["subcategory"],
                    "intent": row["intent"],
                    "geography": row["geography"],
                    "commercial_intent": row[
                        "commercial_intent"
                    ],
                    "entity_type": row["entity_type"],
                    "difficulty": row["difficulty"],
                    "active": active,
                }
            )

    validate_questions(questions)

    return questions


def validate_questions(questions):

    if not questions:
        raise ValueError(
            "Benchmark contains no questions."
        )

    question_ids = [
        question["query_id"]
        for question in questions
    ]

    if len(question_ids) != len(set(question_ids)):
        raise ValueError(
            "Duplicate question_id found."
        )

    question_texts = [
        question["query"].strip()
        for question in questions
    ]

    if len(question_texts) != len(
        set(question_texts)
    ):
        raise ValueError(
            "Duplicate question text found."
        )

    for question in questions:

        if not question["query"].strip():
            raise ValueError(
                f"Empty question for "
                f"question_id {question['query_id']}"
            )


def get_active_questions():

    return [
        question
        for question in load_questions()
        if question["active"] == 1
    ]