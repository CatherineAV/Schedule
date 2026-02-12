import json, sqlite3
from typing import Any, Dict, List, Optional
from database.operations import DBOperations


class SettingsManager:
    def __init__(self, db_ops: DBOperations):
        self.db_ops = db_ops

    # ========== ОБЩИЕ НАСТРОЙКИ ==========
    def save_setting(self, key: str, value: Any, value_type: str = 'TEXT') -> bool:
        value_str = str(value) if value_type != 'JSON' else json.dumps(value)

        existing = self.db_ops.db.execute_query(
            "SELECT ID FROM Настройки WHERE Ключ = ?", (key,)
        )

        if existing:
            return self.db_ops.db.execute_command(
                "UPDATE Настройки SET Значение = ?, Тип = ? WHERE Ключ = ?",
                (value_str, value_type, key)
            )
        else:
            return self.db_ops.db.execute_command(
                "INSERT INTO Настройки (Ключ, Значение, Тип) VALUES (?, ?, ?)",
                (key, value_str, value_type)
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        result = self.db_ops.db.execute_query(
            "SELECT Значение, Тип FROM Настройки WHERE Ключ = ?", (key,)
        )

        if not result:
            return default

        value_str = result[0]['Значение']
        value_type = result[0]['Тип']

        if value_type == 'JSON':
            return json.loads(value_str) if value_str else default
        elif value_type == 'INT':
            return int(value_str) if value_str else default
        elif value_type == 'BOOL':
            return value_str == 'True' if value_str else default
        else:
            return value_str if value_str else default

    # ========== ПОТОКИ ГРУПП ==========
    def save_stream(self, name: str, group_ids: List[int]) -> bool:
        # if len(group_ids) > 4:
        #     raise ValueError("Максимум можно объединить 4 группы")

        if len(set(group_ids)) != len(group_ids):
            raise ValueError("Группы не должны повторяться")

        group1 = group_ids[0] if len(group_ids) > 0 else None
        group2 = group_ids[1] if len(group_ids) > 1 else None
        group3 = group_ids[2] if len(group_ids) > 2 else None
        group4 = group_ids[3] if len(group_ids) > 3 else None

        return self.db_ops.db.execute_command(
            """INSERT INTO Потоки (Поток, Группа1_ID, Группа2_ID, Группа3_ID, Группа4_ID) 
               VALUES (?, ?, ?, ?, ?)""",
            (name, group1, group2, group3, group4)
        )

    def update_stream(self, stream_id: int, name: str, group_ids: List[int]) -> bool:
        # if len(group_ids) > 3:
        #     raise ValueError("Максимум можно объединить 3 группы")

        if len(set(group_ids)) != len(group_ids):
            raise ValueError("Группы не должны повторяться")

        group1 = group_ids[0] if len(group_ids) > 0 else None
        group2 = group_ids[1] if len(group_ids) > 1 else None
        group3 = group_ids[2] if len(group_ids) > 2 else None
        group4 = group_ids[3] if len(group_ids) > 3 else None

        return self.db_ops.db.execute_command(
            """UPDATE Потоки SET Поток = ?, Группа1_ID = ?, Группа2_ID = ?, Группа3_ID = ?, Группа4_ID = ?
               WHERE ID = ?""",
            (name, group1, group2, group3, group4, stream_id)
        )

    def delete_stream(self, stream_id: int) -> bool:
        return self.db_ops.db.execute_command(
            "DELETE FROM Потоки WHERE ID = ?", (stream_id,)
        )

    def get_streams(self) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                п.ID,
                п.Поток as Поток,
                г1.ID as Группа1_ID,
                г1.Группа as Группа1_Название,
                г1.Подгруппа as Группа1_Подгруппа,
                г2.ID as Группа2_ID,
                г2.Группа as Группа2_Название,
                г2.Подгруппа as Группа2_Подгруппа,
                г3.ID as Группа3_ID,
                г3.Группа as Группа3_Название,
                г3.Подгруппа as Группа3_Подгруппа,
                г4.ID as Группа4_ID,  -- НОВАЯ
                г4.Группа as Группа4_Название,  -- НОВАЯ
                г4.Подгруппа as Группа4_Подгруппа  -- НОВАЯ
            FROM Потоки п
            LEFT JOIN Группы г1 ON п.Группа1_ID = г1.ID
            LEFT JOIN Группы г2 ON п.Группа2_ID = г2.ID
            LEFT JOIN Группы г3 ON п.Группа3_ID = г3.ID
            LEFT JOIN Группы г4 ON п.Группа4_ID = г4.ID  -- НОВАЯ
            ORDER BY п.ID
            """

        streams = self.db_ops.db.execute_query(query)

        result = []
        for stream in streams:
            groups_info = []
            if stream['Группа1_ID']:
                group1_name = f"{stream['Группа1_Название']}"
                if stream['Группа1_Подгруппа'] and stream['Группа1_Подгруппа'] != 'Нет':
                    group1_name += f" - {stream['Группа1_Подгруппа']}"
                groups_info.append(group1_name)

            if stream['Группа2_ID']:
                group2_name = f"{stream['Группа2_Название']}"
                if stream['Группа2_Подгруппа'] and stream['Группа2_Подгруппа'] != 'Нет':
                    group2_name += f" - {stream['Группа2_Подгруппа']}"
                groups_info.append(group2_name)

            if stream['Группа3_ID']:
                group3_name = f"{stream['Группа3_Название']}"
                if stream['Группа3_Подгруппа'] and stream['Группа3_Подгруппа'] != 'Нет':
                    group3_name += f" - {stream['Группа3_Подгруппа']}"
                groups_info.append(group3_name)

            if stream['Группа4_ID']:
                group4_name = f"{stream['Группа4_Название']}"
                if stream['Группа4_Подгруппа'] and stream['Группа4_Подгруппа'] != 'Нет':
                    group4_name += f" - {stream['Группа4_Подгруппа']}"
                groups_info.append(group4_name)

            groups_display = ", ".join(groups_info)

            result.append({
                'ID': stream['ID'],
                'Поток': stream['Поток'],
                'Группы': groups_display,
                'Группа1_ID': stream['Группа1_ID'],
                'Группа2_ID': stream['Группа2_ID'],
                'Группа3_ID': stream['Группа3_ID'],
                'Группа4_ID': stream['Группа4_ID'],
                'Группы_список': groups_info
            })

        return result

    def get_stream_by_id(self, stream_id: int) -> Optional[Dict[str, Any]]:
        streams = self.get_streams()
        for stream in streams:
            if stream['ID'] == stream_id:
                return stream
        return None

    def check_group_in_any_stream(self, group_id: int) -> bool:
        result = self.db_ops.db.execute_query(
            """SELECT COUNT(*) as count FROM Потоки 
               WHERE Группа1_ID = ? OR Группа2_ID = ? OR Группа3_ID = ? OR Группа4_ID = ?""",
            (group_id, group_id, group_id, group_id)
        )
        return result[0]['count'] > 0 if result else False

    def save_stream_with_subjects(self, name: str, group_ids: List[int], subject_ids: List[int]) -> bool:
        # if len(group_ids) > 3:
        #     raise ValueError("Максимум можно объединить 3 группы")

        if len(set(group_ids)) != len(group_ids):
            raise ValueError("Группы не должны повторяться")

        conn = self.db_ops.db._get_connection()
        cursor = conn.cursor()

        try:
            group1 = group_ids[0] if len(group_ids) > 0 else None
            group2 = group_ids[1] if len(group_ids) > 1 else None
            group3 = group_ids[2] if len(group_ids) > 2 else None
            group4 = group_ids[3] if len(group_ids) > 3 else None

            cursor.execute(
                """INSERT INTO Потоки (Поток, Группа1_ID, Группа2_ID, Группа3_ID, Группа4_ID) 
                   VALUES (?, ?, ?, ?, ?)""",
                (name, group1, group2, group3, group4)
            )

            stream_id = cursor.lastrowid

            for subject_id in subject_ids:
                cursor.execute(
                    "INSERT INTO Поток_Дисциплина (ПотокID, ДисциплинаID) VALUES (?, ?)",
                    (stream_id, subject_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении потока с дисциплинами: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_stream_with_subjects(self, stream_id: int, name: str, group_ids: List[int],
                                    subject_ids: List[int]) -> bool:
        # if len(group_ids) > 3:
        #     raise ValueError("Максимум можно объединить 3 группы")

        if len(set(group_ids)) != len(group_ids):
            raise ValueError("Группы не должны повторяться")

        conn = self.db_ops.db._get_connection()
        cursor = conn.cursor()

        try:
            group1 = group_ids[0] if len(group_ids) > 0 else None
            group2 = group_ids[1] if len(group_ids) > 1 else None
            group3 = group_ids[2] if len(group_ids) > 2 else None
            group4 = group_ids[3] if len(group_ids) > 3 else None

            cursor.execute(
                """UPDATE Потоки SET Поток = ?, Группа1_ID = ?, Группа2_ID = ?, Группа3_ID = ?, Группа4_ID = ?
                   WHERE ID = ?""",
                (name, group1, group2, group3, group4, stream_id)
            )

            cursor.execute("DELETE FROM Поток_Дисциплина WHERE ПотокID = ?", (stream_id,))

            for subject_id in subject_ids:
                cursor.execute(
                    "INSERT INTO Поток_Дисциплина (ПотокID, ДисциплинаID) VALUES (?, ?)",
                    (stream_id, subject_id)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении потока с дисциплинами: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_stream_subjects(self, stream_id: int) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            д.ID,
            д.Дисциплина as Название,
            д.Модуль as Модуль
        FROM Поток_Дисциплина пд
        JOIN Дисциплины д ON пд.ДисциплинаID = д.ID
        WHERE пд.ПотокID = ?
        ORDER BY д.Дисциплина
        """

        return self.db_ops.db.execute_query(query, (stream_id,))

    def get_streams_with_subjects(self) -> List[Dict[str, Any]]:
        streams = self.get_streams()

        for stream in streams:
            stream_id = stream['ID']
            subjects = self.get_stream_subjects(stream_id)

            subject_names = []
            subject_ids = []
            for subject in subjects:
                subject_names.append(subject['Название'])
                subject_ids.append(subject['ID'])

            stream['Дисциплины'] = ", ".join(subject_names) if subject_names else "Не указаны"
            stream['Дисциплины_список'] = subject_names
            stream['Дисциплины_ID'] = subject_ids

        return streams

    def get_stream_by_id_with_subjects(self, stream_id: int) -> Optional[Dict[str, Any]]:
        streams = self.get_streams_with_subjects()
        for stream in streams:
            if stream['ID'] == stream_id:
                return stream
        return None

    # ========== УПРАВЛЕНИЕ ГРУППАМИ В РАСПИСАНИИ ==========
    def get_excluded_groups(self) -> List[int]:
        setting = self.get_setting("excluded_groups", [])
        return setting if isinstance(setting, list) else []

    def save_excluded_groups(self, group_ids: List[int]) -> bool:
        return self.save_setting("excluded_groups", group_ids, "JSON")

    def add_excluded_group(self, group_id: int) -> bool:
        excluded = self.get_excluded_groups()
        if group_id not in excluded:
            excluded.append(group_id)
            return self.save_excluded_groups(excluded)
        return True

    def remove_excluded_group(self, group_id: int) -> bool:
        excluded = self.get_excluded_groups()
        if group_id in excluded:
            excluded.remove(group_id)
            return self.save_excluded_groups(excluded)
        return True

    def is_group_excluded(self, group_id: int) -> bool:
        return group_id in self.get_excluded_groups()

    # ========== ПОСЛЕДОВАТЕЛЬНОСТЬ ГРУПП ==========
    def get_group_order(self) -> List[int]:
        setting = self.get_setting("group_order", [])
        return setting if isinstance(setting, list) else []

    def save_group_order(self, group_ids: List[int]) -> bool:
        return self.save_setting("group_order", group_ids, "JSON")

    def get_groups_with_exclusion_and_order(self) -> List[Dict[str, Any]]:
        groups = self.db_ops.get_groups()
        excluded = self.get_excluded_groups()
        order = self.get_group_order()

        order_dict = {group_id: index for index, group_id in enumerate(order)}

        result = []
        for group in groups:
            group_id = group['ID']
            result.append({
                **group,
                'Исключена': group_id in excluded,
                'Порядок': order_dict.get(group_id, 999)
            })

        result.sort(key=lambda x: (x['Порядок'], x['Группа'], x['Подгруппа']))
        return result

    # ========== ПАРАМЕТРЫ ГЕНЕРАЦИИ ==========
    def get_generation_params(self) -> Dict[str, Any]:
        return {
            'excluded_groups': self.get_excluded_groups(),
            'group_order': self.get_group_order(),
        }

    def save_generation_params(self, params: Dict[str, Any]) -> bool:
        success = True
        if 'excluded_groups' in params:
            success = success and self.save_excluded_groups(params['excluded_groups'])
        if 'group_order' in params:
            success = success and self.save_group_order(params['group_order'])
        return success
