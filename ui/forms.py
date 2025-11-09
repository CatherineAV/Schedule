import flet as ft
from typing import Callable, List, Dict, Optional, Any
from .components import PALETTE


class GroupForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, group_data: Optional[Dict] = None, subgroups: Optional[List[str]] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_group_name = group_data['Название'] if group_data and edit_mode else ""
        self.selected_subgroups = subgroups if subgroups else []
        self.subgroup_checkbox_refs = {}

        self.group_name_field = ft.TextField(
            label="Название группы",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=group_data['Название'] if group_data and edit_mode else "",
            on_change=self._update_subgroup_options
        )

        self.subgroup_label = ft.Text("Подгруппы", size=16, weight="bold", color=PALETTE[2],
                                      visible=bool(group_data and edit_mode))

        self.subgroup_checkboxes = ft.Column(
            visible=bool(group_data and edit_mode)
        )

        self.self_education_dropdown = ft.Dropdown(
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
            value=group_data.get('Самообразование', 'нет') if group_data and edit_mode else "нет"
        )

        self.important_talks_switch = ft.Switch(
            label=" Разговоры о важном",
            value=bool(group_data.get('Разговоры о важном', 0)) if group_data and edit_mode else False,
            label_style=ft.TextStyle(color=PALETTE[2])
        )

        # Если режим редактирования, сразу заполняем подгруппы
        if edit_mode and group_data and subgroups:
            self._initialize_subgroups(group_data['Название'], subgroups)

    def _initialize_subgroups(self, group_name: str, subgroups: List[str]):
        """Инициализирует чекбоксы подгрупп для режима редактирования"""
        self.subgroup_label.visible = True
        self.subgroup_checkboxes.visible = True

        if "ХБО" in group_name.upper():
            options = ["Кукольники", "Бутафоры"]
        elif "ХКО" in group_name.upper():
            options = ["Женская", "Мужская"]
        else:
            options = ["Нет", "1", "2", "3"]

        checkbox_controls = []

        for option in options:
            checkbox = ft.Checkbox(
                label=option,
                value=option in subgroups,
                label_style=ft.TextStyle(color=PALETTE[2]),
                border_side=ft.BorderSide(width=2, color=PALETTE[2]),
                on_change=lambda e, opt=option: self._on_subgroup_change(opt, e.control.value)
            )
            self.subgroup_checkbox_refs[option] = checkbox
            checkbox_controls.append(checkbox)

        self.subgroup_checkboxes.controls = checkbox_controls

    def build(self) -> ft.Column:
        title = "Редактировать группу" if self.edit_mode else "Добавить группу"

        # Прокручиваемая область
        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.group_name_field,
            self.subgroup_label,
            self.subgroup_checkboxes,
            self.self_education_dropdown,
            self.important_talks_switch,
        ], spacing=15)

        # Кнопки ВНЕ прокручиваемой области
        buttons_container = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=self._on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                    on_click=self.on_cancel
                )
            ], alignment=ft.MainAxisAlignment.END, spacing=20),
            padding=ft.padding.only(top=20),
            border=ft.border.only(top=ft.border.BorderSide(1, PALETTE[1]))
        )

        return ft.Column([
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

    def _update_subgroup_options(self, e):
        group_name = self.group_name_field.value

        if not group_name:
            self.subgroup_label.visible = False
            self.subgroup_checkboxes.visible = False
            self.subgroup_checkboxes.controls = []
            self.subgroup_checkbox_refs.clear()
            self.selected_subgroups.clear()
        else:
            self.subgroup_label.visible = True
            self.subgroup_checkboxes.visible = True

            if "ХБО" in group_name.upper():
                options = ["Кукольники", "Бутафоры"]
            elif "ХКО" in group_name.upper():
                options = ["Женская", "Мужская"]
            else:
                options = ["Нет", "1", "2", "3"]

            checkbox_controls = []
            self.subgroup_checkbox_refs.clear()
            self.selected_subgroups.clear()

            for option in options:
                checkbox = ft.Checkbox(
                    label=option,
                    value=False,
                    label_style=ft.TextStyle(color=PALETTE[2]),
                    border_side=ft.BorderSide(width=2, color=PALETTE[2]),
                    on_change=lambda e, opt=option: self._on_subgroup_change(opt, e.control.value)
                )
                self.subgroup_checkbox_refs[option] = checkbox
                checkbox_controls.append(checkbox)

            self.subgroup_checkboxes.controls = checkbox_controls

        if hasattr(self, 'page'):
            self.page.update()

    def _on_subgroup_change(self, option, is_checked):
        if option == "Нет":
            if is_checked:
                for opt, checkbox in self.subgroup_checkbox_refs.items():
                    if opt != "Нет":
                        checkbox.value = False
                        if opt in self.selected_subgroups:
                            self.selected_subgroups.remove(opt)
                if "Нет" not in self.selected_subgroups:
                    self.selected_subgroups.append("Нет")
            else:
                if "Нет" in self.selected_subgroups:
                    self.selected_subgroups.remove("Нет")
        else:
            if is_checked:
                if "Нет" in self.subgroup_checkbox_refs:
                    self.subgroup_checkbox_refs["Нет"].value = False
                    if "Нет" in self.selected_subgroups:
                        self.selected_subgroups.remove("Нет")
                if option not in self.selected_subgroups:
                    self.selected_subgroups.append(option)
            else:
                if option in self.selected_subgroups:
                    self.selected_subgroups.remove(option)

        if hasattr(self, 'page'):
            self.page.update()

    def _on_form_submit(self, e):
        group_name = self.group_name_field.value.strip()

        if not group_name:
            self.toast.show("Введите название группы!", success=False)
            return

        if not self.selected_subgroups:
            self.toast.show("Выберите хотя бы одну подгруппу (или 'Нет')!", success=False)
            return

        if ("ХКО" in group_name.upper() or "ХБО" in group_name.upper()) and "Нет" in self.selected_subgroups:
            self.toast.show("Группы ХКО и ХБО должны иметь подгруппы!", success=False)
            return

        group_data = {
            'Название': group_name,
            'Самообразование': self.self_education_dropdown.value if self.self_education_dropdown.value != "нет" else None,
            'Разговоры о важном': 1 if self.important_talks_switch.value else 0
        }

        # Проверка на дубликаты (только если изменилось название группы)
        if self.edit_mode and group_name.upper() != self.original_group_name.upper():
            existing_groups = self.db_operations.get_groups_with_subgroups()
            group_exists = any(existing['Название'].upper() == group_name.upper()
                               for existing in existing_groups)

            if group_exists:
                self.toast.show(f"Группа '{group_name}' уже существует!", success=False)
                return

        self.on_submit(group_data, self.selected_subgroups)

    def set_page(self, page: ft.Page):
        self.page = page


class SubjectForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, subject_data: Optional[Dict] = None,
                 classroom_ids: Optional[List[int]] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_subject_name = subject_data['Название'] if subject_data and edit_mode else ""
        self.original_module = subject_data['Модуль'] if subject_data and edit_mode else ""
        self.pre_selected_classroom_ids = classroom_ids if classroom_ids else []

        # ЗАГРУЖАЕМ МОДУЛИ
        self.modules = self.db_operations.get_modules()

        # Загружаем территории
        self.territories = self.db_operations.get_territories()

        # Основные поля предмета
        self.subject_name_field = ft.TextField(
            label="Название предмета",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=subject_data['Название'] if subject_data and edit_mode else "",
        )

        # Создаем выпадающий список для модулей
        module_options = [ft.dropdown.Option(module['Код'], f"{module['Код']} - {module['Название']}")
                          for module in self.modules]

        self.module_dropdown = ft.Dropdown(
            label="Модуль",
            width=300,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=module_options,
            value=subject_data['Модуль'] if subject_data and edit_mode else None,
        )

        # Поля для добавления нового модуля (только при добавлении)
        self.new_module_code_field = ft.TextField(
            label="Код нового модуля",
            border_color=PALETTE[3],
            color=PALETTE[2],
            visible=False,
        )

        self.new_module_name_field = ft.TextField(
            label="Название нового модуля",
            border_color=PALETTE[3],
            color=PALETTE[2],
            visible=False,
        )

        self.add_new_module_switch = ft.Switch(
            label=" Добавить новый модуль",
            value=False,
            label_style=ft.TextStyle(color=PALETTE[2]),
            visible=not edit_mode,
            on_change=self._on_module_switch_change
        )

        # Поля для территорий и кабинетов - СОЗДАЕМ СНАЧАЛА
        self.territory_dropdown = ft.Dropdown(
            label="Территория",
            width=300,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=[ft.dropdown.Option(str(t['ID']), t['Название']) for t in self.territories],
            on_change=self._on_territory_change
        )

        # Заменяем Column на ListView для кабинетов
        self.classroom_label = ft.Text("Доступные кабинеты", size=16, weight="bold",
                                       color=PALETTE[2], visible=False)
        self.classroom_listview = ft.ListView(
            expand=False,
            height=150,  # Фиксированная высота с прокруткой
            spacing=5,
            padding=10,
            visible=False
        )

        # Контейнер для всего блока кабинетов
        self.classroom_container = ft.Container(
            content=self.classroom_listview,
            border=ft.border.all(1, PALETTE[1]),
            border_radius=5,
            visible=False  # Изначально скрыт
        )

        self.classroom_checkbox_refs = {}
        self.selected_classrooms = self.pre_selected_classroom_ids.copy()

        # Сообщения
        self.no_territories_message = ft.Text(
            "Сначала создайте территории и кабинеты в соответствующих разделах",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.territories) == 0
        )
        self.no_classrooms_message = ft.Text(
            "На выбранной территории нет кабинетов",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=False
        )

        # Загружаем кабинеты для предзаполнения (если есть ID кабинетов)
        self.classrooms_data = {}
        if self.pre_selected_classroom_ids:
            self._load_pre_selected_classrooms()
            # Автоматически выбираем территорию если есть предвыбранные кабинеты
            if self.classrooms_data:
                self._auto_select_territory()

    def _load_pre_selected_classrooms(self):
        """Загружает данные о предвыбранных кабинетах"""
        for classroom_id in self.pre_selected_classroom_ids:
            classroom = self.db_operations.get_classroom_by_id(classroom_id)
            if classroom:
                self.classrooms_data[classroom_id] = classroom

    def _auto_select_territory(self):
        """Автоматически выбирает территорию на основе предвыбранных кабинетов"""
        if self.classrooms_data:
            # Берем территорию первого кабинета
            first_classroom = next(iter(self.classrooms_data.values()))
            territory_id = str(first_classroom['ТерриторияID'])
            self.territory_dropdown.value = territory_id
            # Загружаем кабинеты этой территории
            self._load_classrooms_for_territory(int(territory_id))

    def _load_classrooms_for_territory(self, territory_id: int):
        """Загружает кабинеты для территории и отмечает предвыбранные"""
        classrooms = self.db_operations.get_classrooms_by_territory(territory_id)

        if classrooms:
            # Есть кабинеты - показываем ВЕСЬ блок кабинетов
            self.classroom_label.visible = True
            self.classroom_listview.visible = True
            self.classroom_container.visible = True  # Показываем контейнер
            self.no_territories_message.visible = False
            self.no_classrooms_message.visible = False

            # Очищаем список
            self.classroom_listview.controls.clear()
            self.classroom_checkbox_refs.clear()

            # Группируем кабинеты по 3 в строку для компактного отображения
            row_controls = []
            current_row = ft.Row(spacing=3, wrap=True)

            for classroom in classrooms:
                is_checked = classroom['ID'] in self.pre_selected_classroom_ids
                checkbox = ft.Checkbox(
                    label=classroom['Номер'],
                    value=is_checked,
                    label_style=ft.TextStyle(color=PALETTE[2]),
                    on_change=lambda e, classroom_id=classroom['ID']: self._on_classroom_change(classroom_id,
                                                                                                e.control.value)
                )
                self.classroom_checkbox_refs[classroom['ID']] = checkbox

                # Добавляем чекбокс в текущую строку
                current_row.controls.append(checkbox)

                # Если в строке 8 чекбоксов, начинаем новую строку
                if len(current_row.controls) >= 8:
                    row_controls.append(current_row)
                    current_row = ft.Row(spacing=10, wrap=True)

            # Добавляем последнюю строку если она не пустая
            if current_row.controls:
                row_controls.append(current_row)

            # Добавляем все строки в ListView
            self.classroom_listview.controls.extend(row_controls)

        else:
            # Нет кабинетов - скрываем ВЕСЬ блок кабинетов
            self.classroom_label.visible = False
            self.classroom_listview.visible = False
            self.classroom_container.visible = False  # Скрываем контейнер
            self.no_territories_message.visible = False
            self.no_classrooms_message.visible = True
            self.no_classrooms_message.value = f"На выбранной территории нет кабинетов"

    def _on_territory_change(self, e):
        """При изменении территории загружаем кабинеты"""
        territory_id = self.territory_dropdown.value

        if territory_id:
            self._load_classrooms_for_territory(int(territory_id))
        else:
            self.classroom_label.visible = False
            self.classroom_listview.visible = False
            self.classroom_container.visible = False
            self.no_territories_message.visible = False
            self.no_classrooms_message.visible = False

        # Сбрасываем выбранные кабинеты при смене территории
        self.selected_classrooms.clear()
        for checkbox in self.classroom_checkbox_refs.values():
            checkbox.value = False

        if hasattr(self, 'page'):
            self.page.update()

    def _on_classroom_change(self, classroom_id: int, is_checked: bool):
        if is_checked:
            if classroom_id not in self.selected_classrooms:
                self.selected_classrooms.append(classroom_id)
        else:
            if classroom_id in self.selected_classrooms:
                self.selected_classrooms.remove(classroom_id)

    def _on_module_switch_change(self, e):
        """Показывает/скрывает поля для нового модуля и выпадающий список"""
        is_visible = self.add_new_module_switch.value

        # Если включаем создание нового модуля
        if is_visible:
            # Показываем поля для нового модуля
            self.new_module_code_field.visible = True
            self.new_module_name_field.visible = True
            # Скрываем выпадающий список
            self.module_dropdown.visible = False
        else:
            # Если выключаем создание нового модуля
            # Скрываем поля для нового модуля
            self.new_module_code_field.visible = False
            self.new_module_name_field.visible = False
            # Показываем выпадающий список
            self.module_dropdown.visible = True
            # Очищаем поля нового модуля
            self.new_module_code_field.value = ""
            self.new_module_name_field.value = ""

        if hasattr(self, 'page'):
            self.page.update()

    def build(self) -> ft.Column:
        title = "Редактировать предмет" if self.edit_mode else "Добавить предмет"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.subject_name_field,
        ], spacing=15)

        if not self.edit_mode:
            scrollable_content.controls.extend([
                self.add_new_module_switch,
                self.new_module_code_field,
                self.new_module_name_field,
                self.module_dropdown,
            ])
        else:
            scrollable_content.controls.append(self.module_dropdown)

        # Добавляем блок территорий и кабинетов в прокручиваемую область
        scrollable_content.controls.extend([
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Расположение предмета", size=16, weight="bold", color=PALETTE[2]),
            self.territory_dropdown,
            self.no_territories_message,
            self.no_classrooms_message,
            self.classroom_label,
            self.classroom_container,
        ])

        buttons_container = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=self._on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                    on_click=self.on_cancel
                )
            ], alignment=ft.MainAxisAlignment.END, spacing=20),
            padding=ft.padding.only(top=20),
            border=ft.border.only(top=ft.border.BorderSide(1, PALETTE[1]))
        )

        # Основной контейнер - прокручиваемая область + закрепленные кнопки
        return ft.Column([
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

    def _on_form_submit(self, e):
        subject_name = self.subject_name_field.value.strip()

        if self.add_new_module_switch.value:
            # Режим создания нового модуля
            module_code = self.new_module_code_field.value.strip()
            module_name = self.new_module_name_field.value.strip()

            if not subject_name:
                self.toast.show("Введите название предмета!", success=False)
                return

            if not module_code or not module_name:
                self.toast.show("Заполните код и название нового модуля!", success=False)
                return

            # Добавляем новый модуль
            if not self.db_operations.insert_module(module_code, module_name):
                self.toast.show("Ошибка при добавлении модуля! Возможно, модуль с таким кодом уже существует.",
                                success=False)
                return

            if not self.territory_dropdown.value:
                self.toast.show("Выберите территорию!", success=False)
                return

            territory_id = int(self.territory_dropdown.value)
            classrooms = self.db_operations.get_classrooms_by_territory(territory_id)
            if not classrooms:
                self.toast.show("На выбранной территории нет кабинетов!", success=False)
                return

            # Проверяем что выбраны кабинеты
            if not self.selected_classrooms:
                self.toast.show("Выберите хотя бы один кабинет!", success=False)
                return

            module = module_code  # Используем код модуля как значение
        else:
            # Режим выбора существующего модуля
            module = self.module_dropdown.value  # Меняем на module

            if not subject_name:
                self.toast.show("Введите название предмета!", success=False)
                return

            if not module:
                self.toast.show("Выберите модуль!", success=False)
                return

        # Проверка на дубликаты
        if self.edit_mode:
            if (subject_name.upper() != self.original_subject_name.upper() or
                    module != self.original_module):  # Меняем на module
                if self.db_operations.check_subject_exists(subject_name, module):
                    self.toast.show(f"Предмет '{subject_name}' с модулем '{module}' уже существует!", success=False)
                    return
        else:
            if self.db_operations.check_subject_exists(subject_name, module):
                self.toast.show(f"Предмет '{subject_name}' с модулем '{module}' уже существует!", success=False)
                return

        subject_data = {
            'Название': subject_name,
            'Модуль': module  # Меняем на Модуль
        }

        self.on_submit(subject_data, self.selected_classrooms)

    def set_page(self, page: ft.Page):
        self.page = page


class ClassroomForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, classroom_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_classroom_number = classroom_data['Номер'] if classroom_data and edit_mode else ""
        self.original_territory_id = classroom_data['ТерриторияID'] if classroom_data and edit_mode else None

        # Загружаем территории для выпадающего списка
        self.territories = self.db_operations.get_territories()

        self.classroom_number_field = ft.TextField(
            label="Номер кабинета",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=classroom_data['Номер'] if classroom_data and edit_mode else "",
        )

        # Выпадающий список для территорий
        territory_options = [ft.dropdown.Option(str(territory['ID']), territory['Название'])
                             for territory in self.territories]

        self.territory_dropdown = ft.Dropdown(
            label="Территория",
            width=500,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=territory_options,
            value=str(classroom_data['ТерриторияID']) if classroom_data and edit_mode else None,
        )

        self.capacity_field = ft.TextField(
            label="Вместимость (опционально)",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=str(classroom_data.get('Вместимость', '')) if classroom_data and edit_mode else "",
        )

        # Сообщение если нет территорий
        self.no_territories_message = ft.Text(
            "Сначала создайте территории в соответствующем разделе",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.territories) == 0
        )

    def build(self) -> ft.Column:
        title = "Редактировать кабинет" if self.edit_mode else "Добавить кабинет"

        # Прокручиваемая область
        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.classroom_number_field,
            self.territory_dropdown,
            self.no_territories_message,
            self.capacity_field,
        ], spacing=15)

        # Кнопки ВНЕ прокручиваемой области
        buttons_container = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    style=ft.ButtonStyle(bgcolor=PALETTE[3], color="white", padding=20),
                    on_click=self._on_form_submit
                ),
                ft.ElevatedButton(
                    "Отмена",
                    style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=20),
                    on_click=self.on_cancel
                )
            ], alignment=ft.MainAxisAlignment.END, spacing=20),
            padding=ft.padding.only(top=20),
            border=ft.border.only(top=ft.border.BorderSide(1, PALETTE[1]))
        )

        return ft.Column([
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

    def _on_form_submit(self, e):
        classroom_number = self.classroom_number_field.value.strip()
        territory_id = self.territory_dropdown.value
        capacity = self.capacity_field.value.strip()

        if not classroom_number:
            self.toast.show("Введите номер кабинета!", success=False)
            return

        if not territory_id:
            self.toast.show("Выберите территорию!", success=False)
            return

        # ПРОВЕРКА НА ДУБЛИКАТ КАБИНЕТА
        if not self.edit_mode:
            # При добавлении - проверяем существует ли кабинет
            if self.db_operations.check_classroom_exists(classroom_number, int(territory_id)):
                self.toast.show(f"Кабинет '{classroom_number}' уже существует на этой территории!", success=False)
                return
        else:
            # При редактировании - проверяем только если изменился номер или территория
            if (classroom_number != self.original_classroom_number or int(territory_id) != self.original_territory_id):
                if self.db_operations.check_classroom_exists(classroom_number, int(territory_id)):
                    self.toast.show(f"Кабинет '{classroom_number}' уже существует на этой территории!", success=False)
                    return

        classroom_data = {
            'Номер': classroom_number,
            'ТерриторияID': int(territory_id)
        }

        if capacity:
            try:
                classroom_data['Вместимость'] = int(capacity)
            except ValueError:
                self.toast.show("Вместимость должна быть числом!", success=False)
                return

        self.on_submit(classroom_data)

    def set_page(self, page: ft.Page):
        self.page = page
