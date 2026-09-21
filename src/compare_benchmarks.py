from benchmark_loader import load_questions
from questions import QUESTIONS


def main():

    csv_questions = load_questions()

    if len(csv_questions) != len(QUESTIONS):
        raise ValueError(
            "Question count mismatch: "
            f"CSV={len(csv_questions)}, "
            f"Python={len(QUESTIONS)}"
        )

    fields = [
        "category",
        "subcategory",
        "intent",
        "geography",
        "commercial_intent",
        "entity_type",
        "difficulty",
    ]

    for index, (csv_question, python_question) in enumerate(
        zip(csv_questions, QUESTIONS),
        start=1,
    ):

        if csv_question["question"] != python_question["query"]:
            raise ValueError(
                f"Question text mismatch for "
                f"Q{index}\n"
                f"CSV:    {csv_question['question']}\n"
                f"Python: {python_question['query']}"
            )

        for field in fields:

            if csv_question[field] != python_question[field]:
                raise ValueError(
                    f"{field} mismatch for Q{index}\n"
                    f"CSV:    {csv_question[field]}\n"
                    f"Python: {python_question[field]}"
                )

    print("BENCHMARK COMPARISON: EXACT MATCH")


if __name__ == "__main__":
    main()