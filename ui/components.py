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
            "Название": "Территория",
            "Номер": "Номер кабинета",
            "ФИО": "Преподаватель",
            "НазваниеМодуля": "Название модуля"
        }

        for i, row in enumerate(data):
            cells = []
            for col in display_columns:
                value = row.get(col, "")
                if col == "Разговоры о важном":
                    value = "Да" if value == 1 or value == "Да" else "Нет"
                elif col == "Самообразование" and not value:
                    value = "Нет"
                elif col == "Подгруппа" and not value:
                    value = "Нет"

                txt = ft.Text(str(value), color=PALETTE[2], no_wrap=False)
                cell = ft.DataCell(ft.Container(txt, expand=True, alignment=ft.alignment.center_left))
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
        """Проверка уникальности значения в таблице"""
        try:
            if table_name == "Группы":
                # Специальная проверка для групп
                existing_groups = db_operations.get_groups_with_subgroups()
                for group in existing_groups:
                    if group['Группа'].upper() == value.upper():
                        if exclude_id and group['ID'] == exclude_id:
                            continue
                        return f"Группа '{value}' уже существует"
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
                # Для кабинетов нужна специальная обработка
                pass  # Обрабатывается отдельно
            return None
        except Exception as e:
            print(f"Ошибка при проверке уникальности: {e}")
            return "Ошибка при проверке данных"

    @staticmethod
    def validate_subgroups(group_name: str, subgroups: List[str]) -> Optional[str]:
        if not subgroups:
            return "Выберите хотя бы одну подгруппу"

        if ("ХКО" in group_name.upper() or "ХБО" in group_name.upper()) and "Нет" in subgroups:
            return "Группы ХКО и ХБО должны иметь подгруппы"

        return None

    @staticmethod
    def validate_classrooms(territory_id: Optional[str], selected_classrooms: List[int]) -> Optional[str]:
        if not territory_id:
            return "Выберите территорию"

        if not selected_classrooms:
            return "Выберите хотя бы один кабинет"

        return None


def _is_same_territory(db_operations, territory_id: int, name: str) -> bool:
    """Проверяет, относится ли имя к той же территории"""
    territories = db_operations.get_table_data("Территории")
    for territory in territories:
        if territory['ID'] == territory_id:
            return territory['Название'].upper() == name.upper()
    return False


def _is_same_teacher(db_operations, teacher_id: int, name: str) -> bool:
    """Проверяет, относится ли имя к тому же преподавателю"""
    teachers = db_operations.get_table_data("Преподаватели")
    for teacher in teachers:
        if teacher['ID'] == teacher_id:
            return teacher['ФИО'].upper() == name.upper()
    return False


def _is_same_module(db_operations, module_code: str, name: str) -> bool:
    """Проверяет, относится ли имя к тому же модулю"""
    modules = db_operations.get_modules()
    for module in modules:
        if module['Код'] == module_code:
            return module['Код'].upper() == name.upper()
    return False
