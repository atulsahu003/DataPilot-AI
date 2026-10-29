
from app.database.connection import get_db_connection


def test_database_connection():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_user"
            )
            result = cursor.fetchone()

        print("Database connection successful!")
        print("Database:", result[0])
        print("User:", result[1])

    finally:
        connection.close()


if __name__ == "__main__":
    test_database_connection()
