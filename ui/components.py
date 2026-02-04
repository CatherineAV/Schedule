import flet as ft
from typing import Callable, Optional, List, Dict, Any

PALETTE = ["#18363E", "#5F97AA", "#2D5F6E", "#3E88A5", "#93C4D1"]


class Toast:
    def __init__(self, page: ft.Page):
        self.page = page

    def show(self, message: str, success: bool = True):
        toast = ft.Container(
            content=ft.Text(message, color=ft.Colors.WHITE, size=14, weight="bold"),
            bgcolor=ft.Colors.GREEN_400 if success else ft.Colors.RED_400,
            padding=15,
            border_radius=10,
            width=400,
            alignment=ft.alignment.center,
            top=self.page.height / 2 - 25,
            left=self.page.width / 2 - 100,
            animate_position=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK54)
        )

        self.page.overlay.append(toast)
        self.page.update()

        def remove_toast():
            import time
            time.sleep(2)
            if toast in self.page.overlay:
                self.page.overlay.remove(toast)
                self.page.update()

        import threading
        threading.Thread(target=remove_toast, daemon=True).start()


class DataTableManager:
    def __init__(self):
        self.selected_rows = {}

    def create_data_table(self, data: List[Dict[str, Any]], columns: List[str],
                          section_name: str, on_row_select: Callable) -> ft.DataTable:
        display_columns = [col for col in columns if col != 'ID']
        data_rows = []

        selected_row = self.selected_rows.get(section_name, None)

        pretty_column_names = {
            "Код": "Код модуля",
            "Название": "Название модуля",
            "[Разговоры о важном]": "Разговоры о важном",
            "Кабинет": "Номер кабинета",
            "ФИО": "Преподаватель",
        }

        for i, row in enumerate(data):
            cells = []
            for col in display_columns:
                value = row.get(col, "")

                if col == "Разговоры о важном" or col == "[Разговоры о важном]":
                    value = "Да" if value == 1 or value == "Да" or value == 1.0 else "Нет"
                elif col == "Самообразование" and (not value or value == "None"):
                    value = "Нет"
                elif col == "Подгруппа" and (not value or value == "None"):
                    value = "Нет"
                elif col == "Совместитель":
                    value = "Да" if value == 1 or value == "Да" or value == 1.0 else "Нет"
                elif col == "Дни занятий" and (not value or value == "Любые" or value == "None"):
                    value = "Любые"
                elif col == "Территория" and (not value or value == "Не указана" or value == "None"):
                    value = "Не указана"
                elif (col == "Код модуля" or col == "Название модуля") and (value is None or value == "None"):
                    value = ""
                elif col == "Вместимость" and (value is None or value == "None" or value == ""):
                    value = "Не указана"
                if col == "Цвет" and value:
                    color_container = ft.Container(
                        width=20,
                        height=20,
                        border_radius=10,
                        bgcolor=value if value.startswith("#") else f"#{value}",
                        border=ft.border.all(1, PALETTE[2])
                    )
                    cell_content = ft.Row([color_container, ft.Text(value, color=PALETTE[2])], spacing=10)
                else:
                    cell_content = ft.Text(str(value), color=PALETTE[2], no_wrap=False)

                cell = ft.DataCell(ft.Container(cell_content, expand=True, alignment=ft.alignment.center_left))
                cells.append(cell)

            data_row = ft.DataRow(
                cells=cells,
                selected=selected_row == i,
                on_select_changed=lambda e, idx=i: self._on_row_select(e, idx, section_name, on_row_select)
            )
            data_rows.append(data_row)

        display_column_headers = [pretty_column_names.get(col, col) for col in display_columns]

        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight="bold", color=PALETTE[2])) for c in display_column_headers],
            rows=data_rows,
            expand=True,
            divider_thickness=0,
            data_row_color={ft.ControlState.SELECTED: PALETTE[4]}
        )

    def _on_row_select(self, e, index: int, section_name: str, on_row_select: Callable):
        if e.data == "true":
            self.selected_rows[section_name] = index
        else:
            self.selected_rows[section_name] = None

        on_row_select(self.selected_rows[section_name])

    def get_selected_row(self, section_name: str) -> Optional[int]:
        return self.selected_rows.get(section_name, None)

    def clear_selection(self, section_name: str):
        if section_name in self.selected_rows:
            self.selected_rows[section_name] = None


class Validator:
    @staticmethod
    def validate_required(value: str, field_name: str) -> Optional[str]:
        if not value or not value.strip():
            return f"Поле '{field_name}' обязательно для заполнения"
        return None

    @staticmethod
    def validate_unique(db_operations, table_name: str, field_name: str, value: str,
                        exclude_id: Optional[int] = None) -> Optional[str]:
        try:
            if table_name == "Группы":
                return None
            elif table_name == "Территории":
                if db_operations.check_territory_exists(value):
                    if not exclude_id or not _is_same_territory(db_operations, exclude_id, value):
                        return f"Территория '{value}' уже существует"
            elif table_name == "Преподаватели":
                if db_operations.check_teacher_exists(value):
                    if not exclude_id or not _is_same_teacher(db_operations, exclude_id, value):
                        return f"Преподаватель '{value}' уже существует"
            elif table_name == "Модули":
                if db_operations.check_module_exists(value):
                    if not exclude_id or not _is_same_module(db_operations, exclude_id, value):
                        return f"Модуль с кодом '{value}' уже существует"
            elif table_name == "Кабинеты":
                return None
            return None
        except Exception as e:
            print(f"Ошибка при проверке уникальности: {e}")
            return "Ошибка при проверке данных"

    @staticmethod
    def validate_group(group_name: str, subgroup: str) -> Optional[str]:
        if not group_name:
            return "Введите название группы"
        if not subgroup:
            return "Выберите подгруппу"

        if not group_name.replace(' ', '').replace('-', '').replace('/', '').replace('(', '').replace(')',
                                                                                                      '').isalnum():
            return "Название группы может содержать только буквы, цифры, пробелы, дефисы, слэши и скобки"

        if ("ХКО" in group_name.upper() or "ХБО" in group_name.upper()):
            if subgroup == "Нет":
                return "Группы ХКО и ХБО должны иметь подгруппы"
            if "ХБО" in group_name.upper() and subgroup not in ["Кукольники", "Бутафоры"]:
                return "Для группы ХБО допустимые подгруппы: 'Кукольники' или 'Бутафоры'"
            if "ХКО" in group_name.upper() and subgroup not in ["Женская", "Мужская"]:
                return "Для группы ХКО допустимые подгруппы: 'Женская' или 'Мужская'"
        else:
            if subgroup in ["Кукольники", "Бутафоры", "Женская", "Мужская"]:
                return f"Подгруппа '{subgroup}' недопустима для обычных групп"
            if subgroup not in ["Нет", "1", "2", "3"]:
                return "Для обычных групп допустимые подгруппы: 'Нет', '1', '2', '3'"
        return None

    @staticmethod
    def validate_classrooms(territory_id: Optional[str], selected_classrooms: List[int]) -> Optional[str]:
        if not territory_id:
            return "Выберите территорию"

        if not selected_classrooms:
            return "Выберите хотя бы один кабинет"

        return None

    @staticmethod
    def validate_teacher_preferences(preferences_str: str) -> Optional[str]:
        if not preferences_str:
            return None

        try:
            day_blocks = preferences_str.split(';')
            valid_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]

            for block in day_blocks:
                if ':' not in block:
                    return f"Некорректный формат предпочтений: {block}"

                day, lessons_str = block.split(':')
                day = day.strip()

                if day not in valid_days:
                    return f"Некорректный день: {day}"

                lessons = [l.strip() for l in lessons_str.split(',') if l.strip()]
                for lesson in lessons:
                    try:
                        lesson_num = int(lesson)
                        if lesson_num < 1 or lesson_num > 11:
                            return f"Номер урока должен быть от 1 до 11: {lesson}"
                    except ValueError:
                        return f"Некорректный номер урока: {lesson}"
            return None
        except Exception as e:
            return f"Ошибка при проверке предпочтений: {str(e)}"

    @staticmethod
    def validate_module_code(code: str) -> Optional[str]:
        if not code:
            return "Код модуля не может быть пустым"

        if not code.strip():
            return "Код модуля не может состоять только из пробелов"

        if len(code) > 20:
            return "Код модуля не должен превышать 20 символов"

        return None

    @staticmethod
    def validate_module_name(name: str) -> Optional[str]:
        if not name:
            return "Название модуля не может быть пустым"

        if not name.strip():
            return "Название модуля не может состоять только из пробелов"

        if len(name) > 100:
            return "Название модуля не должно превышать 100 символов"

        return None

    @staticmethod
    def validate_territory_name(name: str) -> Optional[str]:
        if not name:
            return "Название территории не может быть пустым"

        if not name.strip():
            return "Название территории не может состоять только из пробелов"

        if len(name) > 50:
            return "Название территории не должно превышать 50 символов"

        return None

    @staticmethod
    def validate_classroom_number(number: str) -> Optional[str]:
        if not number:
            return "Номер кабинета не может быть пустым"

        if not number.strip():
            return "Номер кабинета не может состоять только из пробелов"

        if len(number) > 20:
            return "Номер кабинета не должен превышать 20 символов"

        return None

    @staticmethod
    def validate_capacity(capacity: Optional[str]) -> Optional[str]:
        if not capacity or not capacity.strip():
            return None

        try:
            cap = int(capacity)
            if cap < 1:
                return "Вместимость должна быть положительным числом"
            if cap > 1000:
                return "Вместимость не должна превышать 1000 человек"
        except ValueError:
            return "Вместимость должна быть целым числом"

        return None

    @staticmethod
    def validate_teacher_name(name: str) -> Optional[str]:
        if not name:
            return "ФИО преподавателя не может быть пустым"

        if not name.strip():
            return "ФИО преподавателя не может состоять только из пробелов"

        if len(name) > 100:
            return "ФИО преподавателя не должно превышать 100 символов"

        words = name.strip().split()
        if len(words) < 2:
            return "Введите полное ФИО преподавателя (минимум имя и фамилию)"

        return None

    @staticmethod
    def validate_subject_name(name: str) -> Optional[str]:
        if not name:
            return "Название дисциплины не может быть пустым"

        if not name.strip():
            return "Название дисциплины не может состоять только из пробелов"

        if len(name) > 200:
            return "Название дисциплины не должно превышать 200 символов"

        return None

    @staticmethod
    def validate_hours(hours: str) -> Optional[str]:
        if not hours:
            return "Введите количество часов"

        try:
            hours_int = int(hours)
            if hours_int <= 0:
                return "Часы должны быть положительным числом"
            if hours_int > 40:
                return "Часы не могут превышать 40 в неделю"
        except ValueError:
            return "Часы должны быть числом"

        return None


def _is_same_territory(db_operations, territory_id: int, name: str) -> bool:
    territories = db_operations.get_table_data("Территории")
    for territory in territories:
        if territory['ID'] == territory_id:
            return territory['Название'].upper() == name.upper()
    return False


def _is_same_teacher(db_operations, teacher_id: int, name: str) -> bool:
    teachers = db_operations.get_table_data("Преподаватели")
    for teacher in teachers:
        if teacher['ID'] == teacher_id:
            return teacher['ФИО'].upper() == name.upper()
    return False


def _is_same_module(db_operations, module_code: str, name: str) -> bool:
    modules = db_operations.get_modules()
    for module in modules:
        if module['Код'] == module_code:
            return module['Код'].upper() == name.upper()
    return False
