import flet as ft
from typing import Callable, List, Dict, Optional, Any
from ui.components import PALETTE, Validator


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

        if edit_mode and group_data:
            self_education_value = group_data.get('Самообразование', 'нет')
        else:
            self_education_value = "нет"

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
            value=self_education_value
        )

        self.important_talks_switch = ft.Switch(
            label=" Разговоры о важном",
            value=bool(group_data.get('Разговоры о важном', 0)) if group_data and edit_mode else False,
            label_style=ft.TextStyle(color=PALETTE[2])
        )

        if edit_mode and group_data and subgroups:
            self._initialize_subgroups(group_data['Название'], subgroups)

    def _initialize_subgroups(self, group_name: str, subgroups: List[str]):
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

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.group_name_field,
            self.subgroup_label,
            self.subgroup_checkboxes,
            self.self_education_dropdown,
            self.important_talks_switch,
        ], spacing=15)

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

        # Валидация обязательных полей
        if error := Validator.validate_required(group_name, "Название группы"):
            self.toast.show(error, success=False)
            return

        # Валидация подгрупп
        if error := Validator.validate_subgroups(group_name, self.selected_subgroups):
            self.toast.show(error, success=False)
            return

        # Валидация уникальности (только если имя изменилось при редактировании)
        if self.edit_mode and group_name.upper() != self.original_group_name.upper():
            if error := Validator.validate_unique(self.db_operations, "Группы", "Название", group_name):
                self.toast.show(error, success=False)
                return
        elif not self.edit_mode:
            if error := Validator.validate_unique(self.db_operations, "Группы", "Название", group_name):
                self.toast.show(error, success=False)
                return

        group_data = {
            'Название': group_name,
            'Самообразование': self.self_education_dropdown.value if self.self_education_dropdown.value != "нет" else None,
            'Разговоры о важном': 1 if self.important_talks_switch.value else 0
        }

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

        self.modules = self.db_operations.get_modules()

        self.territories = self.db_operations.get_territories()

        self.subject_name_field = ft.TextField(
            label="Название предмета",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=subject_data['Название'] if subject_data and edit_mode else "",
        )

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

        self.territory_dropdown = ft.Dropdown(
            label="Территория",
            width=300,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=[ft.dropdown.Option(str(t['ID']), t['Название']) for t in self.territories],
            on_change=self._on_territory_change
        )

        self.classroom_label = ft.Text("Доступные кабинеты", size=16, weight="bold",
                                       color=PALETTE[2], visible=False)
        self.classroom_listview = ft.ListView(
            expand=False,
            height=150,
            spacing=5,
            padding=10,
            visible=False
        )

        self.classroom_container = ft.Container(
            content=self.classroom_listview,
            border=ft.border.all(1, PALETTE[1]),
            border_radius=5,
            visible=False
        )

        self.classroom_checkbox_refs = {}
        self.selected_classrooms = self.pre_selected_classroom_ids.copy()

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

        self.classrooms_data = {}
        if self.pre_selected_classroom_ids:
            self._load_pre_selected_classrooms()
            if self.classrooms_data:
                self._auto_select_territory()

    def _load_pre_selected_classrooms(self):
        for classroom_id in self.pre_selected_classroom_ids:
            classroom = self.db_operations.get_classroom_by_id(classroom_id)
            if classroom:
                self.classrooms_data[classroom_id] = classroom

    def _auto_select_territory(self):
        if self.classrooms_data:
            first_classroom = next(iter(self.classrooms_data.values()))
            territory_id = str(first_classroom['ТерриторияID'])
            self.territory_dropdown.value = territory_id
            self._load_classrooms_for_territory(int(territory_id))

    def _load_classrooms_for_territory(self, territory_id: int):
        classrooms = self.db_operations.get_classrooms_by_territory(territory_id)

        if classrooms:
            self.classroom_label.visible = True
            self.classroom_listview.visible = True
            self.classroom_container.visible = True
            self.no_territories_message.visible = False
            self.no_classrooms_message.visible = False

            self.classroom_listview.controls.clear()
            self.classroom_checkbox_refs.clear()

            items_per_row = 15

            for i in range(0, len(classrooms), items_per_row):
                row_classrooms = classrooms[i:i + items_per_row]

                row_controls = []
                for classroom in row_classrooms:
                    is_checked = classroom['ID'] in self.pre_selected_classroom_ids
                    checkbox = ft.Checkbox(
                        label=classroom['Номер'],
                        value=is_checked,
                        label_style=ft.TextStyle(color=PALETTE[2]),
                        on_change=lambda e, classroom_id=classroom['ID']: self._on_classroom_change(classroom_id,
                                                                                                    e.control.value)
                    )
                    self.classroom_checkbox_refs[classroom['ID']] = checkbox
                    row_controls.append(checkbox)

                row = ft.Row(
                    controls=row_controls,
                    spacing=10,
                    wrap=False
                )
                self.classroom_listview.controls.append(row)

        else:
            self.classroom_label.visible = False
            self.classroom_listview.visible = False
            self.classroom_container.visible = False
            self.no_territories_message.visible = False
            self.no_classrooms_message.visible = True
            self.no_classrooms_message.value = f"На выбранной территории нет кабинетов"

    def _on_territory_change(self, e):
        territory_id = self.territory_dropdown.value

        if territory_id:
            self._load_classrooms_for_territory(int(territory_id))
        else:
            self.classroom_label.visible = False
            self.classroom_listview.visible = False
            self.classroom_container.visible = False
            self.no_territories_message.visible = False
            self.no_classrooms_message.visible = False

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
        is_visible = self.add_new_module_switch.value

        if is_visible:
            self.new_module_code_field.visible = True
            self.new_module_name_field.visible = True
            self.module_dropdown.visible = False
        else:
            self.new_module_code_field.visible = False
            self.new_module_name_field.visible = False
            self.module_dropdown.visible = True
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

        if error := Validator.validate_required(subject_name, "Название предмета"):
            self.toast.show(error, success=False)
            return

        if self.add_new_module_switch.value:
            module_code = self.new_module_code_field.value.strip()
            module_name = self.new_module_name_field.value.strip()

            if error := Validator.validate_required(module_code, "Код модуля"):
                self.toast.show(error, success=False)
                return

            if error := Validator.validate_required(module_name, "Название модуля"):
                self.toast.show(error, success=False)
                return

            if error := Validator.validate_unique(self.db_operations, "Модули", "Код", module_code):
                self.toast.show(error, success=False)
                return

            module = module_code
        else:
            module = self.module_dropdown.value
            if not module:
                self.toast.show("Выберите модуль!", success=False)
                return

        if error := Validator.validate_classrooms(self.territory_dropdown.value, self.selected_classrooms):
            self.toast.show(error, success=False)
            return

        if self.edit_mode:
            if (subject_name.upper() != self.original_subject_name.upper() or
                    module != self.original_module):
                if self.db_operations.check_subject_exists(subject_name, module):
                    self.toast.show(f"Предмет '{subject_name}' с модулем '{module}' уже существует!", success=False)
                    return
        else:
            if self.db_operations.check_subject_exists(subject_name, module):
                self.toast.show(f"Предмет '{subject_name}' с модулем '{module}' уже существует!", success=False)
                return

        subject_data = {
            'Название': subject_name,
            'Модуль': module
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

        self.territories = self.db_operations.get_territories()

        self.classroom_number_field = ft.TextField(
            label="Номер кабинета",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=classroom_data['Номер'] if classroom_data and edit_mode else "",
        )

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

        self.no_territories_message = ft.Text(
            "Сначала создайте территории в соответствующем разделе",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.territories) == 0
        )

    def build(self) -> ft.Column:
        title = "Редактировать кабинет" if self.edit_mode else "Добавить кабинет"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.classroom_number_field,
            self.territory_dropdown,
            self.no_territories_message,
            self.capacity_field,
        ], spacing=15)

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

        if error := Validator.validate_required(classroom_number, "Номер кабинета"):
            self.toast.show(error, success=False)
            return

        if not territory_id:
            self.toast.show("Выберите территорию!", success=False)
            return

        territory_id_int = int(territory_id)
        if not self.edit_mode:
            if self.db_operations.check_classroom_exists(classroom_number, territory_id_int):
                self.toast.show(f"Кабинет '{classroom_number}' уже существует на этой территории!", success=False)
                return
        else:
            if (classroom_number != self.original_classroom_number or
                    territory_id_int != self.original_territory_id):
                if self.db_operations.check_classroom_exists(classroom_number, territory_id_int):
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


class TeacherForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, teacher_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_teacher_name = teacher_data['ФИО'] if teacher_data and edit_mode else ""

        saved_days = []
        saved_part_timer = False
        saved_territories = []

        if edit_mode and teacher_data:
            saved_part_timer = teacher_data.get('Совместитель', False)
            saved_days_str = teacher_data.get('[Дни занятий]', '')
            if saved_days_str and saved_days_str != 'Любые':
                saved_days = [day.strip() for day in saved_days_str.split(',')]
            saved_territories = teacher_data.get('Территории', [])

        self.full_name_field = ft.TextField(
            label="ФИО преподавателя",
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=teacher_data['ФИО'] if teacher_data and edit_mode else "",
        )

        self.part_timer_switch = ft.Switch(
            label=" Совместитель",
            value=saved_part_timer,
            label_style=ft.TextStyle(color=PALETTE[2]),
        )

        self.day_checkboxes = {}
        self.selected_days = saved_days.copy()

        days_of_week = [
            ("пн", "Понедельник"),
            ("вт", "Вторник"),
            ("ср", "Среда"),
            ("чт", "Четверг"),
            ("пт", "Пятница"),
            ("сб", "Суббота")
        ]

        day_checkbox_list = []
        for day_code, day_name in days_of_week:
            checkbox = ft.Checkbox(
                label=day_name,
                value=day_code in self.selected_days,
                label_style=ft.TextStyle(color=PALETTE[2]),
                border_side=ft.BorderSide(width=1, color=PALETTE[2]),
                on_change=lambda e, d=day_code: self._on_day_change(d, e.control.value)
            )
            self.day_checkboxes[day_code] = checkbox
            day_checkbox_list.append(checkbox)

        self.days_row1 = ft.Row(
            controls=day_checkbox_list[:3],
            spacing=20
        )

        self.days_row2 = ft.Row(
            controls=day_checkbox_list[3:],
            spacing=20
        )

        self.days_column = ft.Column(
            controls=[self.days_row1, self.days_row2],
            spacing=10
        )

        self.territories = self.db_operations.get_territories()
        self.selected_territories = saved_territories.copy()

        self.territory_checkbox_refs = {}
        self.territory_listview = ft.ListView(
            expand=False,
            height=150,
            spacing=5,
            padding=10,
            visible=False
        )

        self.territory_container = ft.Container(
            content=self.territory_listview,
            border=ft.border.all(1, PALETTE[1]),
            border_radius=5,
            visible=False
        )

        self.no_territories_message = ft.Text(
            "Сначала создайте территории в соответствующем разделе",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.territories) == 0
        )

        if self.territories:
            self._load_territories()

        self.info_note = ft.Text(
            "Если дни не выбраны, преподаватель может вести занятия в любые дни",
            size=12,
            color=ft.Colors.BLUE_700,
            italic=True
        )

    def _load_territories(self):
        if not self.territories:
            return

        self.territory_listview.controls.clear()
        self.territory_checkbox_refs.clear()

        items_per_row = 4

        for i in range(0, len(self.territories), items_per_row):
            row_territories = self.territories[i:i + items_per_row]

            row_controls = []
            for territory in row_territories:
                is_checked = territory['ID'] in self.selected_territories
                checkbox = ft.Checkbox(
                    label=territory['Название'],
                    value=is_checked,
                    label_style=ft.TextStyle(color=PALETTE[2]),
                    on_change=lambda e, territory_id=territory['ID']: self._on_territory_change(territory_id,
                                                                                                e.control.value)
                )
                self.territory_checkbox_refs[territory['ID']] = checkbox
                row_controls.append(checkbox)

            row = ft.Row(
                controls=row_controls,
                spacing=10,
                wrap=False
            )
            self.territory_listview.controls.append(row)

        self.territory_listview.visible = True
        self.territory_container.visible = True
        self.no_territories_message.visible = False

    def _on_territory_change(self, territory_id: int, is_checked: bool):
        if is_checked:
            if territory_id not in self.selected_territories:
                self.selected_territories.append(territory_id)
        else:
            if territory_id in self.selected_territories:
                self.selected_territories.remove(territory_id)

    def _on_day_change(self, day_code: str, is_checked: bool):
        if is_checked:
            if day_code not in self.selected_days:
                self.selected_days.append(day_code)
        else:
            if day_code in self.selected_days:
                self.selected_days.remove(day_code)

    def build(self) -> ft.Column:
        title = "Редактировать преподавателя" if self.edit_mode else "Добавить преподавателя"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.full_name_field,
            self.part_timer_switch,
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Территории", size=16, weight="bold", color=PALETTE[2]),
            self.no_territories_message,
            self.territory_container,
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Дни занятий (необязательно)", size=16, weight="bold", color=PALETTE[2]),
            self.info_note,
            self.days_column,
        ], spacing=15)

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
        full_name = self.full_name_field.value.strip()
        is_part_timer = self.part_timer_switch.value

        if error := Validator.validate_required(full_name, "ФИО преподавателя"):
            self.toast.show(error, success=False)
            return

        if len(self.selected_territories) == 0:
            self.toast.show("Выберите хотя бы одну территорию!", success=False)
            return

        if self.edit_mode:
            if full_name.upper() != self.original_teacher_name.upper():
                if error := Validator.validate_unique(self.db_operations, "Преподаватели", "ФИО", full_name):
                    self.toast.show(error, success=False)
                    return
        else:
            if error := Validator.validate_unique(self.db_operations, "Преподаватели", "ФИО", full_name):
                self.toast.show(error, success=False)
                return

        days_str = ', '.join(sorted(self.selected_days)) if self.selected_days else None

        teacher_data = {
            'ФИО': full_name,
            'Совместитель': is_part_timer,
            '[Дни занятий]': days_str,
            'Территории': self.selected_territories
        }

        self.on_submit(teacher_data)

    def set_page(self, page: ft.Page):
        self.page = page