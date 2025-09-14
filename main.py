import flet as ft
import threading
import create_db as db
from db_operations import get_table_data, get_groups_with_subgroups, get_table_columns, insert_data, insert_group_with_subgroups

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

    def show_toast(message: str, success: bool = True):
        # Создаем контейнер с сообщением
        toast = ft.Container(
            content=ft.Text(message, color=ft.Colors.WHITE, size=14, weight="bold"),
            bgcolor=ft.Colors.GREEN_400 if success else ft.Colors.RED_400,
            padding=15,
            border_radius=10,
            width=400,
            alignment=ft.alignment.center,
            top=page.height / 2 - 25,  # Центр по вертикали
            left=page.width / 2 - 100,  # Центр по горизонтали
            animate_position=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK54)
        )

        # Добавляем в overlay
        page.overlay.append(toast)
        page.update()

        # Удаляем через 2 секунды
        def remove_toast():
            import time
            time.sleep(2)
            if toast in page.overlay:
                page.overlay.remove(toast)
                page.update()

        threading.Thread(target=remove_toast, daemon=True).start()

    # Функция для создания таблицы данных
    def create_data_table(data, columns):
        if not data:
            return ft.Container(
                content=ft.Text("Нет данных для отображения", size=16),
                alignment=ft.alignment.center,
                padding=20
            )

        # Для таблицы Группы показываем дополнительные поля
        if "Группы" in str(data[0].get('table_name', '')) or any('Самообразование' in col for col in columns):
            display_columns = [col for col in columns if col != 'ID']
        else:
            display_columns = columns

        data_rows = []
        for row in data:
            cells = []
            for col in display_columns:
                value = row.get(col, "")
                # Форматируем специальные поля
                if col == "Разговоры о важном":
                    value = "Да" if value == 1 or value == "Да" else "Нет"
                elif col == "Самообразование" and not value:
                    value = "Нет"
                elif col == "Подгруппа" and not value:
                    value = "Нет"

                txt = ft.Text(str(value), color=PALETTE[2], no_wrap=False)
                cell = ft.DataCell(ft.Container(txt, expand=True, alignment=ft.alignment.center_left))
                cells.append(cell)
            data_rows.append(ft.DataRow(cells=cells))

        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, weight="bold", color=PALETTE[2])) for c in display_columns],
            rows=data_rows,
            expand=True,
            divider_thickness=0
        )

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
        if section_name == "Группы":
            data = get_groups_with_subgroups()
            columns = ["Название", "Подгруппа", "Самообразование", "Разговоры о важном"]
        else:
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
        if table_name == "Группы":
            render_group_add_form()
        else:
            # Обычная форма для других таблиц
            render_standard_add_form(table_name, columns)

    def render_group_add_form():
        """Специальная форма для добавления групп"""
        group_name_field = ft.TextField(
            label="Название группы",
            border_color=PALETTE[3],
            color=PALETTE[2],
            on_change=lambda e: update_subgroup_options(e.control.value)
        )

        # Контейнер для заголовка чекбоксов
        subgroup_label = ft.Text("Подгруппы", size=16, weight="bold", color=PALETTE[2], visible=False)

        # Чекбоксы для множественного выбора подгрупп
        subgroup_checkboxes = ft.Column(visible=False)

        # ... остальные поля ...
        self_education_dropdown = ft.Dropdown(
            label="День самообразования",
            width=210,
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

        important_talks_switch = ft.Switch(
            label=" Разговоры о важном",
            value=False,
            label_style=ft.TextStyle(color=PALETTE[2])
        )

        selected_subgroups = []
        subgroup_checkbox_refs = {}

        def update_subgroup_options(group_name):
            if not group_name:
                subgroup_label.visible = False
                subgroup_checkboxes.visible = False
                subgroup_checkboxes.controls = []
                subgroup_checkbox_refs.clear()
                selected_subgroups.clear()
            else:
                subgroup_label.visible = True
                subgroup_checkboxes.visible = True

                if "ХБО" in group_name.upper():
                    options = ["Кукольники", "Бутафоры"]
                elif "ХКО" in group_name.upper():
                    options = ["Женская", "Мужская"]
                else:
                    options = ["Нет", "1", "2", "3"]

                checkbox_controls = []
                subgroup_checkbox_refs.clear()
                selected_subgroups.clear()

                for option in options:
                    checkbox = ft.Checkbox(
                        label=option,
                        value=False,
                        label_style=ft.TextStyle(color=PALETTE[2]),
                        on_change=lambda e, opt=option: on_subgroup_change(opt, e.control.value)
                    )
                    subgroup_checkbox_refs[option] = checkbox
                    checkbox_controls.append(checkbox)

                subgroup_checkboxes.controls = checkbox_controls

            page.update()

        def on_subgroup_change(option, is_checked):
            if option == "Нет":
                if is_checked:
                    for opt, checkbox in subgroup_checkbox_refs.items():
                        if opt != "Нет":
                            checkbox.value = False
                            if opt in selected_subgroups:
                                selected_subgroups.remove(opt)
                    if "Нет" not in selected_subgroups:
                        selected_subgroups.append("Нет")  # <-- вот этого не хватало
                else:
                    if "Нет" in selected_subgroups:
                        selected_subgroups.remove("Нет")
            else:
                if is_checked:
                    if "Нет" in subgroup_checkbox_refs:
                        subgroup_checkbox_refs["Нет"].value = False
                        if "Нет" in selected_subgroups:
                            selected_subgroups.remove("Нет")
                    if option not in selected_subgroups:
                        selected_subgroups.append(option)
                else:
                    if option in selected_subgroups:
                        selected_subgroups.remove(option)
            page.update()

        def on_form_submit(e):
            group_name = group_name_field.value.strip()

            if not group_name:
                show_toast("Введите название группы!", success=False)
                return

            # 1. Проверка: вообще ничего не выбрано
            if not selected_subgroups:
                show_toast("Выберите хотя бы одну подгруппу (или 'Нет')!", success=False)
                return

            # 3. Всё ок — сохраняем
            group_data = {
                'Название': group_name,
                'Самообразование': self_education_dropdown.value if self_education_dropdown.value != "нет" else None,
                'Разговоры о важном': 1 if important_talks_switch.value else 0
            }

            if insert_group_with_subgroups(group_data, selected_subgroups):
                show_toast("Группа и подгруппы успешно добавлены!", success=True)
                render_data_pane("Группы")
            else:
                show_toast("Ошибка при добавлении группы!", success=False)

        form_content = ft.Column([
            ft.Text("Добавить группу", size=18, weight="bold", color=PALETTE[2]),
            group_name_field,
            subgroup_label,
            subgroup_checkboxes,
            self_education_dropdown,
            important_talks_switch,
            ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                    on_click=lambda e: render_data_pane("Группы")
                )
            ])
        ], spacing=15)

        content.content = ft.Container(
            content=form_content,
            padding=20
        )
        page.update()

    def render_standard_add_form(table_name, columns):
        """Обычная форма для других таблиц"""
        form_fields_ref = {}

        def on_form_submit(e):
            data = {}
            for column in columns:
                if column.lower() != 'id' and column in form_fields_ref:
                    data[column] = form_fields_ref[column].value

            if insert_data(table_name, data):
                show_toast(f"Данные успешно добавлены в {table_name}!", success=True)
                render_data_pane(table_name)
            else:
                show_toast(f"Ошибка при добавлении данных в {table_name}", success=False)

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
                    margin=ft.margin.only(top=20, bottom=20, left=20),
                    border_radius=15,
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
