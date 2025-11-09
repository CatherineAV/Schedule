import flet as ft
from typing import Callable, List, Dict, Any, Optional
from database.operations import DBOperations
from ui.components import Toast, DataTableManager, PALETTE
from ui.forms import GroupForm, ClassroomForm


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
            columns = ["ID", "ФИО", "Нагрузка", "Дни", "Уроки"]
        elif section_name == "Территории":
            data = self.db_ops.get_table_data("Территории")
            columns = ["ID", "Название", "Цвет"]
        elif section_name == "Кабинеты":
            data = self.db_ops.get_classrooms_with_territory_names()
            columns = ["ID", "Номер кабинета", "Территория", "Вместимость"]  # "Номер" вместо "Номер кабинета"
        else:
            data = self.db_ops.get_table_data(section_name)
            columns = self.db_ops.get_table_columns(section_name)

        # Создаем переменные для хранения состояния кнопок
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
            # Просто обновляем таблицу, цвет кнопок обновим через refresh_table
            refresh_table()

        def refresh_table():
            selected_row = self.table_manager.get_selected_row(section_name)

            # Обновляем стили кнопок
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
                    # Используем новый метод для удаления территории с кабинетами
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

        # Создаем кнопки с правильными стилями
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

    def _render_edit_group_form(self, record):
        # Получаем все подгруппы для этой группы
        group_name = record['Группа']
        subgroups = [record['Подгруппа']] if record['Подгруппа'] != "Нет" else []

        def on_form_submit(group_data, subgroups):
            # Находим ID группы для обновления
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

        group_data = {
            'Название': record['Группа'],
            'Самообразование': record['Самообразование'] if record['Самообразование'] != "Нет" else None,
            'Разговоры о важном': 1 if record['Разговоры о важном'] == "Да" else 0
        }

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

    def _render_edit_standard_form(self, table_name: str, record: Dict, columns: List[str]):
        form_fields_ref = {}

        def on_form_submit(e):
            data = {}
            for column in columns:
                if column.lower() != 'id' and column in form_fields_ref:
                    data[column] = form_fields_ref[column].value

            if self.db_ops.update_record(table_name, record['ID'], data):
                self.toast.show(f"Данные успешно обновлены в {table_name}!", success=True)
                self.render(table_name)
            else:
                self.toast.show(f"Ошибка при обновлении данных в {table_name}", success=False)

        form_content = ft.Column([
            ft.Text(f"Редактировать запись в {table_name}", size=18, weight="bold", color=PALETTE[2])
        ], spacing=15)

        for column in columns:
            if column.lower() != 'id':
                # Для кабинетов нужно преобразовать TerritoryID в выпадающий список
                if table_name == "Кабинеты" and column == "ТерриторияID":
                    # Создаем выпадающий список для территорий
                    territories = self.db_ops.get_territories()
                    territory_options = [ft.dropdown.Option(str(t['ID']), t['Название']) for t in territories]

                    field = ft.Dropdown(
                        label=column,
                        width=300,
                        border_color=PALETTE[3],
                        bgcolor=ft.Colors.BLUE_GREY,
                        color=PALETTE[2],
                        options=territory_options,
                        value=str(record.get(column, ""))
                    )
                else:
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2],
                        value=str(record.get(column, ""))
                    )
                form_fields_ref[column] = field
                form_content.controls.append(field)

        # Добавляем кнопки в едином стиле
        form_content.controls.extend([
            ft.Container(expand=True),
            ft.Container(
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
        ])

        # Оборачиваем в ListView для прокрутки
        scrollable_content = ft.Column([
            ft.ListView(
                [form_content],
                expand=True,
                spacing=0,
                padding=0
            )
        ], expand=True)

        self.content.content = ft.Container(
            content=scrollable_content,
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_add_form(self, table_name: str, columns: List[str]):
        if table_name == "Группы":
            self._render_group_add_form()
        elif table_name == "Предметы":
            self._render_add_subject_form()
        elif table_name == "Кабинеты":
            self._render_add_classroom_form()
        else:
            self._render_standard_add_form(table_name, columns)

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
            success = self.db_ops.update_record("Кабинеты", record['ID'], classroom_data)
            if success:
                self.toast.show("Кабинет успешно обновлен!", success=True)
                self.render("Кабинеты")
            else:
                self.toast.show("Ошибка при обновлении кабинета!", success=False)

        def on_form_cancel(e):
            self.render("Кабинеты")

        # Используем правильные ключи из БД
        classroom_data = {
            'Номер': record['Номер кабинета'],  # Берем значение из колонки "Номер кабинета"
            'ТерриторияID': None,
            'Вместимость': record.get('Вместимость')
        }

        # Находим ID территории по названию
        territories = self.db_ops.get_territories()
        territory_id = None
        for territory in territories:
            if territory['Название'] == record['Территория']:
                territory_id = territory['ID']
                break

        classroom_data['ТерриторияID'] = territory_id

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

    def _render_group_add_form(self):
        def on_form_submit(group_data, subgroups):  # Добавляем аргументы
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

    def _render_standard_add_form(self, table_name: str, columns: List[str]):
        form_fields_ref = {}

        def on_form_submit(e):
            data = {}
            for column in columns:
                if column.lower() != 'id' and column in form_fields_ref:
                    data[column] = form_fields_ref[column].value

            if self.db_ops.insert_data(table_name, data):
                self.toast.show(f"Данные успешно добавлены в {table_name}!", success=True)
                self.render(table_name)
            else:
                self.toast.show(f"Ошибка при добавлении данных в {table_name}", success=False)

        # Определяем заголовок в зависимости от таблицы
        title_map = {
            "Территории": "Добавить территорию",
            "Кабинеты": "Добавить кабинет",
            "Преподаватели": "Добавить преподавателя",
            "Предметы": "Добавить предмет",
            "Группы": "Добавить группу",
            "Модули": "Добавить модуль"
        }
        title = title_map.get(table_name, f"Добавить {table_name.lower()}")

        # Прокручиваемая область
        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2])  # Используем правильный заголовок
        ], spacing=15)

        for column in columns:
            if column.lower() != 'id':
                field = ft.TextField(
                    label=column,
                    border_color=PALETTE[3],
                    color=PALETTE[2]
                )
                form_fields_ref[column] = field
                scrollable_content.controls.append(field)

        # Кнопки ВНЕ прокручиваемой области
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

        # Основной контейнер
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

        # Получаем текущие кабинеты предмета для предзаполнения
        current_classrooms = self.db_ops.get_classrooms_by_subject(record['ID'])
        classroom_ids = [classroom['ID'] for classroom in current_classrooms]

        subject_data = {
            'Название': record['Предмет'],
            'Модуль': record['Код модуля']
        }

        from ui.forms import SubjectForm
        subject_form = SubjectForm(
            on_form_submit, on_form_cancel, self.db_ops, self.toast,
            edit_mode=True, subject_data=subject_data, classroom_ids=classroom_ids
        )
        subject_form.set_page(self.page)

        self.content.content = ft.Container(
            content=subject_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()
