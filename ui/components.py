import flet as ft
import threading
from typing import Callable, Optional, List, Dict, Any
from database.settings_manager import SettingsManager

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

        threading.Thread(target=remove_toast, daemon=True).start()


class DataTableManager:
    def __init__(self):
        self.selected_rows = {}
        self.filtered_data = {}
        self.current_filters = {}
        self.current_search = ""

    def create_searchable_data_table(self, data: List[Dict[str, Any]], columns: List[str],
                                     section_name: str, on_row_select: Callable,
                                     search_text: str = "", filters: Dict = None) -> ft.DataTable:

        filtered_data = self._filter_data(data, columns, search_text, filters)
        self.filtered_data[section_name] = filtered_data

        return self.create_data_table(filtered_data, columns, section_name, on_row_select)

    def _filter_data(self, data: List[Dict[str, Any]], columns: List[str],
                     search_text: str, filters: Dict) -> List[Dict[str, Any]]:
        if not search_text and not filters:
            return data

        filtered = []
        search_lower = search_text.lower() if search_text else ""

        for row in data:
            if search_text:
                found = False
                for col in columns:
                    if col != 'ID' and col in row:
                        value = str(row.get(col, "")).lower()
                        if search_lower in value:
                            found = True
                            break
                if not found:
                    continue

            if filters:
                matches_filters = True
                for key, value in filters.items():
                    if key == 'active_only' and value:
                        status = row.get('Статус', row.get('Активен', True))
                        if not status:
                            matches_filters = False
                            break

                if not matches_filters:
                    continue

            filtered.append(row)

        return filtered

    def get_filtered_data(self, section_name: str) -> List[Dict[str, Any]]:
        return self.filtered_data.get(section_name, [])

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

        def calculate_row_height(row_data):
            max_lines = 1

            for col in display_columns:
                value = str(row_data.get(col, ""))

                if col == "Разговоры о важном" or col == "[Разговоры о важном]":
                    value = "Да" if value == "1" or value == "Да" or value == "1.0" else "Нет"
                elif col == "Самообразование" and (not value or value == "None"):
                    value = "Нет"
                elif col == "Подгруппа" and (not value or value == "None"):
                    value = "Нет"
                elif col == "Совместитель":
                    value = "Да" if value == "1" or value == "Да" or value == "1.0" else "Нет"
                elif col == "Дни занятий" and (not value or value == "Любые" or value == "None"):
                    value = "Любые"
                elif col == "Территория" and (not value or value == "Не указана" or value == "None"):
                    value = "Не указана"
                elif (col == "Код модуля" or col == "Название модуля") and (value is None or value == "None"):
                    value = ""
                elif col == "Вместимость" and (value is None or value == "None" or value == ""):
                    value = "Не указана"
                elif col == "Часы в неделю" and (value is None or value == "None" or value == ""):
                    value = "0"
                elif col == "Преподаватель" and (not value or value == "None"):
                    value = "Не указан"
                elif col == "Дисциплина" and (not value or value == "None"):
                    value = "Не указана"
                elif col == "Группа" and (not value or value == "None"):
                    value = "Не указана"

                char_count = len(value)

                if col in ["Дисциплина", "Преподаватель", "ФИО", "Название модуля", "Дисциплины", "Группы"]:
                    chars_per_line = 40
                else:
                    chars_per_line = 60

                lines_needed = max(1, (char_count // chars_per_line) + 1)

                if lines_needed > max_lines:
                    max_lines = lines_needed

            row_height = max_lines * 20 + 20
            return min(row_height, 300)

        max_row_height = 40
        for row in data:
            row_height = calculate_row_height(row)
            if row_height > max_row_height:
                max_row_height = row_height

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
                elif col == "Часы в неделю" and (value is None or value == "None" or value == ""):
                    value = "0"
                elif col == "Преподаватель" and (not value or value == "None"):
                    value = "Не указан"
                elif col == "Дисциплина" and (not value or value == "None"):
                    value = "Не указана"
                elif col == "Группа" and (not value or value == "None"):
                    value = "Не указана"
                elif col == "Подгруппа" and (not value or value == "None"):
                    value = "Нет"

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
            data_row_color={ft.ControlState.SELECTED: PALETTE[4]},
            data_row_min_height=40,
            data_row_max_height=max_row_height,
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


class SearchFilterBar:
    def __init__(self, on_search: Callable = None, on_filter: Callable = None,
                 section_name: str = "", db_operations=None):
        self.on_search = on_search
        self.on_filter = on_filter
        self.section_name = section_name
        self.db_ops = db_operations
        self.current_search = ""
        self.current_filters = {}

        self.teachers = []
        self.subjects = []
        self.groups = []
        self.modules = []

        if db_operations and section_name:
            self._load_filter_data()

        self.search_field = ft.TextField(
            hint_text="Поиск...",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            expand=True,
            on_change=self._on_search_change,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=5,
        )

        self.filter_button = ft.IconButton(
            icon=ft.Icons.FILTER_LIST,
            icon_color=ft.Colors.WHITE,
            bgcolor=PALETTE[3],
            tooltip="Фильтры",
            on_click=self._on_filter_click,
        )

        self.clear_button = ft.IconButton(
            icon=ft.Icons.CLEAR,
            icon_color=ft.Colors.WHITE,
            bgcolor=PALETTE[2],
            tooltip="Очистить поиск и фильтры",
            on_click=self._on_clear_click,
        )

        self.filter_dialog = None
        self.filter_controls = {}
        self.page = None

    def _load_filter_data(self):
        if self.section_name == "Нагрузка" and self.db_ops:
            self.teachers = self.db_ops.get_table_data("Преподаватели")
            self.teachers.sort(key=lambda x: x['ФИО'].lower())
            self.subjects = self.db_ops.get_subjects_with_module_names()
            self.subjects.sort(key=lambda x: x['Дисциплина'].lower())
            settings_manager = SettingsManager(self.db_ops)
            groups_with_order = settings_manager.get_groups_with_exclusion_and_order()
            order_dict = {g['ID']: g['Порядок'] for g in groups_with_order}
            self.groups = self.db_ops.get_groups()
            self.groups.sort(key=lambda g: (
                order_dict.get(g['ID'], 999),
                g['Группа'].lower(),
                g['Подгруппа'].lower() if g['Подгруппа'] != 'Нет' else ''))
        elif self.section_name == "Дисциплины" and self.db_ops:
            self.modules = self.db_ops.get_modules()
            self.modules.sort(key=lambda x: x['Код'].lower())

    def _create_filter_dialog_content(self):
        if self.section_name == "Нагрузка":
            return self._create_workload_filters()
        elif self.section_name == "Дисциплины":
            return self._create_subject_filters()
        else:
            return self._create_default_filters()

    def _create_subject_filters(self):
        if not self.modules:
            return ft.Column([
                ft.Text("Фильтрация данных", size=18, weight="bold", color=PALETTE[2]),
                ft.Divider(height=10, color=PALETTE[1]),
                ft.Text("Модули не найдены", color=ft.Colors.ORANGE_700),
            ], spacing=15, width=400)

        module_checkboxes = []

        select_all_checkbox = ft.Checkbox(
            label="Выбрать все",
            value=False,
            label_style=ft.TextStyle(color=PALETTE[2]),
            on_change=self._on_select_all_modules
        )
        module_checkboxes.append(select_all_checkbox)
        self.filter_controls['select_all'] = select_all_checkbox

        for module in self.modules:
            module_code = module['Код']
            module_name = module['Название']

            checkbox = ft.Checkbox(
                label=f"{module_code} - {module_name}",
                value=module_code in self.current_filters.get('modules', []),
                label_style=ft.TextStyle(color=PALETTE[2]),
                on_change=lambda e, code=module_code: self._on_module_filter_change(code, e.control.value)
            )
            module_checkboxes.append(checkbox)
            self.filter_controls[f'module_{module_code}'] = checkbox

        return ft.Column([
            ft.Text("Фильтрация данных", size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),
            ft.Text("Выберите модули для отображения:", color=PALETTE[2]),
            ft.Container(
                content=ft.Column(
                    module_checkboxes,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO
                ),
                height=300,
                padding=10,
                border=ft.border.all(1, PALETTE[1]),
                border_radius=5
            ),
            ft.Text(f"Всего модулей: {len(self.modules)}", size=12, color=ft.Colors.BLUE_700),
        ], spacing=15, width=450)

    def _on_select_all_modules(self, e):
        is_checked = e.control.value
        selected_modules = []

        for module in self.modules:
            module_code = module['Код']
            checkbox_key = f'module_{module_code}'

            if checkbox_key in self.filter_controls:
                self.filter_controls[checkbox_key].value = is_checked

            if is_checked:
                selected_modules.append(module_code)

        self.current_filters['modules'] = selected_modules

        if hasattr(self, 'page') and self.page:
            self.page.update()

    def _on_module_filter_change(self, module_code: str, is_checked: bool):
        if 'modules' not in self.current_filters:
            self.current_filters['modules'] = []

        if is_checked:
            if module_code not in self.current_filters['modules']:
                self.current_filters['modules'].append(module_code)
        else:
            if module_code in self.current_filters['modules']:
                self.current_filters['modules'].remove(module_code)

            if 'select_all' in self.filter_controls:
                self.filter_controls['select_all'].value = False

    def _create_default_filters(self):
        return ft.Column([
            ft.Text("Фильтрация данных", size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),
            ft.Text("Фильтры для этого раздела пока не реализованы", color=PALETTE[0]),
        ], spacing=15, width=400)

    def _create_workload_filters(self):
        teacher_options = [ft.dropdown.Option("", "Все преподаватели")]
        teacher_options.extend([
            ft.dropdown.Option(t['ФИО'], t['ФИО'])
            for t in self.teachers
        ])

        subject_options = [ft.dropdown.Option("", "Все дисциплины")]
        subject_options.extend([
            ft.dropdown.Option(s['Дисциплина'], s['Дисциплина'])
            for s in self.subjects
        ])

        group_options = [ft.dropdown.Option("", "Все группы")]
        for group in self.groups:
            group_name = group['Группа']
            subgroup = group['Подгруппа']
            if subgroup and subgroup != 'Нет' and subgroup != 'None':
                display_name = f"{group_name} - {subgroup}"
            else:
                display_name = group_name
            group_options.append(ft.dropdown.Option(display_name, display_name))

        teacher_dropdown = ft.Dropdown(
            label="Преподаватель",
            options=teacher_options,
            value=self.current_filters.get('teacher', ""),
            width=350,
            border_color=PALETTE[3],
            on_change=lambda e: self._update_filter('teacher', e.control.value)
        )

        subject_dropdown = ft.Dropdown(
            label="Дисциплина",
            options=subject_options,
            value=self.current_filters.get('subject', ""),
            width=350,
            border_color=PALETTE[3],
            on_change=lambda e: self._update_filter('subject', e.control.value)
        )

        group_dropdown = ft.Dropdown(
            label="Группа",
            options=group_options,
            value=self.current_filters.get('group', ""),
            width=350,
            border_color=PALETTE[3],
            on_change=lambda e: self._update_filter('group', e.control.value)
        )

        self.filter_controls['teacher'] = teacher_dropdown
        self.filter_controls['subject'] = subject_dropdown
        self.filter_controls['group'] = group_dropdown

        return ft.Column([
            ft.Text("Фильтрация данных", size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),
            ft.Text("Выберите критерии фильтрации:", color=PALETTE[2]),
            ft.Container(height=10),
            teacher_dropdown,
            ft.Container(height=10),
            subject_dropdown,
            ft.Container(height=10),
            group_dropdown,
            ft.Container(height=10),
            ft.Checkbox(
                label="Показывать только с подгруппами",
                value=self.current_filters.get('with_subgroups_only', False),
                label_style=ft.TextStyle(color=PALETTE[2]),
                on_change=lambda e: self._update_filter('with_subgroups_only', e.control.value)
            ),
        ], spacing=5, width=400, scroll=ft.ScrollMode.AUTO)

    def _on_search_change(self, e):
        self.current_search = e.control.value.lower()
        if self.on_search:
            self.on_search(self.current_search)

    def _on_filter_click(self, e):
        self._show_filter_dialog()

    def _on_clear_click(self, e):
        self.search_field.value = ""
        self.current_search = ""
        self.current_filters = {}

        for key, control in self.filter_controls.items():
            if hasattr(control, 'value'):
                if key == 'select_all':
                    control.value = False
                elif key.startswith('module_'):
                    control.value = False
                else:
                    control.value = ""
        if self.page:
            self.search_field.update()
        if self.on_search:
            self.on_search("")
        if self.on_filter:
            self.on_filter({})

    def _show_filter_dialog(self):
        if not self.on_filter or not self.page:
            return

        filter_content = self._create_filter_dialog_content()

        dialog_height = 500 if self.section_name == "Дисциплины" else 350

        self.filter_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=filter_content,
                width=500,
                height=dialog_height,
                bgcolor=ft.Colors.WHITE,
            ),
            actions=[
                ft.TextButton("Сбросить", on_click=self._reset_filters, style=ft.ButtonStyle(color=PALETTE[2])),
                ft.TextButton("Применить", on_click=self._apply_filters, style=ft.ButtonStyle(color=PALETTE[2])),
                ft.TextButton("Отмена", on_click=self._close_filter_dialog, style=ft.ButtonStyle(color=PALETTE[2])),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
        )

        self.page.overlay.append(self.filter_dialog)
        self.filter_dialog.open = True
        self.page.update()

    def _update_filter(self, key: str, value):
        self.current_filters[key] = value
        if key in self.filter_controls:
            self.filter_controls[key].value = value

    def _reset_filters(self, e):
        self.current_filters = {}

        for key, control in self.filter_controls.items():
            if hasattr(control, 'value'):
                if key == 'select_all':
                    control.value = False
                elif key.startswith('module_'):
                    control.value = False
                else:
                    control.value = ""

        self.filter_dialog.open = False
        self.page.update()

        if self.on_filter:
            self.on_filter({})

    def _apply_filters(self, e):
        self.filter_dialog.open = False
        self.page.update()

        if self.section_name == "Дисциплины" and 'modules' in self.current_filters:
            if not isinstance(self.current_filters['modules'], list):
                self.current_filters['modules'] = []

        if self.on_filter:
            self.on_filter(self.current_filters)

    def _close_filter_dialog(self, e):
        self.filter_dialog.open = False
        self.page.update()

    def build(self) -> ft.Row:
        return ft.Row([
            ft.Container(
                content=self.search_field,
                expand=True,
            ),
            self.filter_button,
            self.clear_button,
        ], spacing=10, alignment=ft.MainAxisAlignment.START, expand=True)


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


def create_styled_dialog(title: str, content: str, on_confirm, on_cancel) -> ft.AlertDialog:
    return ft.AlertDialog(
        modal=True,
        title=ft.Text(title, color=PALETTE[2], weight="bold"),
        content=ft.Text(content, color=PALETTE[2]),
        actions=[
            ft.TextButton(
                "Да",
                on_click=on_confirm,
                style=ft.ButtonStyle(color=PALETTE[3])
            ),
            ft.TextButton(
                "Нет",
                on_click=on_cancel,
                style=ft.ButtonStyle(color=PALETTE[2])
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=ft.Colors.WHITE,
    )
