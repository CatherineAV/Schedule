import flet as ft
from typing import List, Dict
from database.operations import DBOperations
from database.settings_manager import SettingsManager
from ui.components import PALETTE, Toast, DataTableManager, SearchFilterBar
from ui.forms import ModuleForm, StreamForm, GroupsManagementForm
from ui.forms import MultiWorkloadForm, WorkloadForm, ClassroomForm, TeacherForm, GroupForm, SubjectForm, TerritoryForm


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
            ft.Text("Добро пожаловать!", size=20, weight="bold", color=PALETTE[2]),
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Выберите пункт из меню слева", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.page.update()

    def _on_data_click(self, e):
        data_menu = DataMenu(self.menu_column, self.content, self.page, self.db_ops, self.toast)
        data_menu.render()

    def _on_settings_click(self, e):
        settings_page = SettingsPage(self.menu_column, self.content, self.page, self.db_ops, self.toast)
        settings_page.render()

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
                "Модули",
                icon=ft.Icons.DATA_OBJECT,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Модули")
            ),
            ft.ElevatedButton(
                "Дисциплины",
                icon=ft.Icons.BOOK,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Дисциплины")
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
                icon=ft.Icons.ROOM,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Кабинеты")
            ),
            ft.ElevatedButton(
                "Нагрузка",
                icon=ft.Icons.SCHEDULE,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._on_section_click("Нагрузка")
            ),
        ])

        self.content.content = ft.Column([
            ft.Text("Управления данными расписания", size=20, weight="bold", color=PALETTE[2]),
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Выберите раздел данных из меню слева", size=16, color=PALETTE[0])
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
            data = self.db_ops.get_groups()
            columns = ["ID", "Группа", "Подгруппа", "Самообразование", "Разговоры о важном"]
        elif section_name == "Дисциплины":
            data = self.db_ops.get_subjects_with_module_names()
            columns = ["ID", "Дисциплина", "Код модуля", "Название модуля"]
        elif section_name == "Преподаватели":
            data = self.db_ops.get_teachers_with_preferences()
            columns = ["ID", "ФИО", "Совместитель", "Дни занятий", "Территория"]
        elif section_name == "Территории":
            data = self.db_ops.get_table_data("Территории")
            columns = ["ID", "Территория", "Цвет"]
        elif section_name == "Кабинеты":
            data = self.db_ops.get_classrooms_with_territory_names()
            columns = ["ID", "Номер кабинета", "Территория", "Вместимость"]
        elif section_name == "Модули":
            data = self.db_ops.get_modules()
            columns = ["ID", "Код", "Название"]
        elif section_name == "Нагрузка":
            data = self.db_ops.get_workloads()
            columns = ["ID", "Преподаватель", "Дисциплина", "Группа", "Подгруппа", "Часы в неделю"]
        else:
            data = self.db_ops.get_table_data(section_name)
            columns = self.db_ops.get_table_columns(section_name)

        selected_row = self.table_manager.get_selected_row(section_name)

        self.filtered_data = data.copy()

        def on_row_select(index):
            refresh_table()

        def refresh_table():
            selected_row = self.table_manager.get_selected_row(section_name)

            if selected_row is not None:
                edit_button.bgcolor = PALETTE[3]
                delete_button.bgcolor = ft.Colors.RED_400
            else:
                edit_button.bgcolor = ft.Colors.GREY_400
                delete_button.bgcolor = ft.Colors.GREY_400

            data_table = self.table_manager.create_data_table(
                self.filtered_data, columns, section_name, on_row_select
            )
            table_scroll.controls = [data_table]

            self.page.update()

        def filter_data(search_text):
            if not search_text:
                self.filtered_data = data.copy()
            else:
                self.filtered_data = []
                for row in data:
                    match_found = False
                    for col in columns:
                        if col != 'ID' and col in row:
                            value = str(row.get(col, "")).lower()
                            if search_text in value:
                                match_found = True
                                break
                    if match_found:
                        self.filtered_data.append(row)

            refresh_table()

        def apply_filters(filters):
            if not filters:
                self.filtered_data = data.copy()
            else:
                filtered = data.copy()

                if section_name == "Нагрузка":
                    for key, value in filters.items():
                        if value:
                            if key == 'teacher':
                                filtered = [row for row in filtered if row.get('Преподаватель', '') == value]
                            elif key == 'subject':
                                filtered = [row for row in filtered if row.get('Дисциплина', '') == value]
                            elif key == 'group':
                                if ' - ' in value:
                                    group_name, subgroup = value.split(' - ')
                                    filtered = [row for row in filtered if
                                                row.get('Группа', '') == group_name and
                                                row.get('Подгруппа', '') == subgroup]
                                else:
                                    filtered = [row for row in filtered if
                                                row.get('Группа', '') == value]

                            elif key == 'with_subgroups_only' and value:
                                filtered = [row for row in filtered if
                                            row.get('Подгруппа', '') and
                                            row.get('Подгруппа', '') != 'Нет' and
                                            row.get('Подгруппа', '') != 'None']

                elif section_name == "Преподаватели":
                    if 'active_only' in filters and filters['active_only']:
                        pass

                self.filtered_data = filtered

            refresh_table()

        search_bar = SearchFilterBar(
            on_search=filter_data,
            on_filter=apply_filters,
            section_name=section_name,
            db_operations=self.db_ops
        )
        search_bar.page = self.page

        data_table = self.table_manager.create_data_table(
            self.filtered_data, columns, section_name, on_row_select
        )

        table_scroll = ft.ListView(
            [data_table],
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False
        )

        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_color=ft.Colors.WHITE,
            bgcolor=PALETTE[3],
            tooltip="Добавить запись",
            on_click=lambda e: self._render_add_form(section_name, columns),
        )

        def edit_selected_record(e):
            selected_row_index = self.table_manager.get_selected_row(section_name)

            if selected_row_index is None:
                self.toast.show("Выберите запись для редактирования!", success=False)
                return

            # Используем filtered_data для получения правильного индекса
            if 0 <= selected_row_index < len(self.filtered_data):
                record = self.filtered_data[selected_row_index]
            else:
                record = data[selected_row_index] if selected_row_index < len(data) else None

            if not record:
                return

            if section_name == "Группы":
                self._render_edit_group_form(record)
            elif section_name == "Дисциплины":
                self._render_edit_subject_form(record)
            elif section_name == "Преподаватели":
                self._render_edit_teacher_form(record)
            elif section_name == "Кабинеты":
                self._render_edit_classroom_form(record)
            elif section_name == "Модули":
                self._render_edit_module_form(record)
            elif section_name == "Территории":
                self._render_edit_territory_form(record)
            elif section_name == "Нагрузка":
                self._render_edit_workload_form(record)
            else:
                self._render_edit_standard_form(section_name, record, columns)

        def delete_selected_record(e):
            selected_row_index = self.table_manager.get_selected_row(section_name)

            if selected_row_index is None:
                self.toast.show("Выберите запись для удаления!", success=False)
                return

            # Используем filtered_data для получения правильного индекса
            if 0 <= selected_row_index < len(self.filtered_data):
                record = self.filtered_data[selected_row_index]
            else:
                record = data[selected_row_index] if selected_row_index < len(data) else None

            if not record:
                return

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Подтверждение удаления"),
                content=ft.Text(f"Вы уверены, что хотите удалить выбранную запись?"),
                actions=[]
            )

            def on_confirm_delete(evt):
                success = False

                if section_name == "Группы":
                    success = self.db_ops.delete_group(record['ID'])
                elif section_name == "Территории":
                    success = self.db_ops.delete_territory_with_classrooms(record['ID'])
                elif section_name == "Дисциплины":
                    success = self.db_ops.delete_record("Дисциплины", record['ID'])
                elif section_name == "Преподаватели":
                    success = self.db_ops.delete_record("Преподаватели", record['ID'])
                elif section_name == "Кабинеты":
                    success = self.db_ops.delete_record("Кабинеты", record['ID'])
                elif section_name == "Модули":
                    success = self.db_ops.delete_module(record['ID'])
                elif section_name == "Нагрузка":
                    success = self.db_ops.delete_workload(record['ID'])
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

        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            icon_color=ft.Colors.WHITE,
            bgcolor=PALETTE[3] if selected_row is not None else ft.Colors.GREY_400,
            tooltip="Редактировать выбранную запись",
            on_click=edit_selected_record,
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_400 if selected_row is not None else ft.Colors.GREY_400,
            tooltip="Удалить выбранную запись",
            on_click=delete_selected_record,
        )

        self.content.content = ft.Column([
            ft.Row([
                ft.Text(section_name, size=20, weight="bold", color=PALETTE[2]),
                ft.Row([add_button, edit_button, delete_button], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Container(
                content=search_bar.build(),
                padding=ft.padding.only(bottom=10)
            ),

            ft.Divider(height=10, color=PALETTE[1]),

            ft.Container(
                content=table_scroll,
                expand=True,
                padding=10,
                border=ft.border.all(1, color=PALETTE[1]),
                border_radius=5,
            )
        ], expand=True)

        self.page.update()

    def _render_add_form(self, table_name: str, columns: List[str]):
        if table_name == "Группы":
            self._render_group_add_form()
        elif table_name == "Дисциплины":
            self._render_add_subject_form()
        elif table_name == "Преподаватели":
            self._render_teacher_add_form()
        elif table_name == "Кабинеты":
            self._render_add_classroom_form()
        elif table_name == "Модули":
            self._render_add_module_form()
        elif table_name == "Территории":
            self._render_add_territory_form()
        elif table_name == "Нагрузка":
            self._render_workload_add_form()
        else:
            self._render_standard_add_form(table_name, columns)

    # ========== ФОРМЫ ДОБАВЛЕНИЯ ==========

    def _render_group_add_form(self):
        def on_form_submit(group_data):
            success = self.db_ops.insert_group(group_data)
            if success:
                self.toast.show("Группа успешно добавлена!", success=True)
                self.render("Группы")
            else:
                self.toast.show(
                    "Ошибка при добавлении группы! Возможно, такая группа уже существует.",
                    success=False)

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

    def _render_add_subject_form(self):
        def on_form_submit(subject_data, classroom_ids):
            success = self.db_ops.insert_subject_with_classrooms(subject_data, classroom_ids)
            if success:
                self.toast.show("Дисциплина успешно добавлена!", success=True)
                self.render("Дисциплины")
            else:
                self.toast.show("Ошибка при добавлении дисциплины!", success=False)

        def on_form_cancel(e):
            self.render("Дисциплины")

        subject_form = SubjectForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        subject_form.set_page(self.page)

        self.content.content = ft.Container(
            content=subject_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_teacher_add_form(self):
        def on_form_submit(teacher_data):
            territory_ids = teacher_data.get('Территории', [])
            success = self.db_ops.insert_teacher_with_territories(teacher_data, territory_ids)
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

    def _render_add_module_form(self):
        def on_form_submit(module_data):
            success = self.db_ops.insert_module(module_data['Код'], module_data['Название'])
            if success:
                self.toast.show("Модуль успешно добавлен!", success=True)
                self.render("Модули")
            else:
                self.toast.show("Ошибка при добавлении модуля!", success=False)

        def on_form_cancel(e):
            self.render("Модули")

        module_form = ModuleForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        module_form.set_page(self.page)

        self.content.content = ft.Container(
            content=module_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_add_territory_form(self):
        def on_form_submit(territory_data):
            success = self.db_ops.insert_data("Территории", territory_data)
            if success:
                self.toast.show("Территория успешно добавлена!", success=True)
                self.render("Территории")
            else:
                self.toast.show("Ошибка при добавлении территории!", success=False)

        def on_form_cancel(e):
            self.render("Территории")

        territory_form = TerritoryForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        territory_form.set_page(self.page)

        self.content.content = ft.Container(
            content=territory_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    # ========== ФОРМЫ РЕДАКТИРОВАНИЯ ==========

    def _render_edit_group_form(self, record):
        def on_form_submit(group_data):
            success = self.db_ops.update_group(record['ID'], group_data)
            if success:
                self.toast.show("Группа успешно обновлена!", success=True)
                self.render("Группы")
            else:
                self.toast.show("Ошибка при обновлении группы!", success=False)

        def on_form_cancel(e):
            self.render("Группы")

        group_data = {
            'Группа': record['Группа'],
            'Подгруппа': record['Подгруппа'],
            'Самообразование': record['Самообразование'] if record['Самообразование'] else 'Нет',
            'Разговоры о важном': 1 if record['Разговоры о важном'] == "Да" or record['Разговоры о важном'] == 1 else 0
        }

        group_form = GroupForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                               edit_mode=True, group_data=group_data)
        group_form.current_group_id = record['ID']
        group_form.set_page(self.page)

        self.content.content = ft.Container(
            content=group_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_subject_form(self, record):
        def on_form_submit(subject_data, classroom_ids):
            success = self.db_ops.update_subject_with_classrooms(record['ID'], subject_data, classroom_ids)
            if success:
                self.toast.show("Дисциплина успешно обновлена!", success=True)
                self.render("Дисциплины")
            else:
                self.toast.show("Ошибка при обновлении дисциплины!", success=False)

        def on_form_cancel(e):
            self.render("Дисциплины")

        current_classrooms = self.db_ops.get_classrooms_by_subject(record['ID'])
        classroom_ids = [classroom['ID'] for classroom in current_classrooms]

        subject_data = {
            'Дисциплина': record['Дисциплина'],
            'Модуль': record['Код модуля']
        }

        subject_form = SubjectForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                   edit_mode=True, subject_data=subject_data, classroom_ids=classroom_ids)
        subject_form.set_page(self.page)

        self.content.content = ft.Container(
            content=subject_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_teacher_form(self, record):
        def on_form_submit(teacher_data):
            territory_ids = teacher_data.pop('Территории', [])
            success = self.db_ops.update_teacher_with_territories(record['ID'], teacher_data, territory_ids)
            if success:
                self.toast.show("Преподаватель успешно обновлен!", success=True)
                self.render("Преподаватели")
            else:
                self.toast.show("Ошибка при обновлении преподавателя!", success=False)

        def on_form_cancel(e):
            self.render("Преподаватели")

        teacher_territories = self.db_ops.get_teacher_territories(record['ID'])
        is_part_timer = record.get('Совместитель', 'Нет') == 'Да'

        days_str = record.get('Дни занятий', '')
        if days_str == 'Любые' or not days_str:
            days_str = ''

        territory_ids = [t['ID'] for t in teacher_territories]

        teacher_data = {
            'ФИО': record['ФИО'],
            'Совместитель': is_part_timer,
            '[Дни занятий]': days_str,
            'Территории': territory_ids
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

    def _render_edit_classroom_form(self, record):
        def on_form_submit(classroom_data):
            current_territory_id = self.db_ops.get_territory_id_by_name(record['Территория'])

            if (classroom_data['Кабинет'] != record['Номер кабинета'] or
                    classroom_data['ТерриторияID'] != current_territory_id):

                if self.db_ops.check_classroom_exists(classroom_data['Кабинет'], classroom_data['ТерриторияID']):
                    self.toast.show(f"Кабинет '{classroom_data['Кабинет']}' уже существует на этой территории!",
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
            'Кабинет': record['Номер кабинета'],
            'ТерриторияID': current_territory_id,
            'Вместимость': record.get('Вместимость')
        }

        classroom_form = ClassroomForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                       edit_mode=True, classroom_data=classroom_data)
        classroom_form.set_page(self.page)

        self.content.content = ft.Container(
            content=classroom_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_module_form(self, record):
        def on_form_submit(module_data):
            success = self.db_ops.update_module(record['ID'], module_data['Код'], module_data['Название'])
            if success:
                self.toast.show("Модуль успешно обновлен!", success=True)
                self.render("Модули")
            else:
                self.toast.show("Ошибка при обновлении модуля!", success=False)

        def on_form_cancel(e):
            self.render("Модули")

        module_data = {
            'ID': record['ID'],
            'Код': record['Код'],
            'Название': record['Название']
        }

        module_form = ModuleForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                 edit_mode=True, module_data=module_data)
        module_form.set_page(self.page)

        self.content.content = ft.Container(
            content=module_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_territory_form(self, record):
        def on_form_submit(territory_data):
            success = self.db_ops.update_record("Территории", record['ID'], territory_data)
            if success:
                self.toast.show("Территория успешно обновлена!", success=True)
                self.render("Территории")
            else:
                self.toast.show("Ошибка при обновлении территории!", success=False)

        def on_form_cancel(e):
            self.render("Территории")

        territory_data = {
            'Территория': record['Территория'],
            'Цвет': record.get('Цвет', '#FFFFFF')
        }

        territory_form = TerritoryForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                       edit_mode=True, territory_data=territory_data)
        territory_form.set_page(self.page)

        self.content.content = ft.Container(
            content=territory_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_standard_add_form(self, table_name: str, columns: List[str]):

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

            for column, value in data.items():
                if column != "Цвет" and column != "Вместимость" and not value:
                    errors.append(f"Поле '{column}' обязательно для заполнения")

            if errors:
                for error in errors:
                    self.toast.show(error, success=False)
                return

            if self.db_ops.insert_data(table_name, data):
                self.toast.show(f"Данные успешно добавлены!", success=True)
                self.render(table_name)
            else:
                self.toast.show(f"Ошибка при добавлении данных!", success=False)

        title = f"Добавить {self._get_table_russian_name(table_name).lower()}"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2])
        ], spacing=15)

        for column in columns:
            if column.lower() != 'id':
                if column == "Цвет":
                    field = ft.TextField(
                        label=column,
                        border_color=PALETTE[3],
                        color=PALETTE[2],
                        hint_text="#FFFFFF"
                    )
                else:
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

    def _render_workload_add_form(self):
        def on_form_submit(workloads_data):
            success_count = 0
            error_count = 0

            for workload_data in workloads_data:
                success = self.db_ops.insert_workload(workload_data)
                if success:
                    success_count += 1
                else:
                    error_count += 1

            if success_count > 0:
                if error_count > 0:
                    self.toast.show(f"Добавлено {success_count} из {len(workloads_data)} нагрузок. "
                                    f"{error_count} не добавлено.", success=True)
                else:
                    self.toast.show(f"Успешно добавлено {success_count} нагрузок!", success=True)
                self.render("Нагрузка")
            else:
                self.toast.show("Не удалось добавить ни одной нагрузки!", success=False)

        def on_form_cancel(e):
            self.render("Нагрузка")

        workload_form = MultiWorkloadForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        workload_form.set_page(self.page)

        self.content.content = ft.Container(
            content=workload_form.build(),
            padding=20,
            expand=True
        )

        self.page.update()

    def _render_edit_workload_form(self, record):
        def on_form_submit(workload_data):
            success = self.db_ops.update_workload(record['ID'], workload_data)
            if success:
                self.toast.show("Нагрузка успешно обновлена!", success=True)
                self.render("Нагрузка")
            else:
                self.toast.show("Ошибка при обновлении нагрузки!", success=False)

        def on_form_cancel(e):
            self.render("Нагрузка")

        group_name = record['Группа']
        subgroup = record.get('Подгруппа', 'Нет')
        if subgroup and subgroup != "Нет" and subgroup != "None":
            group_display = f"{group_name} - {subgroup}"
        else:
            group_display = group_name

        workload_data = {
            'Преподаватель': record['Преподаватель'],
            'Дисциплина': record['Дисциплина'],
            'Группа': record['Группа'],
            'Подгруппа': record.get('Подгруппа', 'Нет'),
            'Часы в неделю': record['Часы в неделю']
        }

        workload_form = WorkloadForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                     edit_mode=True, workload_data=workload_data)

        workload_form.workload_id = record['ID']

        workload_form.set_page(self.page)

        self.content.content = ft.Container(
            content=workload_form.build(),
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
                    field = form_fields_ref[column]
                    if hasattr(field, 'value'):
                        data[column] = field.value
                    else:
                        data[column] = ""

            if table_name == "Модули":
                success = self.db_ops.update_module(record['Код'], data)
            elif table_name == "Нагрузка":
                success = self.db_ops.update_workload(record['ID'], data)
            else:
                success = self.db_ops.update_record(table_name, record['ID'], data)

            if success:
                self.toast.show(f"Данные успешно обновлены!", success=True)
                self.render(table_name)
            else:
                self.toast.show(f"Ошибка при обновлении данных!", success=False)

        title = f"Редактировать {self._get_table_russian_name(table_name).lower()}"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2])
        ], spacing=15)

        for column in columns:
            if column.lower() != 'id':
                current_value = record.get(column, "")
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

    def _get_table_russian_name(self, table_name: str) -> str:
        names = {
            "Группы": "Группу",
            "Дисциплины": "Дисциплину",
            "Преподаватели": "Преподавателя",
            "Территории": "Территорию",
            "Кабинеты": "Кабинет",
            "Модули": "Модуль"
        }
        return names.get(table_name, table_name)


class SettingsPage(BasePage):
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
                "Потоки групп",
                icon=ft.Icons.MERGE,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._show_streams_section()
            ),
            ft.ElevatedButton(
                "Управление группами",
                icon=ft.Icons.TUNE,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: self._show_groups_management()
            ),
        ])

        self._show_main_settings()
        self.page.update()

    def _show_groups_management(self):
        def on_form_submit(params):
            self.toast.show("Настройки групп сохранены!", success=True)
            self._show_main_settings()

        def on_form_cancel(e):
            self._on_back_click(e)

        settings_manager = SettingsManager(self.db_ops)
        groups_form = GroupsManagementForm(
            on_form_submit, on_form_cancel, self.db_ops, settings_manager, self.toast
        )
        groups_form.set_page(self.page)

        self.content.content = ft.Container(
            content=groups_form.build(),
            padding=20,
            expand=True
        )
        self.page.update()

    def _on_back_click(self, e):
        main_menu = MainMenu(self.menu_column, self.content, self.page, self.db_ops, self.toast)
        main_menu.render()

    def _show_main_settings(self):
        self.content.content = ft.Column([
            ft.Text("Настройки генерации расписания", size=20, weight="bold", color=PALETTE[2]),
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Выберите раздел настроек из меню слева", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _show_streams_section(self):
        settings_manager = SettingsManager(self.db_ops)
        streams = settings_manager.get_streams_with_subjects()
        columns = ["ID", "Поток", "Группы", "Дисциплины"]
        selected_row = self.table_manager.get_selected_row("Потоки")

        self.filtered_streams = streams.copy()

        def on_row_select(index):
            refresh_table()

        def refresh_table():
            nonlocal selected_row
            selected_row = self.table_manager.get_selected_row("Потоки")

            if selected_row is not None:
                edit_button.bgcolor = PALETTE[3]
                delete_button.bgcolor = ft.Colors.RED_400
            else:
                edit_button.bgcolor = ft.Colors.GREY_400
                delete_button.bgcolor = ft.Colors.GREY_400

            data_table = self.table_manager.create_data_table(
                self.filtered_streams, columns, "Потоки", on_row_select
            )
            table_scroll.controls = [data_table]

            self.page.update()

        def filter_data(search_text):
            if not search_text:
                self.filtered_streams = streams.copy()
            else:
                self.filtered_streams = []
                for stream in streams:
                    if (search_text in str(stream.get('Поток', '')).lower() or
                            search_text in str(stream.get('Группы', '')).lower() or
                            search_text in str(stream.get('Дисциплины', '')).lower()):
                        self.filtered_streams.append(stream)

            refresh_table()

        def apply_filters(filters):
            if not filters:
                self.filtered_streams = streams.copy()
            else:
                self.filtered_streams = streams.copy()
            refresh_table()

        search_bar = SearchFilterBar(on_search=filter_data, on_filter=apply_filters)
        search_bar.page = self.page

        data_table = self.table_manager.create_data_table(
            self.filtered_streams,
            columns,
            "Потоки",
            on_row_select
        )

        table_scroll = ft.ListView(
            [data_table],
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False
        )

        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_color=ft.Colors.WHITE,
            bgcolor=PALETTE[3],
            tooltip="Добавить поток",
            on_click=lambda e: self._render_add_stream_form(settings_manager),
        )

        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            icon_color=ft.Colors.WHITE,
            bgcolor=PALETTE[3] if selected_row is not None else ft.Colors.GREY_400,
            tooltip="Редактировать выбранный поток",
            on_click=lambda e: self._edit_selected_stream(settings_manager),
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_400 if selected_row is not None else ft.Colors.GREY_400,
            tooltip="Удалить выбранный поток",
            on_click=lambda e: self._delete_selected_stream(settings_manager),
        )

        self.content.content = ft.Column([
            ft.Row([
                ft.Text("Потоки групп", size=20, weight="bold", color=PALETTE[2]),
                ft.Row([add_button, edit_button, delete_button], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Container(
                content=search_bar.build(),
                padding=ft.padding.only(top=10, bottom=10)
            ),

            ft.Divider(height=10, color=PALETTE[1]),

            ft.Container(
                content=table_scroll,
                expand=True,
                padding=10,
                border=ft.border.all(1, color=PALETTE[1]),
                border_radius=5,
            )
        ], expand=True)

        self.page.update()

    def _render_add_stream_form(self, settings_manager):
        def on_form_submit(stream_data):
            try:
                success = settings_manager.save_stream_with_subjects(
                    stream_data['Поток'],
                    stream_data['Группы_список'],
                    stream_data['Дисциплины_ID']
                )
                if success:
                    self.toast.show("Поток успешно добавлен!", success=True)
                    self._show_streams_section()
                else:
                    self.toast.show("Ошибка при добавлении потока!", success=False)
            except ValueError as e:
                self.toast.show(str(e), success=False)

        def on_form_cancel(e):
            self._show_streams_section()

        stream_form = StreamForm(on_form_submit, on_form_cancel, self.db_ops, self.toast)
        stream_form.set_page(self.page)

        self.content.content = ft.Container(
            content=stream_form.build(),
            padding=20,
            expand=True
        )
        self.page.update()

    def _edit_selected_stream(self, settings_manager):
        selected_row = self.table_manager.get_selected_row("Потоки")
        if selected_row is None:
            self.toast.show("Выберите поток для редактирования!", success=False)
            return

        streams = settings_manager.get_streams_with_subjects()
        stream = streams[selected_row]

        def on_form_submit(stream_data):
            try:
                success = settings_manager.update_stream_with_subjects(
                    stream['ID'],
                    stream_data['Поток'],
                    stream_data['Группы_список'],
                    stream_data['Дисциплины_ID']
                )
                if success:
                    self.toast.show("Поток успешно обновлен!", success=True)
                    self._show_streams_section()
                else:
                    self.toast.show("Ошибка при обновлении потока!", success=False)
            except ValueError as e:
                self.toast.show(str(e), success=False)

        def on_form_cancel(e):
            self._show_streams_section()

        stream_form_data = {
            'Поток': stream['Поток'],
            'Группа1_ID': stream.get('Группа1_ID'),
            'Группа2_ID': stream.get('Группа2_ID'),
            'Группа3_ID': stream.get('Группа3_ID'),
            'Дисциплины_ID': stream.get('Дисциплины_ID', []),
            'Дисциплины_список': stream.get('Дисциплины_список', [])
        }

        stream_form = StreamForm(on_form_submit, on_form_cancel, self.db_ops, self.toast,
                                 edit_mode=True, stream_data=stream_form_data)
        stream_form.set_page(self.page)

        self.content.content = ft.Container(
            content=stream_form.build(),
            padding=20,
            expand=True
        )
        self.page.update()

    def _delete_selected_stream(self, settings_manager):
        selected_row = self.table_manager.get_selected_row("Потоки")
        if selected_row is None:
            self.toast.show("Выберите поток для удаления!", success=False)
            return

        streams = settings_manager.get_streams_with_subjects()
        stream = streams[selected_row]

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Подтверждение удаления"),
            content=ft.Text(f"Вы уверены, что хотите удалить поток '{stream['Поток']}'?"),
            actions=[]
        )

        def on_confirm_delete(evt):
            success = settings_manager.delete_stream(stream['ID'])
            if success:
                self.toast.show("Поток успешно удален!", success=True)
                self.table_manager.clear_selection("Потоки")
                self._show_streams_section()
            else:
                self.toast.show("Ошибка при удалении потока!", success=False)
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
