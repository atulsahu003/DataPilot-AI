
from app.services.data_profiling import profile_csv


def test_profile_csv():
    file_path = "data/sample/students.csv"

    result = profile_csv(file_path)

    print("CSV profile:")
    print(result)


if __name__ == "__main__":
    test_profile_csv()
