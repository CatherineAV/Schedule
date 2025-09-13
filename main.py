import flet as ft
import create_db as db
from db_operations import get_table_data, get_table_columns, insert_data
from create_sample_data import create_sample_data

# Цветовые палитры
PALETTE = ["#18363E", "#5F97AA", "#2D5F6E", "#3E88A5", "#93C4D1"]

db.init_db()
create_sample_data()

def main(page: ft.Page):
    page.title = "Генератор расписания"
    page.bgcolor = PALETTE[4]
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"
    page.window.center()
    page.padding = 0

    menu_column = ft.Column(spacing=10, expand=False)
    content = ft.Container(
        content=ft.Text("Добро пожаловать!", size=16),
        expand=True,
        bgcolor=ft.Colors.WHITE,
        padding=20,
        margin=20,
        border_radius=10,
    )

    # Функция для создания таблицы данных
    def create_data_table(data, columns):
        if not data:
            return ft.Text("Нет данных для отображения", size=16)

        # Создаем строку с заголовками
        header_cells = [ft.DataColumn(ft.Text(col, weight="bold")) for col in columns]

        # Создаем строки с данными
        data_rows = []
        for row in data:
            cells = [ft.DataCell(ft.Text(str(row.get(col, "")), color=PALETTE[0])) for col in columns]
            data_rows.append(ft.DataRow(cells=cells))

        return ft.DataTable(
            columns=header_cells,
            rows=data_rows,
            border=ft.border.all(1, PALETTE[1]),
            border_radius=10,
            horizontal_margin=10,
            column_spacing=20,
            heading_row_color=ft.Colors.BLACK12,
            heading_row_height=40,
            data_row_max_height=40,
        )

    # Функция для создания формы добавления данных
    def create_add_form(table_name, columns, on_submit):
        form_fields = []
        for column in columns:
            if column.lower() != 'id':  # Пропускаем поле ID
                form_fields.append(
                    ft.TextField(
                        label=column,
                        border_color=PALETTE[1],
                    )
                )

        return ft.Column([
            ft.Text(f"Добавить запись в {table_name}", size=18, weight="bold"),
            *form_fields,
            ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white"),
                    on_click=on_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white"),
                    on_click=lambda e: render_data_pane(table_name)
                )
            ])
        ])

    # Функции для рендера меню
    def render_main_menu(e=None):
        menu_column.controls.clear()
        menu_column.controls.extend([
            ft.ElevatedButton(
                "🗁 Данные",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_data_menu),
            ft.ElevatedButton(
                "⛭ Настройки генерации",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_settings),
            ft.ElevatedButton(
                "▷ Сгенерировать",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_generate),
        ])
        content.content = ft.Text("Добро пожаловать! Выберите пункт меню.", size=16)
        page.update()

    def render_data_menu(e=None):
        menu_column.controls.clear()
        menu_column.controls.extend([
            ft.ElevatedButton(
                "↩ Назад",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_main_menu),
            ft.Divider(height=50, color=ft.Colors.WHITE),
            ft.ElevatedButton(
                "🅯 Группы",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Группы")),
            ft.ElevatedButton(
                "🕮 Предметы",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Предметы")),
            ft.ElevatedButton(
                "㉆ Преподаватели",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Преподаватели")),
            ft.ElevatedButton(
                "⛯ Территории",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Территории")),
            ft.ElevatedButton(
                "◫ Кабинеты",
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Кабинеты")),
        ])
        content.content = ft.Text("Раздел Данные. Выберите, что просматривать.", size=16)
        page.update()

    def render_data_pane(section_name):
        # Получаем данные из базы
        data = get_table_data(section_name)
        columns = get_table_columns(section_name)

        # Создаем контент
        content.content = ft.Column([
            ft.Row([
                ft.Text(section_name, size=20, weight="bold", color=PALETTE[2]),
                ft.ElevatedButton(
                    "Добавить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white"),
                    on_click=lambda e: render_add_form(section_name, columns)
                )
            ]),
            ft.Divider(),
            create_data_table(data, columns)
        ], scroll="adaptive")

        page.update()

    def render_add_form(table_name, columns):
        form_fields_ref = {}

        def on_form_submit(e):
            data = {}
            for column in columns:
                if column.lower() != 'id' and column in form_fields_ref:
                    data[column] = form_fields_ref[column].value

            if insert_data(table_name, data):
                ft.toast(f"Данные успешно добавлены в {table_name}!")
                render_data_pane(table_name)
            else:
                ft.toast(f"Ошибка при добавлении данных в {table_name}")

        # Создаем поля формы
        form_content = ft.Column([
            ft.Text(f"Добавить запись в {table_name}", size=18, weight="bold")
        ])

        for column in columns:
            if column.lower() != 'id':
                field = ft.TextField(
                    label=column,
                    border_color=PALETTE[0],
                )
                form_fields_ref[column] = field
                form_content.controls.append(field)

        form_content.controls.extend([
            ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white"),
                    on_click=on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white"),
                    on_click=lambda e: render_data_pane(table_name)
                )
            ])
        ])

        content.content = ft.Container(
            content=form_content,
            padding=20
        )
        page.update()

    def render_settings(e=None):
        content.content = ft.Text("Настройки генерации.", size=16, color=PALETTE[0])
        page.update()

    def render_generate(e=None):
        content.content = ft.Text("Сгенерировать расписание.", size=16, color=PALETTE[0])
        page.update()

    # Первичный рендер
    render_main_menu()

    # Макет: меню слева, контент справа
    page.add(
        ft.Row(
            [
                ft.Container(
                    content=menu_column,
                    width=270,
                    bgcolor=PALETTE[1],
                    padding=20,
                ),
                content,
            ],
            expand=True,
        )
    )


ft.app(target=main)