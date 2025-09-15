import flet as ft
from typing import Callable, List, Dict, Any, Optional
from database.operations import DBOperations
from ui.components import Toast, DataTableManager, PALETTE
from ui.forms import GroupForm


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
            columns = ["ID", "Название", "Подгруппа", "Самообразование", "Разговоры о важном"]
        else:
            data = self.db_ops.get_table_data(section_name)
            columns = self.db_ops.get_table_columns(section_name)

        selected_row = self.table_manager.get_selected_row(section_name)

        def on_row_select(index):
            refresh_table()

        def refresh_table():
            data_table = self.table_manager.create_data_table(data, columns, section_name, on_row_select)
            table_scroll.controls = [data_table]
            delete_button.bgcolor = ft.Colors.RED_400 if selected_row is not None else ft.Colors.GREY_400
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
                    success = self.db_ops.delete_group_with_subgroups(record['Название'], record['Подгруппа'])
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

        data_table = self.table_manager.create_data_table(data, columns, section_name, on_row_select)

        table_scroll = ft.ListView(
            [data_table],
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False
        )

        delete_button = ft.ElevatedButton(
            text="🗑️",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_400 if selected_row is not None else ft.Colors.GREY_400,
                color="white",
                padding=16,
                shape=ft.CircleBorder()
            ),
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
                ft.Row([add_button, delete_button], spacing=10)
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

    def _render_add_form(self, table_name: str, columns: List[str]):
        if table_name == "Группы":
            self._render_group_add_form()
        else:
            self._render_standard_add_form(table_name, columns)

    def _render_group_add_form(self):
        def on_form_submit():
            self.render("Группы")

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

        form_content = ft.Column([
            ft.Text(f"Добавить запись в {table_name}", size=18, weight="bold", color=PALETTE[2])
        ])

        for column in columns:
            if column.lower() != 'id':
                field = ft.TextField(
                    label=column,
                    border_color=PALETTE[3],
                    color=PALETTE[2]
                )
                form_fields_ref[column] = field
                form_content.controls.append(field)

        form_content.controls.extend([
            ft.Row([
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
            ])
        ])

        self.content.content = ft.Container(
            content=form_content,
            padding=20
        )

        self.page.update()
