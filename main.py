import flet as ft
import create_db as db
from db_operations import get_table_data, get_table_columns, insert_data

# Цветовые палитры
PALETTE = ["#18363E", "#5F97AA", "#2D5F6E", "#3E88A5", "#93C4D1"]

db.init_db()


def main(page: ft.Page):
    page.title = "Генератор расписания"
    page.bgcolor = PALETTE[4]
    page.horizontal_alignment = "stretch"
    page.vertical_alignment = "start"
    page.window.min_width = 1000
    page.window.min_height = 600
    page.window.center()
    page.padding = 0
    page.spacing = 0

    menu_column = ft.Column(spacing=10, expand=True)

    # Адаптивный контейнер - занимает все доступное пространство
    content = ft.Container(
        content=ft.Text("Добро пожаловать!", size=16),
        expand=True,
        bgcolor=ft.Colors.WHITE,
        padding=20,
        margin=ft.margin.only(left=20),
        border_radius=15,
    )

    # Функция для создания таблицы данных
    def create_data_table(data, columns):
        data_rows = []
        for row in data:
            cells = []
            for idx, col in enumerate(columns):
                txt = ft.Text(str(row.get(col, "")), color=PALETTE[2], no_wrap=False)

                cell = ft.DataCell(
                    ft.Container(txt, expand=True, alignment=ft.alignment.center_left)
                )
                cells.append(cell)
            data_rows.append(ft.DataRow(cells=cells))

        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight="bold", color=PALETTE[2])) for c in columns],
            rows=data_rows,
            expand=True,
            divider_thickness=0
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
                "Данные",
                icon=ft.Icons.FOLDER,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_data_menu),
            ft.ElevatedButton(
                "Настройки генерации",
                icon=ft.Icons.SETTINGS,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_settings),
            ft.ElevatedButton(
                "Сгенерировать",
                icon=ft.Icons.PLAY_ARROW,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_generate),
        ])
        content.content = ft.Column([
            ft.Text("Добро пожаловать! Выберите пункт меню.", size=16)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    def render_data_menu(e=None):
        menu_column.controls.clear()
        menu_column.controls.extend([
            ft.ElevatedButton(
                "Назад",
                icon=ft.Icons.ARROW_BACK,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=render_main_menu),
            ft.Divider(height=20, color=ft.Colors.WHITE),
            ft.ElevatedButton(
                "Группы",
                icon=ft.Icons.GROUPS,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Группы")),
            ft.ElevatedButton(
                "Предметы",
                icon=ft.Icons.CLASS_,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Предметы")),
            ft.ElevatedButton(
                "Преподаватели",
                icon=ft.Icons.MAN,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Преподаватели")),
            ft.ElevatedButton(
                "Территории",
                icon=ft.Icons.MAP,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Территории")),
            ft.ElevatedButton(
                "Кабинеты",
                icon=ft.Icons.PLACE,
                style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                on_click=lambda e: render_data_pane("Кабинеты")),
        ])
        content.content = ft.Column([
            ft.Text("Раздел Данные. Выберите, что просматривать.", size=16)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    def render_data_pane(section_name):
        data = get_table_data(section_name)
        columns = get_table_columns(section_name)

        data_table = create_data_table(data, columns)

        # контейнер с прокруткой
        table_scroll = ft.ListView(
            [data_table],
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False
        )

        # основной контент
        content.content = ft.Column([
            ft.Row([
                ft.Text(section_name, size=20, weight="bold", color=PALETTE[2]),
                ft.ElevatedButton(
                    text="🞢",
                    style=ft.ButtonStyle(
                        bgcolor=PALETTE[3], color="white", padding=16, shape=ft.CircleBorder()
                    ),
                    on_click=lambda e: render_add_form(section_name, columns)
                )
            ]),
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Container(
                content=table_scroll,
                expand=True,
                padding=10,
                border=ft.border.all(1, color=PALETTE[1]),
                border_radius=5,
            )
        ], expand=True)

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
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
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
        content.content = ft.Column([
            ft.Text("Настройки генерации.", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    def render_generate(e=None):
        content.content = ft.Column([
            ft.Text("Сгенерировать расписание.", size=16, color=PALETTE[0])
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    # Первичный рендер
    render_main_menu()

    # Макет: меню слева, контент справа - оба адаптивные
    page.add(
        ft.Row(
            [
                # Меню - фиксированной ширины
                ft.Container(
                    content=menu_column,
                    width=260,
                    bgcolor=PALETTE[1],
                    padding=20,
                    #margin=ft.margin.only(top=20, bottom=20, left=20),
                    #border_radius=15,
                ),
                # Контент - адаптивный
                ft.Container(
                    content=content,
                    expand=True,
                    margin=ft.margin.only(top=20, bottom=20, right=20, left=0),
                ),
            ],
            expand=True,
            spacing=0,
        )
    )


ft.app(target=main)
