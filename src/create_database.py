"""Создание SQLite-базы данных из синтетических CSV-файлов."""

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATABASE_DIR = PROJECT_ROOT / "data" / "database"
DATABASE_PATH = DATABASE_DIR / "ad_card_ab_test.db"

TABLE_FILES = {
    "users": "users.csv",
    "ads": "ads.csv",
    "events": "events.csv",
    "payments": "payments.csv",
}


def read_csv_table(table_name, file_name):
    """Читает CSV-файл и сообщает понятную ошибку, если данных еще нет."""
    file_path = RAW_DATA_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(
            f"Не найден файл {file_path}. Сначала запустите: python src/generate_data.py"
        )
    return pd.read_csv(file_path)


def create_database():
    """Пересоздает SQLite-базу и загружает в нее все таблицы проекта."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        # Загрузить CSV-файлы в SQLite-таблицы.
        for table_name, file_name in TABLE_FILES.items():
            table = read_csv_table(table_name, file_name)
            table.to_sql(table_name, connection, if_exists="replace", index=False)

        # Напечатать контрольные размеры таблиц.
        print(f"SQLite-база создана: {DATABASE_PATH}")
        print("Количество строк в таблицах:")
        for table_name in TABLE_FILES:
            row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"- {table_name}: {row_count:,} строк")


def main():
    """Создает SQLite-базу из текущих raw CSV-файлов."""
    create_database()


if __name__ == "__main__":
    main()
