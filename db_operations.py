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


# В db_operations.py добавим функцию
def insert_group_with_subgroups(group_data, subgroups, db_name="schedule.db"):
    """Вставить группу и её подгруппы"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Вставляем группу
        cursor.execute(
            "INSERT INTO Группы (Название, Самообразование, [Разговоры о важном]) VALUES (?, ?, ?)",
            (group_data['Название'], group_data.get('Самообразование'), group_data.get('Разговоры о важном', 0))
        )

        group_id = cursor.lastrowid

        # Вставляем подгруппы
        for subgroup in subgroups:
            cursor.execute(
                "INSERT INTO Подгруппы (ГруппаID, Название) VALUES (?, ?)",
                (group_id, subgroup)
            )

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении группы: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_groups_with_subgroups(db_name="schedule.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    query = """
        SELECT g.ID, g.Название, g.Самообразование, g.[Разговоры о важном],
               s.Название as Подгруппа
        FROM Группы g
        LEFT JOIN Подгруппы s ON g.ID = s.ГруппаID
        ORDER BY g.ID
        """
    cursor.execute(query)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        group_name = row[1]
        self_edu = row[2] if row[2] else "Нет"
        talks = "Да" if row[3] else "Нет"
        subgroup = row[4] if row[4] else "Нет"

        result.append({
            "Название": group_name,
            "Подгруппа": subgroup,
            "Самообразование": self_edu,
            "Разговоры о важном": talks
        })

    conn.close()
    return result
