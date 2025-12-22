import flet as ft
from typing import Callable, List, Dict, Any, Optional
from database.operations import DBOperations
from ui.components import Toast, DataTableManager, PALETTE, Validator
from ui.forms import GroupForm, ClassroomForm, TeacherForm


class BasePage:
    def __init__(self, menu_column: ft.Column, content: ft.Container,
                 page: ft.Page, db_ops: DBOperations, toast: Toast):
        self.menu_column = menu_column
        self.content = content
        self.page = page
        self.db_ops = db_ops
        self.toast = toast
        self.table_manager = DataTableManager()


class MainMenu(BasePage):
    def render(self):
        self.menu_column.controls.clear()
        self.menu_column.controls.extend([
            ft.ElevatedButton(
                "Данные",
                icon=ft.Icons.FOLDER,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=self._on_data_click
            ),
            ft.ElevatedButton(
                "Настройки генерации",
                icon=ft.Icons.SETTINGS,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=self._on_settings_click
            ),
            ft.ElevatedButton(
                "Сгенерировать",
                icon=ft.Icons.PLAY_ARROW,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=self._on_generate_click
            ),
        ])

        self.content.content = ft.Column([
            ft.Text("Добро пожаловать! Выберите пункт меню.", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.page.update()

    def _on_data_click(self, e):
        data_menu = DataMenu(self.menu_column, self.content, self.page, self.db_ops, self.toast)
        data_menu.render()

    def _on_settings_click(self, e):
        self.content.content = ft.Column([
            ft.Text("Настройки генерации.", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.page.update()

    def _on_generate_click(self, e):
        self.content.content = ft.Column([
            ft.Text("Сгенерировать расписание.", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.page.update()


class DataMenu(BasePage):
    def render(self):
        self.menu_column.controls.clear()
        self.menu_column.controls.extend([
            ft.ElevatedButton(
                "Назад",
                icon=ft.Icons.ARROW_BACK,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=self._on_back_click
            ),
            ft.Divider(height=20, color=ft.Colors.WHITE),
            ft.ElevatedButton(
                "Группы",
                icon=ft.Icons.GROUPS,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Группы")
            ),
            ft.ElevatedButton(
                "Предметы",
                icon=ft.Icons.CLASS_,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Предметы")
            ),
            ft.ElevatedButton(
                "Преподаватели",
                icon=ft.Icons.MAN,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Преподаватели")
            ),
            ft.ElevatedButton(
                "Территории",
                icon=ft.Icons.MAP,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Территории")
            ),
            ft.ElevatedButton(
                "Кабинеты",
                icon=ft.Icons.PLACE,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Кабинеты")
            ),
        ])

        self.content.content = ft.Column([
            ft.Text("Раздел Данные. Выберите, что просматривать.", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.page.update()

    def _on_back_click(self, e):
        main_menu = MainMenu(self.menu_column, self.content, self.page, self.db_ops, self.toast)
        main_menu.render()

    def _on_section_click(self, section_name: str):
        data_pane = DataPane(self.menu_column, self.content, self.page, self.db_ops, self.toast)
        data_pane.render(section_name)


class DataPane(BasePage):
    def render(self, section_name: str):
        if section_name == "Группы":
            data = self.db_ops.get_groups_with_subgroups()
            columns = ["ID", "Группа", "Подгруппа", "Самообразование", "Разговоры о важном"]
        elif section_name == "Предметы":
            data = self.db_ops.get_subjects_with_module_names()
            columns = ["ID", "Предмет", "Код модуля", "Название модуля"]
        elif section_name == "Преподаватели":
            data = self.db_ops.get_table_data("Преподаватели")
            display_data = []
            for teacher in data:
                preferences = teacher.get('Предпочтения', '')
                display_prefs = self._format_preferences_for_display(preferences)
                display_data.append({
                    'ID': teacher['ID'],
                    'ФИО': teacher['ФИО'],
                    'Предпочтения': display_prefs
                })
            columns = ["ID", "ФИО", "Предпочтения"]
            data = display_data
        elif section_name == "Территории":
            data = self.db_ops.get_table_data("Территории")
            columns = ["ID", "Название", "Цвет"]
        elif section_name == "Кабинеты":
            data = self.db_ops.get_classrooms_with_territory_names()
            columns = ["ID", "Номер кабинета", "Территория", "Вместимость"]
        else:
            data = self.db_ops.get_table_data(section_name)
            columns = self.db_ops.get_table_columns(section_name)

        selected_row = self.table_manager.get_selected_row(section_name)

        delete_button_style = ft.ButtonStyle(
            bgcolor=ft.Colors.RED_400 if selected_row is not None else ft.Colors.GREY_400,
            color="white",
            padding=16,
            shape=ft.CircleBorder()
        )

        edit_button_style = ft.ButtonStyle(
            bgcolor=PALETTE[3] if selected_row is not None else ft.Colors.GREY_400,
            color="white",
            padding=16,
            shape=ft.CircleBorder()
        )

        def on_row_select(index):
            refresh_table()

        def refresh_table():
            selected_row = self.table_manager.get_selected_row(section_name)

            delete_button_style.bgcolor = ft.Colors.RED_400 if selected_row is not None else ft.Colors.GREY_400
            edit_button_style.bgcolor = PALETTE[3] if selected_row is not None else ft.Colors.GREY_400

            data_table = self.table_manager.create_data_table(data, columns, section_name, on_row_select)
            table_scroll.controls = [data_table]
            self.page.update()

        def delete_selected_record(e):
            selected_row = self.table_manager.get_selected_row(section_name)

            if selected_row is None:
                self.toast.show("Выберите запись для удаления!", success=False)
                return

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Подтверждение удаления"),
                content=ft.Text("Вы уверены, что хотите удалить эту запись?"),
                actions=[]
            )

            def on_confirm_delete(evt):
                record = data[selected_row]

                if section_name == "Группы":
                    success = self.db_ops.delete_group_with_subgroups(record['Группа'], record['Подгруппа'])
                elif section_name == "Территории":
                    success = self.db_ops.delete_territory_with_classrooms(record['ID'])
                else:
                    success = self.db_ops.delete_record(section_name, record['ID'])

                if success:
                    self.toast.show("Запись успешно удалена!", success=True)
                    self.table_manager.clear_selection(section_name)
                    self.render(section_name)
                else:
                    self.toast.show("Ошибка при удалении записи!", success=False)

                dialog.open = False
                self.page.update()

            def on_cancel_delete(evt):
                dialog.open = False
                self.page.update()

            dialog.actions = [
                ft.TextButton("Да", on_click=on_confirm_delete),
                ft.TextButton("Нет", on_click=on_cancel_delete)
            ]

            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        def edit_selected_record(e):
            selected_row = self.table_manager.get_selected_row(section_name)

            if selected_row is None:
                self.toast.show("Выберите запись для редактирования!", success=False)
                return

            record = data[selected_row]

            if section_name == "Группы":
                self._render_edit_group_form(record)
            elif section_name == "Предметы":
                self._render_edit_subject_form(record)
            elif section_name == "Преподаватели":
                self._render_edit_teacher_form(record)
            elif section_name == "Кабинеты":
                self._render_edit_classroom_form(record)
            else:
                self._render_edit_standard_form(section_name, record, columns)

        data_table = self.table_manager.create_data_table(data, columns, section_name, on_row_select)

        table_scroll = ft.ListView(
            [data_table],
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False
        )

        edit_button = ft.ElevatedButton(
            text="✏️",
            style=edit_button_style,
            on_click=edit_selected_record,
            tooltip="Редактировать выбранную запись"
        )

        delete_button = ft.ElevatedButton(
            text="🗑️",
            style=delete_button_style,
            on_click=delete_selected_record,
            tooltip="Удалить выбранную запись"
        )

        add_button = ft.ElevatedButton(
            text="🞢",
            style=ft.ButtonStyle(
                bgcolor=PALETTE[3],
                color="white",
                padding=16,
                shape=ft.CircleBorder()
            ),
            on_click=lambda e: self._render_add_form(section_name, columns),
            tooltip="Добавить запись"
        )

        self.content.content = ft.Column([
            ft.Row([
                ft.Text(section_name, size=20, weight="bold", color=PALETTE[2]),
                ft.Row([add_button, edit_button, delete_button], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Container(
                content=table_scroll,
                expand=True,
                padding=10,
                border=ft.border.all(1, color=PALETTE[1]),
                border_radius=5,
            )
        ], expand=True)

        self.page.update()

    def _format_preferences_for_display(self, preferences_str: str) -> str:
        """Форматирование предпочтений для отображения в таблице"""
        if not preferences_str:
            return "Нет"

        try:
            parts = []
            day_blocks = preferences_str.split(';')
            for block in day_blocks:
                if ':' in block:
                    day, lessons = block.split(':')
                    day_name = {
                        'пн': 'Пн',
                        'вт': 'Вт',
                        'ср': 'Ср',
                        'чт': 'Чт',
                        'пт': 'Пт',
                        'сб': 'Сб'
                    }.get(day, day)
                    parts.append(f"{day_name}: {lessons}")

            return '; '.join(parts)
        except:
            return preferences_str

    def _render_add_form(self, table_name: str, columns: List[str]):
        if table_name == "Группы":
            self._render_group_add_form()
        elif table_name == "Предметы":
            self._render_add_subject_form()
        elif table_name == "Преподаватели":
            self._render_teacher_add_form()
        elif table_name == "Кабинеты":
            self._render_add_classroom_form()
        else:
            self._render_standard_add_form(table_name, columns)

    def _render_standard_add_form(self, table_name: str, columns: List[str]):
        form_fields_ref = {}

        def on_form_submit(e):
            data = {}
            errors = []

            # Собираем данные из полей формы
            for column in columns:
                if column.lower() != 'id' and column in form_fields_ref:
                    field = form_fields_ref[column]
                    if hasattr(field, 'value'):
                        # Для dropdown получаем значение, для TextField - value
                        if isinstance(field, ft.Dropdown):
                            data[column] = field.value
                        else:
                            data[column] = field.value
                    else:
                        data[column] = ""

            # Валидация обязательных полей
            required_fields_map = {
                "Территории": ["Название"],
                "Кабинеты": ["Номер", "ТерриторияID"],
                "Преподаватели": ["ФИО"],
                "Модули": ["Код", "Название"],
                "Потоки": ["Название"]
            }

            required_fields = required_fields_map.get(table_name, [])
            for field_name in required_fields:
                value = data.get(field_name, "")
                if not value or (isinstance(value, str) and not value.strip()):
                    errors.append(f"Поле '{field_name}' обязательно для заполнения")

            # Специфическая валидация для разных таблиц
            if not errors:
                if table_name == "Территории":
                    territory_name = data.get('Название', '').strip()
                    if self.db_ops.check_territory_exists(territory_name):
                        errors.append(f"Территория '{territory_name}' уже существует!")

                elif table_name == "Кабинеты":
                    classroom_number = data.get('Номер', '').strip()
                    territory_id = data.get('ТерриторияID')

                    if not territory_id:
                        errors.append("Выберите территорию!")
                    else:
                        territory_id_int = int(territory_id)
                        if self.db_ops.check_classroom_exists(classroom_number, territory_id_int):
                            errors.append(f"Кабинет '{classroom_number}' уже существует на этой территории!")

                elif table_name == "Преподаватели":
                    teacher_name = data.get('ФИО', '').strip()
                    if self.db_ops.check_teacher_exists(teacher_name):
                        errors.append(f"Преподаватель '{teacher_name}' уже существует!")

                elif table_name == "Модули":
                    module_code = data.get('Код', '').strip()
                    if self.db_ops.check_module_exists(module_code):
                        errors.append(f"Модуль с кодом '{module_code}' уже существует!")

            # Проверка числовых полей
            if table_name == "Кабинеты" and data.get('Вместимость'):
                try:
                    capacity = int(data['Вместимость'])
                    if capacity < 0:
                        errors.append("Вместимость не может быть отрицательной!")
                except ValueError:
                    errors.append("Вместимость должна быть числом!")

            if table_name == "Преподаватели":
                if data.get('Нагрузка'):
                    try:
                        workload = int(data['Нагрузка'])
                        if workload < 0:
                            errors.append("Нагрузка не может быть отрицательной!")
                    except ValueError:
                        errors.append("Нагрузка должна быть числом!")

                if data.get('Уроки'):
                    try:
                        lessons = int(data['Уроки'])
                        if lessons < 0:
                            errors.append("Количество уроков не может быть отрицательным!")
                    except ValueError:
                        errors.append("Количество уроков должно быть числом!")

            # Если есть ошибки - показываем их и прерываем сохранение
            if errors:
                for error in errors:
                    self.toast.show(error, success=False)
                return

            # Подготовка данных для сохранения
            clean_data = {}
            for column, value in data.items():
                if column.lower() != 'id':
                    # Обработка пустых значений для числовых полей
                    if table_name == "Кабинеты" and column == "Вместимость" and not value:
                        clean_data[column] = None
                    elif table_name == "Преподаватели" and column in ["Нагрузка", "Уроки"] and not value:
                        clean_data[column] = None
                    else:
                        clean_data[column] = value

            # Сохранение данных
            if self.db_ops.insert_data(table_name, clean_data):
                self.toast.show(f"Данные успешно добавлены!", success=True)
                self.render(table_name)
            else:
                self.toast.show(f"Ошибка при добавлении данных!", success=False)

        title_map = {
            "Территории": "Добавить территорию",
            "Кабинеты": "Добавить кабинет",
            "Преподаватели": "Добавить преподавателя",
            "Модули": "Добавить модуль",
            "Потоки": "Добавить поток"
        }

        title = title_map.get(table_name, f"Добавить {table_name.lower()}")

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2])
        ], spacing=15)

        for column in columns:
            if column.lower() != 'id':
                if table_name == "Кабинеты" and column == "ТерриторияID":
                    territories = self.db_ops.get_territories()
                    territory_options = [ft.dropdown.Option(str(t['ID']), t['Название']) for t in territories]

                    field = ft.Dropdown(
                        label="Территория",
                        width=300,
                        border_color=PALETTE[3],
                        bgcolor=ft.Colors.BLUE_GREY,
                        color=PALETTE[2],
                        options=territory_options,
                    )

                elif column in ["Вместимость", "Нагрузка", "Уроки"]:
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2],
                        keyboard_type=ft.KeyboardType.NUMBER
                    )

                elif column == "Цвет":
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2],
                        hint_text="Например: #FF0000"
                    )

                elif column == "Разговоры о важном":
                    field = ft.Switch(
                        label=column,
                        value=False,
                        label_style=ft.TextStyle(color=PALETTE[2])
                    )

                elif column == "Самообразование":
                    field = ft.Dropdown(
                        label=column,
                        width=200,
                        border_color=PALETTE[3],
                        bgcolor=ft.Colors.BLUE_GREY,
                        color=PALETTE[2],
                        options=[
                            ft.dropdown.Option("нет"),
                            ft.dropdown.Option("пн"),
                            ft.dropdown.Option("вт"),
                            ft.dropdown.Option("ср"),
                            ft.dropdown.Option("чт"),
                            ft.dropdown.Option("пт"),
                            ft.dropdown.Option("сб")
                        ],
                        value="нет"
                    )

                else:
                    # Стандартное текстовое поле
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2]
                    )

                form_fields_ref[column] = field
                scrollable_content.controls.append(field)

        buttons_container = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                    on_click=lambda e: self.render(table_name)
                )
            ], alignment=ft.MainAxisAlignment.END, spacing=20),
            padding=ft.padding.only(top=20),
            border=ft.border.only(top=ft.border.BorderSide(1, PALETTE[1]))
        )

        main_content = ft.Column([
            ft.Container(
                content=ft.ListView(
                    [scrollable_content],
                    expand=True,
                    spacing=0,
                    padding=0
                ),
                expand=True
            ),
            buttons_container
        ], expand=True)

        self.content.content = ft.Container(
            content=main_content,
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_standard_form(self, table_name: str, record: Dict, columns: List[str]):
        if table_name == "Кабинеты":
            self._render_edit_classroom_form(record)
            return
        if table_name == "Преподаватели":
            self._render_edit_teacher_form(record)
            return

        form_fields_ref = {}

        def on_form_submit(e):
            data = {}
            errors = []

            for column in columns:
                if column.lower() != 'id' and column in form_fields_ref:
                    field = form_fields_ref[column]
                    if hasattr(field, 'value'):
                        data[column] = field.value
                    else:
                        data[column] = ""

            required_fields = {
                "Территории": ["Название"],
                "Кабинеты": ["Номер", "ТерриторияID"],
                "Преподаватели": ["ФИО"],
                "Модули": ["Код", "Название"],
                "Потоки": ["Название"]
            }

            if table_name in required_fields:
                for field_name in required_fields[table_name]:
                    if field_name in data:
                        error = Validator.validate_required(str(data[field_name]), field_name)
                        if error:
                            errors.append(error)

            if table_name == "Территории":
                new_territory_name = data.get('Название', '').strip()
                if new_territory_name != record['Название']:
                    if self.db_ops.check_territory_exists(new_territory_name):
                        errors.append(f"Территория '{new_territory_name}' уже существует!")

            elif table_name == "Преподаватели":
                new_teacher_name = data.get('ФИО', '').strip()
                if new_teacher_name != record['ФИО']:
                    if self.db_ops.check_teacher_exists(new_teacher_name):
                        errors.append(f"Преподаватель '{new_teacher_name}' уже существует!")

            elif table_name == "Модули":
                new_module_code = data.get('Код', '').strip()
                if new_module_code != record['Код']:
                    if self.db_ops.check_module_exists(new_module_code):
                        errors.append(f"Модуль с кодом '{new_module_code}' уже существует!")

            clean_data = {}
            for column, value in data.items():
                if column.lower() != 'id':
                    if table_name == "Преподаватели" and column in ["Нагрузка", "Уроки"] and not value:
                        clean_data[column] = None
                    else:
                        clean_data[column] = value

            if self.db_ops.update_record(table_name, record['ID'], clean_data):
                self.toast.show(f"Данные успешно обновлены!", success=True)
                self.render(table_name)
            else:
                self.toast.show(f"Ошибка при обновлении данных!", success=False)

        title_map = {
            "Территории": "Редактировать территорию",
            "Кабинеты": "Редактировать кабинет",
            "Преподаватели": "Редактировать преподавателя",
            "Модули": "Редактировать модуль",
            "Потоки": "Редактировать поток"
        }

        title = title_map.get(table_name, f"Редактировать {table_name.lower()}")

        if table_name.endswith('ы'):
            title = f"Редактировать {table_name[:-1].lower()}у"
        elif table_name.endswith('и'):
            title = f"Редактировать {table_name[:-1].lower()}ь"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2])
        ], spacing=15)

        for column in columns:
            if column.lower() != 'id':
                current_value = record.get(column, "")

                if column in ["Вместимость", "Нагрузка", "Уроки"]:
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2],
                        value=str(current_value) if current_value else "",
                        keyboard_type=ft.KeyboardType.NUMBER
                    )
                elif column == "Разговоры о важном":
                    field = ft.Switch(
                        label=column,
                        value=bool(current_value),
                        label_style=ft.TextStyle(color=PALETTE[2])
                    )
                else:
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2],
                        value=str(current_value) if current_value is not None else ""
                    )
                form_fields_ref[column] = field
                scrollable_content.controls.append(field)

        buttons_container = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                    on_click=lambda e: self.render(table_name)
                )
            ], alignment=ft.MainAxisAlignment.END, spacing=20),
            padding=ft.padding.only(top=20),
            border=ft.border.only(top=ft.border.BorderSide(1, PALETTE[1]))
        )

        main_content = ft.Column([
            ft.Container(
                content=ft.ListView(
                    [scrollable_content],
                    expand=True,
                    spacing=0,
                    padding=0
                ),
                expand=True
            ),
            buttons_container
        ], expand=True)

        self.content.content = ft.Container(
            content=main_content,
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_group_add_form(self):
        def on_form_submit(group_data, subgroups):
            success = self.db_ops.insert_group_with_subgroups(group_data, subgroups)
            if success:
                self.toast.show("Группа и подгруппы успешно добавлены!", success=True)
                self.render("Группы")
            else:
                self.toast.show("Ошибка при добавлении группы! Возможно, такая группа или подгруппа "
                                "уже существует.", success=False)

        def on_form_cancel(e):
            self.render("Группы")

        group_form = GroupForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        group_form.set_page(self.page)

        self.content.content = ft.Container(
            content=group_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_group_form(self, record):
        group_name = record['Группа']
        subgroups = [record['Подгруппа']] if record['Подгруппа'] != "Нет" else []

        def on_form_submit(group_data, subgroups):
            all_groups = self.db_ops.get_groups_with_subgroups()
            group_id = None
            for group in all_groups:
                if group['Группа'] == group_name and group['Подгруппа'] == record['Подгруппа']:
                    group_id = group['ID']
                    break

            if group_id and self.db_ops.update_group_with_subgroups(group_id, group_data, subgroups):
                self.toast.show("Группа успешно обновлена!", success=True)
                self.render("Группы")
            else:
                self.toast.show("Ошибка при обновлении группы!", success=False)

        def on_form_cancel(e):
            self.render("Группы")

        # Правильно получаем значение дня самообразования
        current_self_education = record['Самообразование']
        if current_self_education == "Нет" or not current_self_education:
            current_self_education = "нет"

        group_data = {
            'Название': record['Группа'],
            'Самообразование': current_self_education,  # Передаем правильное значение
            'Разговоры о важном': 1 if record['Разговоры о важном'] == "Да" else 0
        }

        from ui.forms import GroupForm
        group_form = GroupForm(
            on_form_submit, on_form_cancel, self.db_ops, self.toast,
            edit_mode=True, group_data=group_data, subgroups=subgroups
        )
        group_form.set_page(self.page)

        self.content.content = ft.Container(
            content=group_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_add_classroom_form(self):
        def on_form_submit(classroom_data):
            success = self.db_ops.insert_data("Кабинеты", classroom_data)
            if success:
                self.toast.show("Кабинет успешно добавлен!", success=True)
                self.render("Кабинеты")
            else:
                self.toast.show("Ошибка при добавлении кабинета!", success=False)

        def on_form_cancel(e):
            self.render("Кабинеты")

        classroom_form = ClassroomForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        classroom_form.set_page(self.page)

        self.content.content = ft.Container(
            content=classroom_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_classroom_form(self, record):
        def on_form_submit(classroom_data):
            current_territory_id = self.db_ops.get_territory_id_by_name(record['Территория'])

            if (classroom_data['Номер'] != record['Номер кабинета'] or
                    classroom_data['ТерриторияID'] != current_territory_id):

                if self.db_ops.check_classroom_exists(classroom_data['Номер'], classroom_data['ТерриторияID']):
                    self.toast.show(f"Кабинет '{classroom_data['Номер']}' уже существует на этой территории!",
                                    success=False)
                    return

            success = self.db_ops.update_record("Кабинеты", record['ID'], classroom_data)
            if success:
                self.toast.show("Кабинет успешно обновлен!", success=True)
                self.render("Кабинеты")
            else:
                self.toast.show("Ошибка при обновлении кабинета!", success=False)

        def on_form_cancel(e):
            self.render("Кабинеты")

        current_territory_id = self.db_ops.get_territory_id_by_name(record['Территория'])

        classroom_data = {
            'Номер': record['Номер кабинета'],
            'ТерриторияID': current_territory_id,
            'Вместимость': record.get('Вместимость')
        }

        classroom_form = ClassroomForm(
            on_form_submit, on_form_cancel, self.db_ops, self.toast,
            edit_mode=True, classroom_data=classroom_data
        )
        classroom_form.set_page(self.page)

        self.content.content = ft.Container(
            content=classroom_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_add_subject_form(self):
        def on_form_submit(subject_data, classroom_ids):
            success = self.db_ops.insert_subject_with_classrooms(subject_data, classroom_ids)
            if success:
                self.toast.show("Предмет успешно добавлен!", success=True)
                self.render("Предметы")
            else:
                self.toast.show("Ошибка при добавлении предмета!", success=False)

        def on_form_cancel(e):
            self.render("Предметы")

        from ui.forms import SubjectForm
        subject_form = SubjectForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        subject_form.set_page(self.page)

        self.content.content = ft.Container(
            content=subject_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_subject_form(self, record):
        def on_form_submit(subject_data, classroom_ids):
            success = self.db_ops.update_subject_with_classrooms(record['ID'], subject_data, classroom_ids)
            if success:
                self.toast.show("Предмет успешно обновлен!", success=True)
                self.render("Предметы")
            else:
                self.toast.show("Ошибка при обновлении предмета!", success=False)

        def on_form_cancel(e):
            self.render("Предметы")

        current_classrooms = self.db_ops.get_classrooms_by_subject(record['ID'])
        classroom_ids = [classroom['ID'] for classroom in current_classrooms]

        subject_data = {
            'Название': record['Предмет'],
            'Модуль': record['Код модуля']
        }

        from ui.forms import SubjectForm
        subject_form = SubjectForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                   edit_mode=True, subject_data=subject_data, classroom_ids=classroom_ids)
        subject_form.set_page(self.page)

        self.content.content = ft.Container(
            content=subject_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_teacher_add_form(self):
        def on_form_submit(teacher_data):
            success = self.db_ops.insert_data("Преподаватели", teacher_data)
            if success:
                self.toast.show("Преподаватель успешно добавлен!", success=True)
                self.render("Преподаватели")
            else:
                self.toast.show("Ошибка при добавлении преподавателя!", success=False)

        def on_form_cancel(e):
            self.render("Преподаватели")

        teacher_form = TeacherForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        teacher_form.set_page(self.page)

        self.content.content = ft.Container(
            content=teacher_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_teacher_form(self, record):
        def on_form_submit(teacher_data):
            success = self.db_ops.update_record("Преподаватели", record['ID'], teacher_data)
            if success:
                self.toast.show("Преподаватель успешно обновлен!", success=True)
                self.render("Преподаватели")
            else:
                self.toast.show("Ошибка при обновлении преподавателя!", success=False)

        def on_form_cancel(e):
            self.render("Преподаватели")

        teacher_data = {
            'ФИО': record['ФИО'],
            'Дни': record['Дни'] if record['Дни'] != 'Нет' else '',
            'Уроки': record['Уроки'] if record['Уроки'] != 'Нет' else ''
        }

        teacher_form = TeacherForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                   edit_mode=True, teacher_data=teacher_data)
        teacher_form.set_page(self.page)

        self.content.content = ft.Container(
            content=teacher_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()