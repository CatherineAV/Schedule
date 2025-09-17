import sqlite3
from typing import List, Dict, Any
from .core import Database


class DBOperations:
    def __init__(self, db_name: str = "schedule.db"):
        self.db = Database(db_name)

    def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        return self.db.execute_query(f"SELECT * FROM {table_name}")

    def get_table_columns(self, table_name: str) -> List[str]:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [column[1] for column in cursor.fetchall()]
        finally:
            conn.close()

    def insert_data(self, table_name: str, data: Dict[str, Any]) -> bool:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.db.execute_command(query, values)

    def delete_record(self, table_name: str, record_id: int) -> bool:
        return self.db.execute_command(f"DELETE FROM {table_name} WHERE ID = ?", (record_id,))

    def get_groups_with_subgroups(self) -> List[Dict[str, Any]]:
        query = """
        SELECT g.ID, g.Название, g.Самообразование, g.[Разговоры о важном],
               s.Название as Подгруппа
        FROM Группы g
        LEFT JOIN Подгруппы s ON g.ID = s.ГруппаID
        ORDER BY g.ID
        """

        rows = self.db.execute_query(query)
        result = []

        for row in rows:
            result.append({
                "ID": row['ID'],  # Добавляем ID
                "Название": row['Название'],
                "Подгруппа": row['Подгруппа'] if row['Подгруппа'] else "Нет",
                "Самообразование": row['Самообразование'] if row['Самообразование'] else "Нет",
                "Разговоры о важном": "Да" if row['Разговоры о важном'] else "Нет"
            })

        return result

    def insert_group_with_subgroups(self, group_data: Dict[str, Any], subgroups: List[str]) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Проверка на существующие записи (без учета регистра)
            existing_groups = self.get_groups_with_subgroups()
            group_name = group_data['Название']

            # Проверяем, есть ли уже такая группа (без учета регистра)
            group_exists = any(existing['Название'].upper() == group_name.upper() for existing in existing_groups)

            if group_exists:
                # Получаем все подгруппы этой группы (без учета регистра названия группы)
                existing_subgroups = [existing['Подгруппа'] for existing in existing_groups
                                      if existing['Название'].upper() == group_name.upper()]

                # Если у группы уже есть подгруппа "Нет" - нельзя добавлять другие подгруппы
                if "Нет" in existing_subgroups:
                    return False

                # Если пытаемся добавить "Нет" к группе, у которой уже есть другие подгруппы
                if "Нет" in subgroups:
                    return False

                # Проверяем, не пытаемся ли добавить уже существующую подгруппу
                for subgroup in subgroups:
                    if subgroup in existing_subgroups:
                        return False

            # Если проверки пройдены, вставляем данные
            cursor.execute(
                "INSERT INTO Группы (Название, Самообразование, [Разговоры о важном]) VALUES (?, ?, ?)",
                (group_data['Название'], group_data.get('Самообразование'), group_data.get('Разговоры о важном', 0))
            )

            group_id = cursor.lastrowid

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

    def delete_group_with_subgroups(self, group_name: str, subgroup_name: str) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT ID FROM Группы WHERE Название = ?", (group_name,))
            group_result = cursor.fetchone()

            if not group_result:
                return False

            group_id = group_result[0]
            cursor.execute("DELETE FROM Подгруппы WHERE ГруппаID = ? AND Название = ?", (group_id, subgroup_name))

            cursor.execute("SELECT COUNT(*) FROM Подгруппы WHERE ГруппаID = ?", (group_id,))
            remaining_subgroups = cursor.fetchone()[0]

            if remaining_subgroups == 0:
                cursor.execute("DELETE FROM Группы WHERE ID = ?", (group_id,))

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при удалении группы: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_record(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Обновляет запись в таблице"""
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        values.append(record_id)

        query = f"UPDATE {table_name} SET {set_clause} WHERE ID = ?"
        return self.db.execute_command(query, values)

    def update_group_with_subgroups(self, group_id: int, group_data: Dict[str, Any], subgroups: List[str]) -> bool:
        """Обновляет группу и подгруппы"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Обновляем данные группы
            cursor.execute(
                "UPDATE Группы SET Название = ?, Самообразование = ?, [Разговоры о важном] = ? WHERE ID = ?",
                (group_data['Название'], group_data.get('Самообразование'),
                 group_data.get('Разговоры о важном', 0), group_id)
            )

            # Удаляем старые подгруппы
            cursor.execute("DELETE FROM Подгруппы WHERE ГруппаID = ?", (group_id,))

            # Добавляем новые подгруппы
            for subgroup in subgroups:
                cursor.execute(
                    "INSERT INTO Подгруппы (ГруппаID, Название) VALUES (?, ?)",
                    (group_id, subgroup)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении группы: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
