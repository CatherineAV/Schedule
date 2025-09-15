import flet as ft
from database.operations import DBOperations
from ui.components import Toast
from ui.pages import MainMenu

PALETTE = ["#18363E", "#5F97AA", "#2D5F6E", "#3E88A5", "#93C4D1"]


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

    db_ops = DBOperations()
    toast = Toast(page)

    menu_column = ft.Column(spacing=10, expand=True)
    content = ft.Container(
        content=ft.Text("Добро пожаловать!", size=16),
        expand=True,
        bgcolor=ft.Colors.WHITE,
        padding=20,
        margin=ft.margin.only(left=20),
        border_radius=15,
    )

    main_menu = MainMenu(menu_column, content, page, db_ops, toast)

    main_menu.render()

    page.add(
        ft.Row(
            [
                ft.Container(
                    content=menu_column,
                    width=260,
                    bgcolor=PALETTE[1],
                    padding=20,
                    margin=ft.margin.only(top=20, bottom=20, left=20),
                    border_radius=15,
                ),
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


if __name__ == "__main__":
    ft.app(target=main)
