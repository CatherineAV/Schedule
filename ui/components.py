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

        # Словарь для красивых названий колонок
        pretty_column_names = {
            "Название": "Территория",  # Для таблицы Территории
            "Номер": "Номер кабинета",  # Для таблицы Кабинеты
            "ФИО": "Преподаватель",  # Для таблицы Преподаватели
            "НазваниеМодуля": "Название модуля"  # Для таблицы Предметы
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

        # Используем красивые названия для заголовков колонок
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
