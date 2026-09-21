import sqlite3

from config import DB_PATH


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    runs = connection.execute(
        """
        SELECT
            COUNT(*) AS total_runs,
            SUM(
                CASE WHEN status = 'completed'
                THEN 1 ELSE 0 END
            ) AS completed_runs,
            SUM(
                CASE WHEN status = 'partial'
                THEN 1 ELSE 0 END
            ) AS partial_runs
        FROM runs
        """
    ).fetchone()

    questions = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM queries
        WHERE active = 1
        """
    ).fetchone()

    responses = connection.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE WHEN response_status = 'success'
                THEN 1 ELSE 0 END
            ) AS successful,
            SUM(
                CASE WHEN response_status = 'error'
                THEN 1 ELSE 0 END
            ) AS errors
        FROM responses
        """
    ).fetchone()

    print("\nBAKING AI VISIBILITY OBSERVATORY")
    print("=" * 60)

    print(f"Active benchmark questions : {questions['total']}")
    print(f"Total experiment runs      : {runs['total_runs']}")
    print(f"Completed runs             : {runs['completed_runs'] or 0}")
    print(f"Partial runs               : {runs['partial_runs'] or 0}")

    print("\nOBSERVATIONS")
    print("-" * 60)
    print(f"Total responses            : {responses['total']}")
    print(f"Successful responses       : {responses['successful'] or 0}")
    print(f"Error responses            : {responses['errors'] or 0}")

    print("\nDATA LAYERS")
    print("-" * 60)
    print("Raw responses              : YES")
    print("Historical preservation    : YES")
    print("Run IDs                    : YES")
    print("Experiment versioning      : YES")
    print("Run comparison             : YES")
    print("CSV export                 : YES")
    print("Entity extraction          : EXPERIMENTAL")

    connection.close()


if __name__ == "__main__":
    main()