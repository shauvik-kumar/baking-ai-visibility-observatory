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
    """
    Load benchmark questions from CSV.

    Returns a list of dictionaries.
    """

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
                "Benchmark columns do not match the "
                f"required schema.\n"
                f"Expected: {REQUIRED_COLUMNS}\n"
                f"Found: {reader.fieldnames}"
            )

        questions = []

        for row in reader:

            row["question_id"] = int(
                row["question_id"]
            )

            row["active"] = int(
                row["active"]
            )

            if row["active"] not in (0, 1):
                raise ValueError(
                    f"Invalid active value for "
                    f"question {row['question_id']}"
                )

            questions.append(row)

    validate_questions(questions)

    return questions


def validate_questions(questions):
    """
    Validate benchmark integrity.
    """

    if not questions:
        raise ValueError(
            "Benchmark contains no questions."
        )

    question_ids = [
        question["question_id"]
        for question in questions
    ]

    if len(question_ids) != len(set(question_ids)):
        raise ValueError(
            "Duplicate question_id found."
        )

    question_texts = [
        question["question"].strip()
        for question in questions
    ]

    if len(question_texts) != len(
        set(question_texts)
    ):
        raise ValueError(
            "Duplicate question text found."
        )

    for question in questions:

        if not question["question"].strip():
            raise ValueError(
                f"Empty question for "
                f"question_id {question['question_id']}"
            )


def get_active_questions():
    """
    Return only active benchmark questions.
    """

    return [
        question
        for question in load_questions()
        if question["active"] == 1
    ]