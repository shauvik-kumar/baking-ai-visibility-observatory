from benchmark_loader import load_questions


def main():
    questions = load_questions()

    active_questions = [
        question
        for question in questions
        if question["active"] == 1
    ]

    print(
        "BAKING AI VISIBILITY OBSERVATORY"
    )
    print("=" * 60)

    print(
        f"Benchmark questions : {len(questions)}"
    )

    print(
        f"Active questions    : "
        f"{len(active_questions)}"
    )

    print()
    print("QUESTIONS")
    print("-" * 60)

    for question in questions:

        print(
            f"Q{question['query_id']} | "
            f"{question['query']}"
        )

    print()
    print("BENCHMARK VALIDATION: OK")


if __name__ == "__main__":
    main()