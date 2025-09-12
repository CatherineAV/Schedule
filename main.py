import flet as ft

# Цветовые палитры (можно будет переключать, сейчас используем первую)
PALETTE1 = ["#DCAEB1", "#E3BEAB", "#F8EDD1", "#CED5B3", "#A0BAB9"]
PALETTE2 = ["#E1ECF0", "#BADDE3", "#C5CFE8", "#ECD2D1", "#D0E7CA"]


def main(page: ft.Page):
    page.title = "Генератор расписания"
    page.bgcolor = PALETTE2[0]   # фон страницы (мягкий бежевый)
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

    # Функции для рендера меню
    def render_main_menu(e=None):
        menu_column.controls.clear()
        menu_column.controls.extend([
            ft.ElevatedButton(
                "🗁 Данные",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,
                ),
                on_click=render_data_menu),
            ft.ElevatedButton(
                "⛭ Настройки генерации",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=render_settings),
            ft.ElevatedButton(
                "▷ Сгенерировать",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=render_generate),
        ])
        content.content = ft.Text("Добро пожаловать! Выберите пункт меню.", size=16)
        page.update()

    def render_data_menu(e=None):
        menu_column.controls.clear()
        menu_column.controls.extend([
            ft.ElevatedButton(
                "↩ Назад",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=render_main_menu),
            ft.Divider(height=50, color=ft.Colors.WHITE),
            ft.ElevatedButton(
                "🅯 Группы",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=lambda e: render_data_pane("Группы")),
            ft.ElevatedButton(
                "🕮 Предметы",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=lambda e: render_data_pane("Предметы")),
            ft.ElevatedButton(
                "㉆ Преподаватели",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=lambda e: render_data_pane("Преподаватели")),
            ft.ElevatedButton(
                "⛯ Территории",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[1],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=lambda e: render_data_pane("Территории")),
        ])
        content.content = ft.Text("Раздел Данные. Выберите, что просматривать.", size=16)
        page.update()

    def render_settings(e=None):
        content.content = ft.Text("Настройки генерации.", size=16, color=PALETTE1[0])
        page.update()

    def render_generate(e=None):
        content.content = ft.Text("Сгенерировать расписание.", size=16, color=PALETTE1[1])
        page.update()

    def render_data_pane(section_name):
        content.content = ft.Column([
            ft.Text(section_name, size=20, weight="bold", color=PALETTE1[4]),
            ft.Text(f"Здесь будет список: {section_name}", size=14),
            ft.ElevatedButton(
                f"Добавить",
                style=ft.ButtonStyle(
                    bgcolor=PALETTE2[4],
                    color="white",
                    padding=20,  # внутренние отступы
                ),
                on_click=lambda e: ft.toast(f"Добавление {section_name} — заглушка"))
        ])
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
                    bgcolor=PALETTE1[4],
                    padding=20,
                ),
                content,
            ],
            expand=True,
        )
    )


ft.app(target=main)


