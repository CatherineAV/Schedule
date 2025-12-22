import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from .core import Database


class DBOperations:
    def __init__(self, db_name: str = "schedule.db"):
        self.db = Database(db_name)

    def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Получение всех данных из таблицы"""
        try:
            return self.db.execute_query(f"SELECT * FROM {table_name}")
        except Exception as e:
            print(f"Ошибка при получении данных из таблицы {table_name}: {e}")
            return []

    def get_table_columns(self, table_name: str) -> List[str]:
        """Получение списка колонок таблицы"""
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
        """Вставка данных в таблицу"""
        try:
            # Убираем ID если он есть (для автоинкремента)
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
        """Удаление записи по ID"""
        try:
            return self.db.execute_command(f"DELETE FROM {table_name} WHERE ID = ?", (record_id,))
        except Exception as e:
            print(f"Ошибка при удалении записи из таблицы {table_name}: {e}")
            return False

    def update_record(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Обновление записи по ID"""
        try:
            # Убираем ID из данных для обновления
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

    def get_groups_with_subgroups(self) -> List[Dict[str, Any]]:
        """Получение групп с подгруппами"""
        try:
            query = """
            SELECT g.ID, g.Название as Группа, g.Самообразование, g.[Разговоры о важном],
                   s.Название as Подгруппа
            FROM Группы g
            LEFT JOIN Подгруппы s ON g.ID = s.ГруппаID
            ORDER BY g.ID
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении групп с подгруппами: {e}")
            return []

    def insert_group_with_subgroups(self, group_data: Dict[str, Any], subgroups: List[str]) -> bool:
        """Добавление группы с подгруппами"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Проверка существования группы с таким названием
            existing_groups = self.get_groups_with_subgroups()
            group_name = group_data['Название']

            # Проверяем, существует ли уже группа с таким названием
            for existing in existing_groups:
                if existing['Группа'].upper() == group_name.upper():
                    # Если группа существует, проверяем подгруппы
                    existing_subgroups = [existing['Подгруппа'] for existing in existing_groups
                                          if existing['Группа'].upper() == group_name.upper()]

                    # Если пытаемся добавить "Нет" когда уже есть подгруппы
                    if "Нет" in subgroups and len(existing_subgroups) > 0 and "Нет" not in existing_subgroups:
                        return False

                    # Если пытаемся добавить подгруппы когда уже есть "Нет"
                    if "Нет" not in subgroups and "Нет" in existing_subgroups:
                        return False

                    # Проверяем дублирование подгрупп
                    for subgroup in subgroups:
                        if subgroup in existing_subgroups:
                            return False

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

    def delete_group_with_subgroups(self, group_name: str, subgroup_name: str) -> bool:
        """Удаление группы или подгруппы"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Находим ID группы
            cursor.execute("SELECT ID FROM Группы WHERE Название = ?", (group_name,))
            group_result = cursor.fetchone()

            if not group_result:
                return False

            group_id = group_result[0]

            # Удаляем указанную подгруппу
            cursor.execute("DELETE FROM Подгруппы WHERE ГруппаID = ? AND Название = ?", (group_id, subgroup_name))

            # Проверяем, остались ли подгруппы
            cursor.execute("SELECT COUNT(*) FROM Подгруппы WHERE ГруппаID = ?", (group_id,))
            remaining_subgroups = cursor.fetchone()[0]

            # Если подгрупп не осталось, удаляем группу
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

    def update_group_with_subgroups(self, group_id: int, group_data: Dict[str, Any], subgroups: List[str]) -> bool:
        """Обновление группы с подгруппами"""
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

    def get_modules(self) -> List[Dict[str, Any]]:
        """Получение всех модулей"""
        try:
            return self.db.execute_query("SELECT Код, Название FROM Модули ORDER BY Код")
        except Exception as e:
            print(f"Ошибка при получении модулей: {e}")
            return []

    def insert_module(self, code: str, name: str) -> bool:
        """Добавление модуля"""
        try:
            return self.db.execute_command(
                "INSERT INTO Модули (Код, Название) VALUES (?, ?)",
                (code, name)
            )
        except Exception as e:
            print(f"Ошибка при добавлении модуля: {e}")
            return False

    def check_subject_exists(self, name: str, module: str) -> bool:
        """Проверка существования предмета"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Предметы WHERE Название = ? AND Модуль = ?",
                (name, module)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования предмета: {e}")
            return False

    def check_module_exists(self, code: str) -> bool:
        """Проверка существования модуля"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Модули WHERE Код = ?",
                (code,)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования модуля: {e}")
            return False

    def get_subjects_with_module_names(self) -> List[Dict[str, Any]]:
        """Получение предметов с названиями модулей"""
        try:
            query = """
            SELECT 
                п.ID, 
                п.Название as Предмет, 
                п.Модуль as [Код модуля],
                м.Название as [Название модуля]
            FROM Предметы п
            LEFT JOIN Модули м ON п.Модуль = м.Код
            ORDER BY п.ID
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении предметов с модулями: {e}")
            return []

    def get_classrooms(self) -> List[Dict[str, Any]]:
        """Получение всех кабинетов с названиями территорий"""
        try:
            query = """
            SELECT к.ID, к.Номер, т.Название as Территория 
            FROM Кабинеты к
            LEFT JOIN Территории т ON к.ТерриторияID = т.ID
            ORDER BY т.Название, к.Номер
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении кабинетов: {e}")
            return []

    def insert_subject_with_classrooms(self, subject_data: Dict[str, Any], classroom_ids: List[int]) -> bool:
        """Добавление предмета с привязкой к кабинетам"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Добавляем предмет
            cursor.execute(
                "INSERT INTO Предметы (Название, Модуль) VALUES (?, ?)",
                (subject_data['Название'], subject_data['Модуль'])
            )

            subject_id = cursor.lastrowid

            # Привязываем кабинеты
            for classroom_id in classroom_ids:
                cursor.execute(
                    "INSERT INTO Предмет_Кабинет (ПредметID, КабинетID) VALUES (?, ?)",
                    (subject_id, classroom_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении предмета: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_territories(self) -> List[Dict[str, Any]]:
        """Получение всех территорий"""
        try:
            return self.db.execute_query("SELECT ID, Название FROM Территории ORDER BY Название")
        except Exception as e:
            print(f"Ошибка при получении территорий: {e}")
            return []

    def get_classrooms_by_territory(self, territory_id: int) -> List[Dict[str, Any]]:
        """Получение кабинетов по территории"""
        try:
            return self.db.execute_query(
                "SELECT ID, Номер FROM Кабинеты WHERE ТерриторияID = ? ORDER BY Номер",
                (territory_id,)
            )
        except Exception as e:
            print(f"Ошибка при получении кабинетов по территории: {e}")
            return []

    def get_classrooms_by_subject(self, subject_id: int) -> List[Dict[str, Any]]:
        """Получение кабинетов по предмету"""
        try:
            return self.db.execute_query(
                """SELECT к.ID, к.Номер, т.Название as Территория 
                FROM Кабинеты к
                JOIN Предмет_Кабинет пк ON к.ID = пк.КабинетID
                JOIN Территории т ON к.ТерриторияID = т.ID
                WHERE пк.ПредметID = ?""",
                (subject_id,)
            )
        except Exception as e:
            print(f"Ошибка при получении кабинетов по предмету: {e}")
            return []

    def update_subject_with_classrooms(self, subject_id: int, subject_data: Dict[str, Any],
                                       classroom_ids: List[int]) -> bool:
        """Обновление предмета с кабинетами"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Обновляем предмет
            cursor.execute(
                "UPDATE Предметы SET Название = ?, Модуль = ? WHERE ID = ?",
                (subject_data['Название'], subject_data['Модуль'], subject_id)
            )

            # Удаляем старые привязки к кабинетам
            cursor.execute("DELETE FROM Предмет_Кабинет WHERE ПредметID = ?", (subject_id,))

            # Добавляем новые привязки
            for classroom_id in classroom_ids:
                cursor.execute(
                    "INSERT INTO Предмет_Кабинет (ПредметID, КабинетID) VALUES (?, ?)",
                    (subject_id, classroom_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении предмета: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_classroom_by_id(self, classroom_id: int) -> Optional[Dict[str, Any]]:
        """Получение кабинета по ID"""
        try:
            result = self.db.execute_query(
                "SELECT ID, Номер, ТерриторияID FROM Кабинеты WHERE ID = ?",
                (classroom_id,)
            )
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении кабинета по ID: {e}")
            return None

    def check_classroom_exists(self, number: str, territory_id: int) -> bool:
        """Проверка существования кабинета"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Кабинеты WHERE Номер = ? AND ТерриторияID = ?",
                (number, territory_id)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования кабинета: {e}")
            return False

    def get_classrooms_with_territory_names(self) -> List[Dict[str, Any]]:
        """Получение кабинетов с названиями территорий и вместимостью"""
        try:
            query = """
            SELECT 
                к.ID, 
                к.Номер as [Номер кабинета],
                т.Название as Территория,
                к.Вместимость
            FROM Кабинеты к
            LEFT JOIN Территории т ON к.ТерриторияID = т.ID
            ORDER BY т.Название, к.Номер
            """
            return self.db.execute_query(query)
        except Exception as e:
            print(f"Ошибка при получении кабинетов с территориями: {e}")
            return []

    def delete_territory_with_classrooms(self, territory_id: int) -> bool:
        """Удаление территории с кабинетами"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Удаляем привязки предметов к кабинетам этой территории
            cursor.execute("""
                DELETE FROM Предмет_Кабинет 
                WHERE КабинетID IN (
                    SELECT ID FROM Кабинеты WHERE ТерриторияID = ?
                )
            """, (territory_id,))

            # Удаляем кабинеты территории
            cursor.execute("DELETE FROM Кабинеты WHERE ТерриторияID = ?", (territory_id,))

            # Удаляем территорию
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
        """Проверка существования территории"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Территории WHERE Название = ?",
                (name,)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования территории: {e}")
            return False

    def check_teacher_exists(self, name: str) -> bool:
        """Проверка существования преподавателя"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Преподаватели WHERE ФИО = ?",
                (name,)
            )
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            print(f"Ошибка при проверке существования преподавателя: {e}")
            return False

    # Новые методы для улучшенной валидации

    def check_group_exists(self, group_name: str, exclude_id: Optional[int] = None) -> bool:
        """Проверка существования группы (с исключением ID)"""
        try:
            groups = self.get_groups_with_subgroups()
            for group in groups:
                if group['Группа'].upper() == group_name.upper():
                    if exclude_id and group['ID'] == exclude_id:
                        continue
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке существования группы: {e}")
            return False

    def check_territory_exists_by_id(self, territory_id: int, name: str) -> bool:
        """Проверка существования территории с другим ID"""
        try:
            territories = self.get_territories()
            for territory in territories:
                if territory['ID'] != territory_id and territory['Название'].upper() == name.upper():
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке существования территории по ID: {e}")
            return False

    def check_teacher_exists_by_id(self, teacher_id: int, name: str) -> bool:
        """Проверка существования преподавателя с другим ID"""
        try:
            teachers = self.get_table_data("Преподаватели")
            for teacher in teachers:
                if teacher['ID'] != teacher_id and teacher['ФИО'].upper() == name.upper():
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке существования преподавателя по ID: {e}")
            return False

    def check_module_exists_by_code(self, exclude_code: str, code: str) -> bool:
        """Проверка существования модуля с другим кодом"""
        try:
            modules = self.get_modules()
            for module in modules:
                if module['Код'] != exclude_code and module['Код'].upper() == code.upper():
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке существования модуля по коду: {e}")
            return False

    def get_territory_id_by_name(self, territory_name: str) -> Optional[int]:
        """Получение ID территории по названию"""
        try:
            territories = self.get_territories()
            for territory in territories:
                if territory['Название'] == territory_name:
                    return territory['ID']
            return None
        except Exception as e:
            print(f"Ошибка при получении ID территории по названию: {e}")
            return None

