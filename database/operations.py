import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from .core import Database


class DBOperations:
    def __init__(self, db_name: str = "schedule.db"):
        self.db = Database(db_name)

    def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            return self.db.execute_query(f"SELECT * FROM {table_name}")
        except Exception as e:
            print(f"Ошибка при получении данных из таблицы {table_name}: {e}")
            return []

    def get_table_columns(self, table_name: str) -> List[str]:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [column[1] for column in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении колонок таблицы {table_name}: {e}")
            return []
        finally:
            conn.close()

    def insert_data(self, table_name: str, data: Dict[str, Any]) -> bool:
        try:
            clean_data = {k: v for k, v in data.items() if k.upper() != 'ID'}

            if not clean_data:
                return False

            columns = ', '.join(clean_data.keys())
            placeholders = ', '.join(['?' for _ in clean_data])
            values = list(clean_data.values())

            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            return self.db.execute_command(query, values)
        except Exception as e:
            print(f"Ошибка при вставке данных в таблицу {table_name}: {e}")
            return False

    def delete_record(self, table_name: str, record_id: int) -> bool:
        try:
            return self.db.execute_command(f"DELETE FROM {table_name} WHERE ID = ?", (record_id,))
        except Exception as e:
            print(f"Ошибка при удалении записи из таблицы {table_name}: {e}")
            return False

    def update_record(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        try:
            clean_data = {k: v for k, v in data.items() if k.upper() != 'ID'}

            if not clean_data:
                return False

            set_clause = ', '.join([f"{key} = ?" for key in clean_data.keys()])
            values = list(clean_data.values())
            values.append(record_id)

            query = f"UPDATE {table_name} SET {set_clause} WHERE ID = ?"
            return self.db.execute_command(query, values)
        except Exception as e:
            print(f"Ошибка при обновлении записи в таблице {table_name}: {e}")
            return False

    # ========== ГРУППЫ ==========
    def get_groups(self) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT ID, Группа, Подгруппа, Самообразование, [Разговоры о важном] 
            FROM Группы 
            ORDER BY Группа, Подгруппа
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении групп: {e}")
            return []

    def insert_group(self, group_data: Dict[str, Any]) -> bool:
        try:
            group_name = group_data['Группа']
            subgroup = group_data.get('Подгруппа', 'Нет')

            if ("ХКО" in group_name.upper() or "ХБО" in group_name.upper()):
                if subgroup == "Нет":
                    return False
            else:
                existing_groups = self.db.execute_query(
                    "SELECT Подгруппа FROM Группы WHERE Группа = ?",
                    (group_name,)
                )

                for existing in existing_groups:
                    existing_subgroup = existing['Подгруппа']

                    if subgroup == "Нет" and existing_subgroup != "Нет":
                        return False
                    elif subgroup != "Нет" and existing_subgroup == "Нет":
                        return False
                    elif subgroup == existing_subgroup:
                        return False

            existing_same = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Группы WHERE Группа = ? AND Подгруппа = ?",
                (group_name, subgroup)
            )

            if existing_same and existing_same[0]['count'] > 0:
                return False

            return self.db.execute_command(
                "INSERT INTO Группы (Группа, Подгруппа, Самообразование, [Разговоры о важном]) VALUES (?, ?, ?, ?)",
                (
                    group_data['Группа'],
                    group_data.get('Подгруппа', 'Нет'),
                    group_data.get('Самообразование'),
                    group_data.get('Разговоры о важном', 0)
                )
            )
        except Exception as e:
            print(f"Ошибка при добавлении группы: {e}")
            return False

    def update_group(self, group_id: int, group_data: Dict[str, Any]) -> bool:
        try:
            group_name = group_data['Группа']
            subgroup = group_data.get('Подгруппа', 'Нет')

            if ("ХКО" in group_name.upper() or "ХБО" in group_name.upper()):
                if subgroup == "Нет":
                    return False
            else:
                # Проверка для обычных групп
                existing_groups = self.db.execute_query(
                    "SELECT ID, Подгруппа FROM Группы WHERE Группа = ? AND ID != ?",
                    (group_name, group_id)
                )

                for existing in existing_groups:
                    existing_subgroup = existing['Подгруппа']

                    if subgroup == "Нет" and existing_subgroup != "Нет":
                        return False
                    elif subgroup != "Нет" and existing_subgroup == "Нет":
                        return False
                    elif subgroup == existing_subgroup:
                        return False

            existing_same = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Группы WHERE Группа = ? AND Подгруппа = ? AND ID != ?",
                (group_name, subgroup, group_id)
            )

            if existing_same and existing_same[0]['count'] > 0:
                return False

            return self.db.execute_command(
                "UPDATE Группы SET Группа = ?, Подгруппа = ?, Самообразование = ?, [Разговоры о важном] = ? WHERE ID = ?",
                (
                    group_data['Группа'],
                    group_data.get('Подгруппа', 'Нет'),
                    group_data.get('Самообразование'),
                    group_data.get('Разговоры о важном', 0),
                    group_id
                )
            )
        except Exception as e:
            print(f"Ошибка при обновлении группы: {e}")
            return False

    def delete_group(self, group_id: int) -> bool:
        try:
            return self.db.execute_command("DELETE FROM Группы WHERE ID = ?", (group_id,))
        except Exception as e:
            print(f"Ошибка при удалении группы: {e}")
            return False

    def check_group_exists(self, group_name: str, subgroup: str = "Нет", exclude_id: Optional[int] = None) -> bool:
        try:
            query = """
            SELECT COUNT(*) as count FROM Группы 
            WHERE UPPER(Группа) = ? AND UPPER(Подгруппа) = ?
            """
            params = [group_name.upper(), subgroup.upper()]

            if exclude_id:
                query += " AND ID != ?"
                params.append(exclude_id)

            result = self.db.execute_query(query, tuple(params))
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования группы: {e}")
            return False

    def check_group_exists_any_subgroup(self, group_name: str, exclude_id: Optional[int] = None) -> bool:
        try:
            query = "SELECT COUNT(*) as count FROM Группы WHERE Группа = ?"
            params = [group_name]

            if exclude_id:
                query += " AND ID != ?"
                params.append(exclude_id)

            result = self.db.execute_query(query, params)
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования группы в любой подгруппе: {e}")
            return False

    # ========== МОДУЛИ ==========
    def get_modules(self) -> List[Dict[str, Any]]:
        try:
            return self.db.execute_query("SELECT ID, Код, Название FROM Модули ORDER BY Код")
        except Exception as e:
            print(f"Ошибка при получении модулей: {e}")
            return []

    def insert_module(self, code: str, name: str) -> bool:
        try:
            return self.db.execute_command(
                "INSERT INTO Модули (Код, Название) VALUES (?, ?)",
                (code, name)
            )
        except Exception as e:
            print(f"Ошибка при добавлении модуля: {e}")
            return False

    def update_module(self, module_id: int, code: str, name: str) -> bool:
        try:
            return self.db.execute_command(
                "UPDATE Модули SET Код = ?, Название = ? WHERE ID = ?",
                (code, name, module_id)
            )
        except Exception as e:
            print(f"Ошибка при обновлении модуля: {e}")
            return False

    def delete_module(self, module_id: int) -> bool:
        try:
            return self.db.execute_command("DELETE FROM Модули WHERE ID = ?", (module_id,))
        except Exception as e:
            print(f"Ошибка при удалении модуля: {e}")
            return False

    def check_module_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        try:
            if exclude_id:
                result = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM Модули WHERE Код = ? AND ID != ?",
                    (code, exclude_id)
                )
            else:
                result = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM Модули WHERE Код = ?",
                    (code,)
                )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования модуля: {e}")
            return False

    # ========== ДИСЦИПЛИНЫ ==========
    def check_subject_exists(self, name: str, module: str) -> bool:
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Дисциплины WHERE Дисциплина = ? AND Модуль = ?",
                (name, module)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования дисциплины: {e}")
            return False

    def get_subjects_with_module_names(self) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT 
                d.ID, 
                d.Дисциплина as Дисциплина, 
                d.Модуль as [Код модуля],
                m.Название as [Название модуля]
            FROM Дисциплины d
            LEFT JOIN Модули m ON d.Модуль = m.Код
            ORDER BY d.ID
            """
            subjects = self.db.execute_query(query)

            for subject in subjects:
                if subject['Код модуля'] is None:
                    subject['Код модуля'] = ''
                if subject['Название модуля'] is None:
                    subject['Название модуля'] = ''

            return subjects
        except Exception as e:
            print(f"Ошибка при получении дисциплин с модулями: {e}")
            return []

    def insert_subject_with_classrooms(self, subject_data: Dict[str, Any], classroom_ids: List[int]) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO Дисциплины (Дисциплина, Модуль) VALUES (?, ?)",
                (subject_data['Дисциплина'], subject_data['Модуль'])
            )

            subject_id = cursor.lastrowid

            for classroom_id in classroom_ids:
                cursor.execute(
                    "INSERT INTO Дисциплина_Кабинет (ДисциплинаID, КабинетID) VALUES (?, ?)",
                    (subject_id, classroom_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении дисциплины: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_subject_with_classrooms(self, subject_id: int, subject_data: Dict[str, Any],
                                       classroom_ids: List[int]) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE Дисциплины SET Дисциплина = ?, Модуль = ? WHERE ID = ?",
                (subject_data['Дисциплина'], subject_data['Модуль'], subject_id)
            )

            cursor.execute("DELETE FROM Дисциплина_Кабинет WHERE ДисциплинаID = ?", (subject_id,))

            for classroom_id in classroom_ids:
                cursor.execute(
                    "INSERT INTO Дисциплина_Кабинет (ДисциплинаID, КабинетID) VALUES (?, ?)",
                    (subject_id, classroom_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении дисциплины: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_classrooms_by_subject(self, subject_id: int) -> List[Dict[str, Any]]:
        try:
            return self.db.execute_query(
                """SELECT к.ID, к.Кабинет, т.Территория
                FROM Кабинеты к
                JOIN Дисциплина_Кабинет пк ON к.ID = пк.КабинетID
                JOIN Территории т ON к.ТерриторияID = т.ID
                WHERE пк.ДисциплинаID = ?""",
                (subject_id,)
            )
        except Exception as e:
            print(f"Ошибка при получении кабинетов по дисциплинам: {e}")
            return []

    # ========== ТЕРРИТОРИИ И КАБИНЕТЫ ==========
    def get_territories(self) -> List[Dict[str, Any]]:
        try:
            return self.db.execute_query(
                "SELECT ID, Территория, Цвет FROM Территории ORDER BY Территория")
        except Exception as e:
            print(f"Ошибка при получении территорий: {e}")
            return []

    def get_classrooms(self) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT к.ID, к.Кабинет, т.Территория
            FROM Кабинеты к
            LEFT JOIN Территории т ON к.ТерриторияID = т.ID
            ORDER BY т.Территория, к.Кабинет 
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении кабинетов: {e}")
            return []

    def get_classrooms_by_territory(self, territory_id: int) -> List[Dict[str, Any]]:
        try:
            return self.db.execute_query(
                "SELECT ID, Кабинет FROM Кабинеты WHERE ТерриторияID = ? ORDER BY Кабинет",
                (territory_id,)
            )
        except Exception as e:
            print(f"Ошибка при получении кабинетов по территории: {e}")
            return []

    def get_classroom_by_id(self, classroom_id: int) -> Optional[Dict[str, Any]]:
        try:
            result = self.db.execute_query(
                "SELECT ID, Кабинет, ТерриторияID FROM Кабинеты WHERE ID = ?",
                (classroom_id,)
            )
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении кабинета по ID: {e}")
            return None

    def check_classroom_exists(self, number: str, territory_id: int) -> bool:
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Кабинеты WHERE Кабинет = ? AND ТерриторияID = ?",
                (number, territory_id)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования кабинета: {e}")
            return False

    def get_classrooms_with_territory_names(self) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT 
                к.ID, 
                к.Кабинет as [Номер кабинета],
                т.Территория as Территория,
                к.Вместимость
            FROM Кабинеты к
            LEFT JOIN Территории т ON к.ТерриторияID = т.ID
            ORDER BY т.Территория, к.Кабинет
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении кабинетов с территориями: {e}")
            return []

    def delete_territory_with_classrooms(self, territory_id: int) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM Дисциплина_Кабинет 
                WHERE КабинетID IN (
                    SELECT ID FROM Кабинеты WHERE ТерриторияID = ?
                )
            """, (territory_id,))

            cursor.execute("DELETE FROM Кабинеты WHERE ТерриторияID = ?", (territory_id,))

            cursor.execute("DELETE FROM Территории WHERE ID = ?", (territory_id,))

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при удалении территории: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def check_territory_exists(self, name: str) -> bool:
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Территории WHERE Территория = ?",
                (name,)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования территории: {e}")
            return False

    def check_territory_exists_by_id(self, territory_id: int, name: str) -> bool:
        try:
            territories = self.get_territories()
            for territory in territories:
                if territory['ID'] != territory_id and territory['Территория'].upper() == name.upper():
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке существования территории по ID: {e}")
            return False

    def get_territory_id_by_name(self, territory_name: str) -> Optional[int]:
        try:
            territories = self.get_territories()
            for territory in territories:
                if territory['Территория'] == territory_name:
                    return territory['ID']
            return None
        except Exception as e:
            print(f"Ошибка при получении ID территории по названию: {e}")
            return None

    # ========== ПРЕПОДАВАТЕЛИ ==========
    def get_teachers_with_preferences(self) -> List[Dict[str, Any]]:
        try:
            query = """
                SELECT ID, ФИО, 
                       CASE WHEN Совместитель = 1 THEN 'Да' ELSE 'Нет' END as Совместитель,
                       COALESCE([Дни занятий], 'Любые') as [Дни занятий]
                FROM Преподаватели 
                ORDER BY ФИО
                """
            teachers = self.db.execute_query(query)

            for teacher in teachers:
                teacher_id = teacher['ID']

                territory_query = """
                    SELECT т.ID, т.Территория as Название
                    FROM Преподаватель_Территория пт
                    JOIN Территории т ON пт.ТерриторияID = т.ID
                    WHERE пт.ПреподавательID = ?
                    ORDER BY пт.ID
                    LIMIT 2
                    """
                territory_result = self.db.execute_query(territory_query, (teacher_id,))

                if territory_result:
                    territory_names = [t['Название'] for t in territory_result]
                    teacher['Территория'] = ', '.join(territory_names)
                else:
                    teacher['Территория'] = 'Не указана'

            return teachers
        except Exception as e:
            print(f"Ошибка при получении преподавателей: {e}")
            return []

    def check_teacher_exists(self, name: str) -> bool:
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Преподаватели WHERE ФИО = ?",
                (name,)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования преподавателя: {e}")
            return False

    def check_teacher_exists_by_id(self, teacher_id: int, name: str) -> bool:
        try:
            teachers = self.get_table_data("Преподаватели")
            for teacher in teachers:
                if teacher['ID'] != teacher_id and teacher['ФИО'].upper() == name.upper():
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке существования преподавателя по ID: {e}")
            return False

    def get_teacher_territories(self, teacher_id: int) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT т.ID, т.Территория
            FROM Преподаватель_Территория пт
            JOIN Территории т ON пт.ТерриторияID = т.ID
            WHERE пт.ПреподавательID = ?
            ORDER BY т.Территория
            """
            return self.db.execute_query(query, (teacher_id,))
        except Exception as e:
            print(f"Ошибка при получении территорий преподавателя: {e}")
            return []

    def insert_teacher_with_territories(self, teacher_data: Dict[str, Any], territory_ids: List[int]) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO Преподаватели (ФИО, Совместитель, [Дни занятий]) VALUES (?, ?, ?)",
                (
                    teacher_data['ФИО'],
                    1 if teacher_data.get('Совместитель', False) else 0,
                    teacher_data.get('[Дни занятий]')
                )
            )

            teacher_id = cursor.lastrowid

            for territory_id in territory_ids:
                cursor.execute(
                    "INSERT INTO Преподаватель_Территория (ПреподавательID, ТерриторияID) VALUES (?, ?)",
                    (teacher_id, territory_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении преподавателя с территориями: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_teacher_with_territories(self, teacher_id: int, teacher_data: Dict[str, Any],
                                        territory_ids: List[int]) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE Преподаватели SET ФИО = ?, Совместитель = ?, [Дни занятий] = ? WHERE ID = ?",
                (
                    teacher_data['ФИО'],
                    1 if teacher_data.get('Совместитель', False) else 0,
                    teacher_data.get('[Дни занятий]'),
                    teacher_id
                )
            )

            cursor.execute("DELETE FROM Преподаватель_Территория WHERE ПреподавательID = ?", (teacher_id,))

            for territory_id in territory_ids:
                cursor.execute(
                    "INSERT INTO Преподаватель_Территория (ПреподавательID, ТерриторияID) VALUES (?, ?)",
                    (teacher_id, territory_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении преподавателя с территориями: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== НАГРУЗКА ==========
    def get_workloads(self) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT 
                н.ID,
                п.ФИО as Преподаватель,
                д.Дисциплина as Дисциплина,
                г.Группа,
                г.Подгруппа,
                н.Часы as [Часы в неделю]
            FROM Нагрузка н
            LEFT JOIN Преподаватели п ON н.ПреподавательID = п.ID
            LEFT JOIN Дисциплины д ON н.ДисциплинаID = д.ID
            LEFT JOIN Группы г ON н.ГруппаID = г.ID
            ORDER BY п.ФИО, д.Дисциплина, г.Группа
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении нагрузки: {e}")
            return []

    def get_workload_columns(self) -> List[str]:
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Нагрузка)")
            columns = [column[1] for column in cursor.fetchall()]
            conn.close()

            column_mapping = {
                'ID': 'ID',
                'ПреподавательID': 'Преподаватель',
                'ДисциплинаID': 'Дисциплина',
                'ГруппаID': 'Группа',
                'Часы': 'Часы в неделю'
            }

            return [column_mapping.get(col, col) for col in columns]
        except Exception as e:
            print(f"Ошибка при получении колонок нагрузки: {e}")
            return []

    def insert_workload(self, workload_data: Dict[str, Any]) -> bool:
        try:
            teacher_id = self._get_teacher_id_by_name(workload_data['Преподаватель'])
            subject_id = self._get_subject_id_by_name(workload_data['Дисциплина'])

            group_name = workload_data['Группа']
            subgroup = workload_data['Подгруппа']

            result = self.db.execute_query(
                "SELECT ID FROM Группы WHERE Группа = ? AND Подгруппа = ?",
                (group_name, subgroup)
            )

            if not result:
                return False

            group_id = result[0]['ID']

            return self.db.execute_command(
                "INSERT INTO Нагрузка (ПреподавательID, ДисциплинаID, ГруппаID, Часы) VALUES (?, ?, ?, ?)",
                (teacher_id, subject_id, group_id, workload_data['Часы в неделю'])
            )
        except Exception as e:
            print(f"Ошибка при добавлении нагрузки: {e}")
            return False

    def update_workload(self, workload_id: int, workload_data: Dict[str, Any]) -> bool:
        try:
            teacher_id = self._get_teacher_id_by_name(workload_data['Преподаватель'])
            subject_id = self._get_subject_id_by_name(workload_data['Дисциплина'])

            group_name = workload_data['Группа']
            subgroup = workload_data['Подгруппа']

            result = self.db.execute_query(
                "SELECT ID FROM Группы WHERE Группа = ? AND Подгруппа = ?",
                (group_name, subgroup)
            )

            if not result:
                return False

            group_id = result[0]['ID']

            return self.db.execute_command(
                "UPDATE Нагрузка SET ПреподавательID = ?, ДисциплинаID = ?, ГруппаID = ?, Часы = ? WHERE ID = ?",
                (teacher_id, subject_id, group_id, workload_data['Часы в неделю'], workload_id)
            )
        except Exception as e:
            print(f"Ошибка при обновлении нагрузки: {e}")
            return False

    def delete_workload(self, workload_id: int) -> bool:
        try:
            return self.db.execute_command("DELETE FROM Нагрузка WHERE ID = ?", (workload_id,))
        except Exception as e:
            print(f"Ошибка при удалении нагрузки: {e}")
            return False

    def _get_teacher_id_by_name(self, name: str) -> Optional[int]:
        try:
            result = self.db.execute_query(
                "SELECT ID FROM Преподаватели WHERE ФИО = ?",
                (name,)
            )
            return result[0]['ID'] if result else None
        except Exception as e:
            print(f"Ошибка при получении ID преподавателя: {e}")
            return None

    def _get_subject_id_by_name(self, name: str) -> Optional[int]:
        try:
            result = self.db.execute_query(
                "SELECT ID FROM Дисциплины WHERE Дисциплина = ?",
                (name,)
            )
            return result[0]['ID'] if result else None
        except Exception as e:
            print(f"Ошибка при получении ID дисциплины: {e}")
            return None

    def _get_group_id_by_name(self, group_info: str) -> Optional[int]:
        try:
            if ' - ' in group_info:
                parts = group_info.split(' - ')
                group_name = parts[0].strip()
                subgroup = parts[1].strip()
            else:
                group_name = group_info
                subgroup = "Нет"

            result = self.db.execute_query(
                "SELECT ID FROM Группы WHERE Группа = ? AND Подгруппа = ?",
                (group_name, subgroup)
            )
            return result[0]['ID'] if result else None
        except Exception as e:
            print(f"Ошибка при получении ID группы: {e}")
            return None
