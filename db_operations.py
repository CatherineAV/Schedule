import sqlite3
from typing import List, Dict, Any


def get_table_data(table_name: str, db_name="schedule.db") -> List[Dict[str, Any]]:
    """Получить все данные из указанной таблицы"""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Ошибка при чтении таблицы {table_name}: {e}")
        return []
    finally:
        conn.close()


def get_table_columns(table_name: str, db_name="schedule.db") -> List[str]:
    """Получить названия колонок таблицы"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        return columns
    except sqlite3.Error as e:
        print(f"Ошибка при получении колонок таблицы {table_name}: {e}")
        return []
    finally:
        conn.close()


def insert_data(table_name: str, data: Dict[str, Any], db_name="schedule.db") -> bool:
    """Вставить данные в таблицу"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())

        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при вставке данных в таблицу {table_name}: {e}")
        return False
    finally:
        conn.close()
