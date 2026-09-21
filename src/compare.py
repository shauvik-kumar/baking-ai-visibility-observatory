from database import get_connection


def show_run_history():
    connection = get_connection()

    runs = connection.execute(
        """
        SELECT
            run_id,
            started_at,
            completed_at,
            status,
            question_count
        FROM runs
        ORDER BY started_at
        """
    ).fetchall()

    print("\nRUN HISTORY")
    print("=" * 80)

    for run in runs:
        print(
            f"{run['started_at']} | "
            f"{run['status']} | "
            f"{run['question_count']} questions | "
            f"{run['run_id']}"
        )

    responses = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM responses
        """
    ).fetchone()

    print("\nTOTAL RESPONSES:", responses["total"])

    connection.close()


if __name__ == "__main__":
    show_run_history()