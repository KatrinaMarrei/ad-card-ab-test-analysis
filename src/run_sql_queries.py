"""Запуск SQL-запросов к SQLite-базе и сохранение результатов в CSV."""

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "database" / "ad_card_ab_test.db"
SQL_DIR = PROJECT_ROOT / "sql"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def get_sql_files():
    """Возвращает SQL-файлы в порядке выполнения."""
    return sorted(SQL_DIR.glob("*.sql"))


def execute_query(connection, sql_path):
    """Выполняет один SQL-файл и возвращает результат как DataFrame."""
    query = sql_path.read_text(encoding="utf-8")
    return pd.read_sql_query(query, connection)


def save_query_result(result, sql_path):
    """Сохраняет результат запроса в data/processed с тем же номером и именем."""
    output_path = PROCESSED_DATA_DIR / f"{sql_path.stem}.csv"
    result.to_csv(output_path, index=False)
    print(f"{output_path.name}: сохранено {result.shape[0]} строк и {result.shape[1]} столбцов")


def run_sql_queries():
    """Запускает все SQL-запросы проекта и сохраняет их результаты."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Не найдена база данных {DATABASE_PATH}. Сначала запустите: python src/create_database.py"
        )

    sql_files = get_sql_files()
    if not sql_files:
        raise FileNotFoundError(f"В папке {SQL_DIR} не найдены SQL-файлы.")

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        # Выполнить SQL-файлы в порядке их номеров.
        for sql_path in sql_files:
            try:
                result = execute_query(connection, sql_path)
                save_query_result(result, sql_path)
            except Exception as error:
                raise RuntimeError(f"Ошибка при выполнении запроса {sql_path.name}: {error}") from error


def main():
    """Запускает SQL-пайплайн и печатает понятную ошибку при сбое."""
    try:
        run_sql_queries()
    except Exception as error:
        print(error)
        raise


if __name__ == "__main__":
    main()
