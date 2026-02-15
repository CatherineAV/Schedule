import flet as ft
import re
from typing import Callable, List, Dict, Optional
from ui.components import PALETTE, Validator
from database.settings_manager import SettingsManager


class GroupForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, group_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode

        if edit_mode and group_data:
            self.original_group_name = group_data['Группа']
            self.original_subgroup = group_data['Подгруппа']
        else:
            self.original_group_name = ""
            self.original_subgroup = ""

        self.group_name_field = ft.TextField(
            label="Группа",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=group_data['Группа'] if group_data and edit_mode else "",
            on_change=self._update_subgroup_options
        )

        current_group_name = group_data['Группа'] if group_data and edit_mode else ""
        subgroup_options = self._get_subgroup_options(current_group_name)

        self.subgroup_dropdown = ft.Dropdown(
            label="Подгруппа",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            width=400,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=subgroup_options,
            value=group_data['Подгруппа'] if group_data and edit_mode else "Нет",
        )

        if edit_mode and group_data:
            self_education_value = group_data.get('Самообразование', 'Нет')
        else:
            self_education_value = "Нет"

        self.self_education_dropdown = ft.Dropdown(
            label="День самообразования",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            width=400,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=[
                ft.dropdown.Option("Нет"),
                ft.dropdown.Option("Пн"),
                ft.dropdown.Option("Вт"),
                ft.dropdown.Option("Ср"),
                ft.dropdown.Option("Чт"),
                ft.dropdown.Option("Пт"),
                ft.dropdown.Option("Сб")
            ],
            value=self_education_value
        )

        self.important_talks_switch = ft.Switch(
            label=" Разговоры о важном",
            value=bool(group_data.get('Разговоры о важном', 0)) if group_data and edit_mode else False,
            label_style=ft.TextStyle(color=PALETTE[2])
        )

    def _get_subgroup_options(self, group_name: str) -> List[ft.dropdown.Option]:
        if not group_name:
            return [
                ft.dropdown.Option("Нет"),
                ft.dropdown.Option("1"),
                ft.dropdown.Option("2"),
                ft.dropdown.Option("3"),
                ft.dropdown.Option("Кукольники"),
                ft.dropdown.Option("Бутафоры"),
                ft.dropdown.Option("Женская"),
                ft.dropdown.Option("Мужская")
            ]
        elif "ХБО" in group_name.upper():
            return [
                ft.dropdown.Option("Кукольники"),
                ft.dropdown.Option("Бутафоры")
            ]
        elif "ХКО" in group_name.upper():
            return [
                ft.dropdown.Option("Женская"),
                ft.dropdown.Option("Мужская")
            ]
        else:
            return [
                ft.dropdown.Option("Нет"),
                ft.dropdown.Option("1"),
                ft.dropdown.Option("2"),
                ft.dropdown.Option("3")
            ]

    def _update_subgroup_options(self, e):
        group_name = self.group_name_field.value
        subgroup_options = self._get_subgroup_options(group_name)

        self.subgroup_dropdown.options = subgroup_options

        current_subgroup = self.subgroup_dropdown.value
        valid_subgroups = [option.key for option in subgroup_options]

        if current_subgroup not in valid_subgroups:
            if ("ХКО" in group_name.upper() or "ХБО" in group_name.upper()):
                self.subgroup_dropdown.value = subgroup_options[0].key
            else:
                self.subgroup_dropdown.value = "Нет"

        if hasattr(self, 'page'):
            self.page.update()

    def build(self) -> ft.Column:
        title = "Редактировать группу" if self.edit_mode else "Добавить группу"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.group_name_field,
            self.subgroup_dropdown,
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

    def _on_form_submit(self, e):
        group_name = self.group_name_field.value.strip()
        subgroup = self.subgroup_dropdown.value
        self_education = self.self_education_dropdown.value if self.self_education_dropdown.value != "Нет" else None
        important_talks = 1 if self.important_talks_switch.value else 0

        if error := Validator.validate_required(group_name, "Название группы"):
            self.toast.show(error, success=False)
            return

        if not subgroup:
            self.toast.show("Выберите подгруппу!", success=False)
            return

        if error := Validator.validate_group(group_name, subgroup):
            self.toast.show(error, success=False)
            return

        if self.edit_mode:
            current_id = getattr(self, 'current_group_id', None)
            if self.db_operations.check_group_exists(group_name, subgroup, exclude_id=current_id):
                self.toast.show(f"Группа '{group_name}' с подгруппой '{subgroup}' уже существует!", success=False)
                return
        else:
            if self.db_operations.check_group_exists(group_name, subgroup):
                self.toast.show(f"Группа '{group_name}' с подгруппой '{subgroup}' уже существует!", success=False)
                return

        group_data = {
            'Группа': group_name,
            'Подгруппа': subgroup,
            'Самообразование': self_education,
            'Разговоры о важном': important_talks
        }

        self.on_submit(group_data)

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
        self.original_subject_name = subject_data['Дисциплина'] if subject_data and edit_mode else ""
        self.original_module = subject_data['Модуль'] if subject_data and edit_mode else ""
        self.pre_selected_classroom_ids = classroom_ids if classroom_ids else []

        self.subject_name_field = ft.TextField(
            label="Название дисциплины",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=subject_data['Дисциплина'] if subject_data and edit_mode else "",
        )

        self.modules = self.db_operations.get_modules()
        self.territories = self.db_operations.get_territories()

        module_options = [ft.dropdown.Option(module['Код'], f"{module['Код']} - {module['Название']}")
                          for module in self.modules]

        self.module_dropdown = ft.Dropdown(
            label="Модуль",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=module_options,
            value=subject_data['Модуль'] if subject_data and edit_mode else None,
        )

        self.add_new_module_switch = ft.Switch(
            label=" Добавить новый модуль",
            value=False,
            label_style=ft.TextStyle(color=PALETTE[2]),
            visible=not edit_mode,
            on_change=self._on_module_switch_change
        )

        self.new_module_code_field = ft.TextField(
            label="Код нового модуля",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            color=PALETTE[2],
            visible=False,
        )

        self.new_module_name_field = ft.TextField(
            label="Название нового модуля",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            color=PALETTE[2],
            visible=False,
        )

        self.territory_dropdown1 = ft.Dropdown(
            label="Основная территория",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory1_change
        )

        self.classrooms_container1 = ft.GridView(
            runs_count=4,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=3,
            max_extent=100,
            visible=False
        )

        self.classrooms_label1 = ft.Text(
            "Кабинеты основной территории:",
            size=14,
            weight="bold",
            color=PALETTE[2],
            visible=False
        )

        self.no_classrooms_message1 = ft.Text(
            "На этой территории нет кабинетов",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=False
        )

        self.territory_dropdown2 = ft.Dropdown(
            label="Дополнительная территория (необязательно)",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory2_change
        )

        self.classrooms_container2 = ft.GridView(
            runs_count=4,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=3,
            max_extent=100,
            visible=False
        )

        self.classrooms_label2 = ft.Text(
            "Кабинеты дополнительной территории:",
            size=14,
            weight="bold",
            color=PALETTE[2],
            visible=False
        )

        self.no_classrooms_message2 = ft.Text(
            "На этой территории нет кабинетов",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=False
        )

        self.no_territories_message = ft.Text(
            "Сначала создайте территории и кабинеты в соответствующих разделах",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.territories) == 0
        )

        self.classroom_checkbox_refs = {}
        self.selected_classrooms = self.pre_selected_classroom_ids.copy()

        self._update_territory_options()

        if edit_mode and subject_data and classroom_ids:
            self._load_territories_from_classrooms(classroom_ids)

        if self.pre_selected_classroom_ids:
            self._load_pre_selected_classrooms()

    def _update_territory_options(self):
        selected_territory1 = self.territory_dropdown1.value
        selected_territory2 = self.territory_dropdown2.value

        options1 = []
        for territory in self.territories:
            territory_id = str(territory['ID'])
            if territory_id != selected_territory2:
                options1.append(ft.dropdown.Option(territory_id, territory['Территория']))
        self.territory_dropdown1.options = options1

        options2 = [ft.dropdown.Option("Нет", "Нет")]
        for territory in self.territories:
            territory_id = str(territory['ID'])
            if territory_id != selected_territory1:
                options2.append(ft.dropdown.Option(territory_id, territory['Территория']))
        self.territory_dropdown2.options = options2

    def _on_territory1_change(self, e):
        if (self.territory_dropdown1.value and self.territory_dropdown2.value and
                self.territory_dropdown1.value == self.territory_dropdown2.value):
            self.territory_dropdown2.value = None
            self._hide_territory2_classrooms()

        self._update_territory_options()
        self._load_classrooms_for_territory1()

        if hasattr(self, 'page'):
            self.page.update()

    def _on_territory2_change(self, e):
        if self.territory_dropdown2.value == "Нет":
            self._hide_territory2_classrooms()
            self._update_territory_options()
            if hasattr(self, 'page'):
                self.page.update()
            return

        if (self.territory_dropdown1.value and self.territory_dropdown2.value and
                self.territory_dropdown1.value == self.territory_dropdown2.value):
            self.territory_dropdown1.value = None
            self._hide_territory1_classrooms()

        self._update_territory_options()
        self._load_classrooms_for_territory2()

        if hasattr(self, 'page'):
            self.page.update()

    def _load_classrooms_for_territory1(self):
        territory_id = self.territory_dropdown1.value

        if not territory_id:
            self.classrooms_label1.visible = False
            self.classrooms_container1.visible = False
            self.no_classrooms_message1.visible = False
            return

        territory_id_int = int(territory_id)
        classrooms = self.db_operations.get_classrooms_by_territory(territory_id_int)

        if classrooms:
            self.classrooms_label1.visible = True
            self.classrooms_container1.visible = True
            self.no_classrooms_message1.visible = False
            self.classrooms_container1.controls.clear()

            for classroom in classrooms:
                is_checked = classroom['ID'] in self.pre_selected_classroom_ids
                checkbox = ft.Checkbox(
                    label=classroom['Кабинет'],
                    value=is_checked,
                    border_side=ft.BorderSide(width=2, color=PALETTE[2]),
                    label_style=ft.TextStyle(color=PALETTE[2]),
                    on_change=lambda e, classroom_id=classroom['ID']: self._on_classroom_change(classroom_id,
                                                                                                e.control.value)
                )
                self.classroom_checkbox_refs[classroom['ID']] = checkbox
                self.classrooms_container1.controls.append(checkbox)
        else:
            self.classrooms_label1.visible = False
            self.classrooms_container1.visible = False
            self.no_classrooms_message1.visible = True

        if hasattr(self, 'page') and self.page:
            self.page.update()

    def _load_classrooms_for_territory2(self):
        territory_id = self.territory_dropdown2.value

        if not territory_id or territory_id == "Нет":
            self.classrooms_label2.visible = False
            self.classrooms_container2.visible = False
            self.no_classrooms_message2.visible = False
            return

        territory_id_int = int(territory_id)
        classrooms = self.db_operations.get_classrooms_by_territory(territory_id_int)

        if classrooms:
            self.classrooms_label2.visible = True
            self.classrooms_container2.visible = True
            self.no_classrooms_message2.visible = False

            self.classrooms_container2.controls.clear()

            for classroom in classrooms:
                is_checked = classroom['ID'] in self.pre_selected_classroom_ids
                checkbox = ft.Checkbox(
                    label=classroom['Кабинет'],
                    value=is_checked,
                    border_side=ft.BorderSide(width=2, color=PALETTE[2]),
                    label_style=ft.TextStyle(color=PALETTE[2]),
                    on_change=lambda e, classroom_id=classroom['ID']: self._on_classroom_change(classroom_id,
                                                                                                e.control.value)
                )
                self.classroom_checkbox_refs[classroom['ID']] = checkbox
                self.classrooms_container2.controls.append(checkbox)
        else:
            self.classrooms_label2.visible = False
            self.classrooms_container2.visible = False
            self.no_classrooms_message2.visible = True

        if hasattr(self, 'page') and self.page:
            self.page.update()

    def _hide_territory1_classrooms(self):
        self.classrooms_label1.visible = False
        self.classrooms_container1.visible = False
        self.no_classrooms_message1.visible = False

    def _hide_territory2_classrooms(self):
        self.classrooms_label2.visible = False
        self.classrooms_container2.visible = False
        self.no_classrooms_message2.visible = False

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
            self.module_dropdown.value = None
        else:
            self.new_module_code_field.visible = False
            self.new_module_name_field.visible = False
            self.module_dropdown.visible = True
            self.new_module_code_field.value = ""
            self.new_module_name_field.value = ""

            self.modules = self.db_operations.get_modules()
            module_options = [ft.dropdown.Option(module['Код'], f"{module['Код']} - {module['Название']}")
                              for module in self.modules]
            self.module_dropdown.options = module_options

        if hasattr(self, 'page'):
            self.page.update()

    def _load_pre_selected_classrooms(self):
        for classroom_id in self.pre_selected_classroom_ids:
            classroom = self.db_operations.get_classroom_by_id(classroom_id)
            if classroom:
                territory_id = classroom['ТерриторияID']

                if not self.territory_dropdown1.value:
                    self.territory_dropdown1.value = str(territory_id)
                    self._load_classrooms_for_territory1()
                elif self.territory_dropdown1.value == str(territory_id):
                    self._load_classrooms_for_territory1()
                elif not self.territory_dropdown2.value or self.territory_dropdown2.value == "Нет":
                    self.territory_dropdown2.value = str(territory_id)
                    self._load_classrooms_for_territory2()
                elif self.territory_dropdown2.value == str(territory_id):
                    self._load_classrooms_for_territory2()

        self._update_territory_options()

        if self.territory_dropdown1.value:
            self._load_classrooms_for_territory1()
        if self.territory_dropdown2.value and self.territory_dropdown2.value != "Нет":
            self._load_classrooms_for_territory2()

    def _load_territories_from_classrooms(self, classroom_ids: List[int]):
        territory_ids = set()
        for classroom_id in classroom_ids:
            classroom = self.db_operations.get_classroom_by_id(classroom_id)
            if classroom:
                territory_ids.add(str(classroom['ТерриторияID']))

        territory_ids_list = list(territory_ids)
        if len(territory_ids_list) > 0:
            self.territory_dropdown1.value = territory_ids_list[0]
        if len(territory_ids_list) > 1:
            self.territory_dropdown2.value = territory_ids_list[1]
        else:
            self.territory_dropdown2.value = "Нет"

        self._update_territory_options()

        if self.territory_dropdown1.value:
            self._load_classrooms_for_territory1()
        if self.territory_dropdown2.value and self.territory_dropdown2.value != "Нет":
            self._load_classrooms_for_territory2()

    def build(self) -> ft.Column:
        title = "Редактировать дисциплину" if self.edit_mode else "Добавить дисциплину"

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

        territories_block = [
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Территории", size=16, weight="bold", color=PALETTE[2]),
            self.no_territories_message,
            self.territory_dropdown1,
        ]

        territories_block.append(self.no_classrooms_message1)
        territories_block.append(self.classrooms_label1)
        territories_block.append(self.classrooms_container1)

        territories_block.extend([
            self.territory_dropdown2,
            self.no_classrooms_message2,
            self.classrooms_label2,
            self.classrooms_container2,
        ])

        scrollable_content.controls.extend(territories_block)

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

        if error := Validator.validate_required(subject_name, "Название дисциплины"):
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
            new_module_needed = True
        else:
            module = self.module_dropdown.value
            if not module:
                self.toast.show("Выберите модуль!", success=False)
                return
            new_module_needed = False

        if not self.territory_dropdown1.value:
            self.toast.show("Выберите основную территорию!", success=False)
            return

        if error := Validator.validate_classrooms(self.territory_dropdown1.value, self.selected_classrooms):
            self.toast.show(error, success=False)
            return

        if self.edit_mode:
            if (subject_name.upper() != self.original_subject_name.upper() or
                    module != self.original_module):
                if self.db_operations.check_subject_exists(subject_name, module):
                    self.toast.show(f"Дисциплина '{subject_name}' с модулем '{module}' уже существует!", success=False)
                    return
        else:
            if self.db_operations.check_subject_exists(subject_name, module):
                self.toast.show(f"Дисциплина '{subject_name}' с модулем '{module}' уже существует!", success=False)
                return

        if new_module_needed:
            if not self.db_operations.insert_module(module, self.new_module_name_field.value.strip()):
                self.toast.show("Ошибка при создании модуля!", success=False)
                return

        subject_data = {
            'Дисциплина': subject_name,
            'Модуль': module
        }

        self.on_submit(subject_data, self.selected_classrooms)

    def set_page(self, page: ft.Page):
        self.page = page


class ModuleForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, module_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_module_code = module_data['Код'] if module_data and edit_mode else ""

        self.module_code_field = ft.TextField(
            label="Код модуля",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=module_data['Код'] if module_data and edit_mode else "",
        )

        self.module_name_field = ft.TextField(
            label="Название модуля",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=module_data['Название'] if module_data and edit_mode else "",
        )

    def build(self) -> ft.Column:
        title = "Редактировать модуль" if self.edit_mode else "Добавить модуль"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.module_code_field,
            self.module_name_field,
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
        module_code = self.module_code_field.value.strip()
        module_name = self.module_name_field.value.strip()

        if error := Validator.validate_required(module_code, "Код модуля"):
            self.toast.show(error, success=False)
            return

        if error := Validator.validate_required(module_name, "Название модуля"):
            self.toast.show(error, success=False)
            return

        if error := Validator.validate_module_code(module_code):
            self.toast.show(error, success=False)
            return

        if error := Validator.validate_module_name(module_name):
            self.toast.show(error, success=False)
            return

        if self.edit_mode:
            if module_code.upper() != self.original_module_code.upper():
                if error := Validator.validate_unique(self.db_operations, "Модули", "Код", module_code):
                    self.toast.show(error, success=False)
                    return
        else:
            if error := Validator.validate_unique(self.db_operations, "Модули", "Код", module_code):
                self.toast.show(error, success=False)
                return

        module_data = {
            'Код': module_code,
            'Название': module_name
        }

        self.on_submit(module_data)

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
        self.original_classroom_number = classroom_data['Кабинет'] if classroom_data and edit_mode else ""
        self.original_territory_id = classroom_data['ТерриторияID'] if classroom_data and edit_mode else None

        self.territories = self.db_operations.get_territories()

        self.classroom_number_field = ft.TextField(
            label="Номер кабинета",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=classroom_data['Кабинет'] if classroom_data and edit_mode else "",
        )

        territory_options = [ft.dropdown.Option(str(territory['ID']), territory['Территория'])
                             for territory in self.territories]

        self.territory_dropdown = ft.Dropdown(
            label="Территория",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=territory_options,
            value=str(classroom_data['ТерриторияID']) if classroom_data and edit_mode else None,
        )

        self.capacity_field = ft.TextField(
            label="Вместимость (опционально)",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
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
            'Кабинет': classroom_number,
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
            saved_territories = [str(t) for t in saved_territories]

        self.full_name_field = ft.TextField(
            label="ФИО преподавателя",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=teacher_data['ФИО'] if teacher_data and edit_mode else "",
        )

        self.part_timer_switch = ft.Switch(
            label=" Совместитель",
            value=saved_part_timer,
            label_style=ft.TextStyle(color=PALETTE[2]),
        )

        self.territories = self.db_operations.get_territories()

        self.territory_dropdown1 = ft.Dropdown(
            label="Основная территория",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory1_change
        )

        self.territory_dropdown2 = ft.Dropdown(
            label="Дополнительная территория (необязательно)",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory2_change
        )

        self._update_territory_options()

        if saved_territories:
            if len(saved_territories) > 0 and saved_territories[0]:
                self.territory_dropdown1.value = saved_territories[0]
            if len(saved_territories) > 1 and saved_territories[1]:
                self.territory_dropdown2.value = saved_territories[1]
            else:
                self.territory_dropdown2.value = "Нет"

        self._update_territory_options()

        self.no_territories_message = ft.Text(
            "Сначала создайте территории в соответствующем разделе",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.territories) == 0
        )

        self.day_checkboxes = {}
        self.selected_days = saved_days.copy()

        days_of_week = [
            ("Пн", "Понедельник"),
            ("Вт", "Вторник"),
            ("Ср", "Среда"),
            ("Чт", "Четверг"),
            ("Пт", "Пятница"),
            ("Сб", "Суббота")
        ]

        self.day_columns = []

        for i in range(0, len(days_of_week), 2):
            group = days_of_week[i:i + 2]
            column_checkboxes = []

            for day_code, day_name in group:
                checkbox = ft.Checkbox(
                    label=day_name,
                    value=day_code in self.selected_days,
                    label_style=ft.TextStyle(color=PALETTE[2]),
                    border_side=ft.BorderSide(width=2, color=PALETTE[2]),
                    on_change=lambda e, d=day_code: self._on_day_change(d, e.control.value)
                )
                self.day_checkboxes[day_code] = checkbox
                column_checkboxes.append(checkbox)

            column = ft.Column(
                controls=column_checkboxes,
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.START
            )
            self.day_columns.append(column)

        self.days_container = ft.Row(
            controls=self.day_columns,
            spacing=40,
            alignment=ft.MainAxisAlignment.START
        )

        self.info_note = ft.Text(
            "Если дни не выбраны, преподаватель может вести занятия в любые дни",
            size=12,
            color=ft.Colors.BLUE_700,
            italic=True
        )

    def _update_territory_options(self):
        selected_territory1 = self.territory_dropdown1.value
        selected_territory2 = self.territory_dropdown2.value

        options1 = []
        for territory in self.territories:
            territory_id = str(territory['ID'])
            if territory_id != selected_territory2:
                options1.append(ft.dropdown.Option(territory_id, territory['Территория']))
        self.territory_dropdown1.options = options1

        options2 = [ft.dropdown.Option("Нет", "Нет")]
        for territory in self.territories:
            territory_id = str(territory['ID'])
            if territory_id != selected_territory1:
                options2.append(ft.dropdown.Option(territory_id, territory['Территория']))
        self.territory_dropdown2.options = options2

    def _on_territory1_change(self, e):
        if (self.territory_dropdown1.value and self.territory_dropdown2.value and
                self.territory_dropdown1.value == self.territory_dropdown2.value):
            self.territory_dropdown2.value = None

        self._update_territory_options()

        if hasattr(self, 'page'):
            self.page.update()

    def _on_territory2_change(self, e):
        if self.territory_dropdown2.value == "Нет":
            self._update_territory_options()
            if hasattr(self, 'page'):
                self.page.update()
            return

        if (self.territory_dropdown1.value and self.territory_dropdown2.value and
                self.territory_dropdown1.value == self.territory_dropdown2.value):
            self.territory_dropdown1.value = None

        self._update_territory_options()

        if hasattr(self, 'page'):
            self.page.update()

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
            self.territory_dropdown1,
            self.territory_dropdown2,
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Дни занятий (необязательно)", size=16, weight="bold", color=PALETTE[2]),
            self.info_note,
            self.days_container,
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

        territory1 = self.territory_dropdown1.value

        if not territory1:
            self.toast.show("Выберите основную территорию!", success=False)
            return

        territory2 = self.territory_dropdown2.value

        territory_ids = []
        if territory1:
            territory_ids.append(int(territory1))
        if territory2 and territory2 != "Нет":
            territory_ids.append(int(territory2))

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
            'Территории': territory_ids
        }

        self.on_submit(teacher_data)

    def set_page(self, page: ft.Page):
        self.page = page


class TerritoryForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, territory_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_territory_name = territory_data['Территория'] if territory_data and edit_mode else ""
        self.original_color = territory_data.get('Цвет', '#FFFFFF') if territory_data and edit_mode else "#FFFFFF"

        self.territory_name_field = ft.TextField(
            label="Название территории",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=territory_data['Территория'] if territory_data and edit_mode else "",
        )

        initial_color = territory_data.get('Цвет', '#FFFFFF') if territory_data and edit_mode else "#FFFFFF"

        self.color_display = ft.Container(
            width=50,
            height=50,
            border_radius=5,
            bgcolor=initial_color,
            border=ft.border.all(2, PALETTE[2]),
        )

        self.color_hex_field = ft.TextField(
            label="HEX код цвета",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            value=initial_color,
            border_color=PALETTE[3],
            color=PALETTE[2],
            width=200,
            on_change=self._on_hex_change,
        )

        self.preset_colors = [
            "#FF5252", "#FF4081", "#E040FB", "#7C4DFF", "#536DFE",
            "#448AFF", "#40C4FF", "#18FFFF", "#64FFDA", "#69F0AE",
            "#B2FF59", "#EEFF41", "#FFFF00", "#FFD740", "#FFAB40",
            "#FF6E40", "#FF3D00", "#8D6E63", "#9E9E9E", "#607D8B",
            "#18363E", "#5F97AA", "#2D5F6E", "#3E88A5", "#93C4D1"
        ]

        self.preset_color_containers = []
        for color in self.preset_colors:
            color_container = ft.Container(
                width=30,
                height=30,
                border_radius=5,
                bgcolor=color,
                border=ft.border.all(2, ft.Colors.WHITE if color != "#FFFFFF" else ft.Colors.BLACK),
                on_click=lambda e, col=color: self._select_preset_color(col),
                tooltip=color
            )
            self.preset_color_containers.append(color_container)

        self.preset_colors_row = ft.Row(
            controls=self.preset_color_containers,
            wrap=True,
            spacing=5,
            run_spacing=5
        )

    def _on_hex_change(self, e):
        hex_value = e.control.value
        if not hex_value.startswith("#"):
            hex_value = "#" + hex_value

        hex_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')

        if hex_pattern.match(hex_value):
            self.color_display.bgcolor = hex_value
            if hasattr(self, 'page'):
                self.page.update()
        else:
            pass

    def _select_preset_color(self, color):
        self.color_display.bgcolor = color
        self.color_hex_field.value = color
        if hasattr(self, 'page'):
            self.page.update()

    def build(self) -> ft.Column:
        title = "Редактировать территорию" if self.edit_mode else "Добавить территорию"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.territory_name_field,
            ft.Divider(height=20, color=PALETTE[1]),
            ft.Text("Выбор цвета территории", size=16, weight="bold", color=PALETTE[2]),
            ft.Row([
                self.color_display,
                self.color_hex_field
            ], spacing=20, alignment=ft.MainAxisAlignment.START),
            ft.Text("Выберите цвет из палитры:", size=14, color=PALETTE[2]),
            self.preset_colors_row,
            ft.Text("Цвет будет использоваться для визуального выделения территории в расписании",
                    size=12, color=ft.Colors.BLUE_700, italic=True)
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
        territory_name = self.territory_name_field.value.strip()
        color = self.color_hex_field.value

        if error := Validator.validate_required(territory_name, "Название территории"):
            self.toast.show(error, success=False)
            return

        hex_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
        if not hex_pattern.match(color):
            self.toast.show("Неверный формат HEX цвета! Используйте формат #RRGGBB", success=False)
            return

        if self.edit_mode:
            if territory_name.upper() != self.original_territory_name.upper():
                if self.db_operations.check_territory_exists(territory_name):
                    self.toast.show(f"Территория '{territory_name}' уже существует!", success=False)
                    return
        else:
            if self.db_operations.check_territory_exists(territory_name):
                self.toast.show(f"Территория '{territory_name}' уже существует!", success=False)
                return

        territory_data = {
            'Территория': territory_name,
            'Цвет': color
        }

        self.on_submit(territory_data)

    def set_page(self, page: ft.Page):
        self.page = page


class WorkloadForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, workload_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_data = workload_data.copy() if workload_data else {}

        self.settings_manager = SettingsManager(db_operations)

        teachers = self.db_operations.get_table_data("Преподаватели")
        teachers.sort(key=lambda x: x['ФИО'].lower())
        teacher_options = [ft.dropdown.Option(t['ФИО'], t['ФИО']) for t in teachers]

        subjects = self.db_operations.get_subjects_with_module_names()
        subjects.sort(key=lambda x: x['Дисциплина'].lower())
        subject_options = [ft.dropdown.Option(s['Дисциплина'], s['Дисциплина']) for s in subjects]

        groups = self.db_operations.get_groups()

        groups_with_order = self.settings_manager.get_groups_with_exclusion_and_order()
        order_dict = {g['ID']: g['Порядок'] for g in groups_with_order}
        groups.sort(key=lambda g: (
            order_dict.get(g['ID'], 999),
            g['Группа'].lower(),
            g['Подгруппа'].lower() if g['Подгруппа'] != 'Нет' else ''
        ))

        group_options = []
        for group in groups:
            group_name = group['Группа']
            subgroup = group['Подгруппа']
            if subgroup and subgroup != "Нет" and subgroup != "None":
                display_name = f"{group_name} - {subgroup}"
            else:
                display_name = group_name
            group_options.append(ft.dropdown.Option(display_name, display_name))

        teacher_value = workload_data.get('Преподаватель', '') if workload_data else ''
        self.teacher_dropdown = ft.Dropdown(
            label="Преподаватель",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=teacher_options,
            value=teacher_value,
        )

        subject_value = workload_data.get('Дисциплина', '') if workload_data else ''
        self.subject_dropdown = ft.Dropdown(
            label="Дисциплина",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=subject_options,
            value=subject_value,
        )

        group_value = ''
        if workload_data and 'Группа' in workload_data:
            group_name = workload_data['Группа']
            subgroup = workload_data.get('Подгруппа', 'Нет')
            if subgroup and subgroup != "Нет" and subgroup != "None":
                group_value = f"{group_name} - {subgroup}"
            else:
                group_value = group_name

        self.group_dropdown = ft.Dropdown(
            label="Группа",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=group_options,
            value=group_value,
        )

        hours_value = str(workload_data.get('Часы в неделю', '')) if workload_data else ''
        self.hours_field = ft.TextField(
            label="Часы в неделю",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=hours_value,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.no_teachers_message = ft.Text(
            "Сначала добавьте преподавателей",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(teachers) == 0
        )

        self.no_subjects_message = ft.Text(
            "Сначала добавьте дисциплины",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(subjects) == 0
        )

        self.no_groups_message = ft.Text(
            "Сначала добавьте группы",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(groups) == 0
        )

    def build(self) -> ft.Column:
        title = "Редактировать нагрузку" if self.edit_mode else "Добавить нагрузку"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),

            ft.Text("Преподаватель", size=16, weight="bold", color=PALETTE[2]),
            self.no_teachers_message,
            self.teacher_dropdown,

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Дисциплина", size=16, weight="bold", color=PALETTE[2]),
            self.no_subjects_message,
            self.subject_dropdown,

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Группа", size=16, weight="bold", color=PALETTE[2]),
            self.no_groups_message,
            self.group_dropdown,

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Часы", size=16, weight="bold", color=PALETTE[2]),
            self.hours_field,
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
        teacher = self.teacher_dropdown.value
        subject = self.subject_dropdown.value
        group_display = self.group_dropdown.value
        hours_str = self.hours_field.value.strip()

        if not teacher:
            self.toast.show("Выберите преподавателя!", success=False)
            return

        if not subject:
            self.toast.show("Выберите дисциплину!", success=False)
            return

        if not group_display:
            self.toast.show("Выберите группу!", success=False)
            return

        if not hours_str:
            self.toast.show("Введите количество часов в неделю!", success=False)
            return

        try:
            hours = int(hours_str)
            if hours <= 0:
                self.toast.show("Часы должны быть положительным числом!", success=False)
                return
            if hours > 40:
                self.toast.show("Часы не могут превышать 40 в неделю!", success=False)
                return
        except ValueError:
            self.toast.show("Часы должны быть числом!", success=False)
            return

        if ' - ' in group_display:
            parts = group_display.split(' - ')
            group_name = parts[0].strip()
            subgroup = parts[1].strip()
        else:
            group_name = group_display
            subgroup = "Нет"

        teacher_result = self.db_operations.db.execute_query(
            "SELECT ID FROM Преподаватели WHERE ФИО = ?",
            (teacher,)
        )
        if not teacher_result:
            self.toast.show("Преподаватель не найден!", success=False)
            return
        teacher_id = teacher_result[0]['ID']

        subject_result = self.db_operations.db.execute_query(
            "SELECT ID FROM Дисциплины WHERE Дисциплина = ?",
            (subject,)
        )
        if not subject_result:
            self.toast.show("Дисциплина не найдена!", success=False)
            return
        subject_id = subject_result[0]['ID']

        group_result = self.db_operations.db.execute_query(
            "SELECT ID FROM Группы WHERE Группа = ? AND Подгруппа = ?",
            (group_name, subgroup)
        )
        if not group_result:
            self.toast.show("Группа не найдена!", success=False)
            return
        group_id = group_result[0]['ID']

        workload_id = getattr(self, 'workload_id', None) if self.edit_mode else None
        if self.db_operations.check_workload_duplicate(teacher_id, subject_id, group_id, workload_id):
            self.toast.show(f"Такая нагрузка уже существует для преподавателя '{teacher}'!", success=False)
            return

        workload_data = {
            'Преподаватель': teacher,
            'Дисциплина': subject,
            'Группа': group_name,
            'Подгруппа': subgroup,
            'Часы в неделю': hours
        }

        self.on_submit(workload_data)

    def set_page(self, page: ft.Page):
        self.page = page


class MultiWorkloadForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, teacher_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode

        self.settings_manager = SettingsManager(db_operations)
        self.workload_rows = []
        self.max_rows = 25
        self.current_rows = 1

        self.teachers = self.db_operations.get_table_data("Преподаватели")
        self.teachers.sort(key=lambda x: x['ФИО'].lower())
        teacher_options = [ft.dropdown.Option(t['ФИО'], t['ФИО']) for t in self.teachers]

        self.subjects = self.db_operations.get_subjects_with_module_names()
        self.subjects.sort(key=lambda x: x['Дисциплина'].lower())

        self.groups = self.db_operations.get_groups()
        groups_with_order = self.settings_manager.get_groups_with_exclusion_and_order()
        order_dict = {g['ID']: g['Порядок'] for g in groups_with_order}

        self.groups.sort(key=lambda g: (
            order_dict.get(g['ID'], 999),
            g['Группа'].lower(),
            g['Подгруппа'].lower() if g['Подгруппа'] != 'Нет' else ''
        ))

        self.teacher_dropdown = ft.Dropdown(
            label="Преподаватель *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=teacher_options,
            value=teacher_data['ФИО'] if teacher_data and edit_mode else '',
        )

        self.workload_rows_container = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )

        self.add_row_button = ft.ElevatedButton(
            "Добавить нагрузку",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white", padding=15),
            on_click=self._add_workload_row,
            tooltip=f"Максимум {self.max_rows} строк"
        )

        self._create_workload_row()

        self.no_teachers_message = ft.Text(
            "Сначала добавьте преподавателей",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.teachers) == 0
        )

        self.no_subjects_message = ft.Text(
            "Сначала добавьте дисциплины",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.subjects) == 0
        )

        self.no_groups_message = ft.Text(
            "Сначала добавьте группы",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(self.groups) == 0
        )

    def _create_workload_row(self, row_data: Optional[Dict] = None):
        row_id = len(self.workload_rows)

        #self.subjects.sort(key=lambda x: x['Дисциплина'].lower())
        subject_options = [ft.dropdown.Option(s['Дисциплина'], s['Дисциплина']) for s in self.subjects]
        subject_dropdown = ft.Dropdown(
            label="Дисциплина *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=subject_options,
            value=row_data.get('Дисциплина', '') if row_data else '',
        )

        group_options = []
        for group in self.groups:
            group_name = group['Группа']
            subgroup = group['Подгруппа']
            if subgroup and subgroup != "Нет" and subgroup != "None":
                display_name = f"{group_name} - {subgroup}"
            else:
                display_name = group_name
            group_options.append(ft.dropdown.Option(display_name, display_name))

        group_dropdown = ft.Dropdown(
            label="Группа *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=group_options,
            value=row_data.get('Группа', '') if row_data else '',
        )

        hours_field = ft.TextField(
            label="Часы в неделю *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=str(row_data.get('Часы в неделю', '')) if row_data else '',
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_color=ft.Colors.RED_400,
            tooltip="Удалить строку",
            visible=row_id > 0,
            data=row_id,
            on_click=self._delete_workload_row
        )

        delete_container = ft.Container(
            content=delete_button,
            width=50,
            alignment=ft.alignment.center
        )

        row = ft.Row(
            controls=[
                ft.Container(
                    content=subject_dropdown,
                    expand=True,
                    margin=ft.margin.only(right=5)
                ),
                ft.Container(
                    content=group_dropdown,
                    expand=True,
                    margin=ft.margin.only(right=5)
                ),
                ft.Container(
                    content=hours_field,
                    expand=True,
                    margin=ft.margin.only(right=5)
                ),
                delete_container
            ],
            spacing=0,
            expand=True,
            alignment=ft.MainAxisAlignment.START
        )

        row_data = {
            'id': row_id,
            'row': row,
            'subject_dropdown': subject_dropdown,
            'group_dropdown': group_dropdown,
            'hours_field': hours_field,
            'delete_button': delete_button
        }

        self.workload_rows.append(row_data)
        self.workload_rows_container.controls.append(row)

        self._update_add_button_state()

    def _add_workload_row(self, e):
        if self.current_rows >= self.max_rows:
            self.toast.show(f"Достигнут максимум {self.max_rows} строк нагрузки!", success=False)
            return

        self._create_workload_row()
        self.current_rows += 1

        if hasattr(self, 'page'):
            self.page.update()

    def _delete_workload_row(self, e):
        delete_button = e.control

        row_to_delete = None
        for i, row_data in enumerate(self.workload_rows):
            if row_data['delete_button'] == delete_button:
                row_to_delete = i
                break

        if row_to_delete is None:
            return

        if row_to_delete == 0:
            self.toast.show("Первая строка не может быть удалена!", success=False)
            return

        self.workload_rows_container.controls.pop(row_to_delete)
        self.workload_rows.pop(row_to_delete)

        for i, row_data in enumerate(self.workload_rows):
            row_data['id'] = i
            row_data['delete_button'].visible = i > 0
            row_data['delete_button'].data = i

        self.current_rows -= 1
        self._update_add_button_state()

        if hasattr(self, 'page'):
            self.page.update()

    def _update_add_button_state(self):
        if self.current_rows >= self.max_rows:
            self.add_row_button.disabled = True
            self.add_row_button.tooltip = f"Достигнут максимум {self.max_rows} строк"
        else:
            self.add_row_button.disabled = False
            self.add_row_button.tooltip = f"Максимум {self.max_rows} строк"

    def build(self) -> ft.Column:
        title = "Добавить нагрузку преподавателю"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),

            ft.Text("Преподаватель", size=16, weight="bold", color=PALETTE[2]),
            self.no_teachers_message,
            self.teacher_dropdown,

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Нагрузка преподавателя", size=16, weight="bold", color=PALETTE[2]),
            self.no_subjects_message,
            self.no_groups_message,

            self.workload_rows_container,

            ft.Container(
                content=self.add_row_button,
                padding=ft.padding.only(top=10)
            ),

            ft.Text(f"* Обязательные поля. Можно добавить до {self.max_rows} строк нагрузки.",
                    size=12, color=ft.Colors.BLUE_700, italic=True)
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
        teacher = self.teacher_dropdown.value

        if not teacher:
            self.toast.show("Выберите преподавателя!", success=False)
            return

        teacher_result = self.db_operations.db.execute_query(
            "SELECT ID FROM Преподаватели WHERE ФИО = ?",
            (teacher,)
        )
        if not teacher_result:
            self.toast.show("Преподаватель не найден!", success=False)
            return
        teacher_id = teacher_result[0]['ID']

        workloads_data = []
        errors = []
        duplicates = []

        for i, row_data in enumerate(self.workload_rows):
            subject = row_data['subject_dropdown'].value
            group_display = row_data['group_dropdown'].value
            hours_str = row_data['hours_field'].value.strip()

            if not subject:
                errors.append(f"Строка {i + 1}: выберите дисциплину")
                continue

            if not group_display:
                errors.append(f"Строка {i + 1}: выберите группу")
                continue

            if not hours_str:
                errors.append(f"Строка {i + 1}: введите количество часов")
                continue

            try:
                hours = int(hours_str)
                if hours <= 0:
                    errors.append(f"Строка {i + 1}: часы должны быть положительным числом")
                    continue
                if hours > 40:
                    errors.append(f"Строка {i + 1}: часы не могут превышать 40 в неделю")
                    continue
            except ValueError:
                errors.append(f"Строка {i + 1}: часы должны быть числом")
                continue

            if ' - ' in group_display:
                parts = group_display.split(' - ')
                group_name = parts[0].strip()
                subgroup = parts[1].strip()
            else:
                group_name = group_display
                subgroup = "Нет"

            subject_result = self.db_operations.db.execute_query(
                "SELECT ID FROM Дисциплины WHERE Дисциплина = ?",
                (subject,)
            )
            if not subject_result:
                errors.append(f"Строка {i + 1}: дисциплина '{subject}' не найдена")
                continue
            subject_id = subject_result[0]['ID']

            group_result = self.db_operations.db.execute_query(
                "SELECT ID FROM Группы WHERE Группа = ? AND Подгруппа = ?",
                (group_name, subgroup)
            )
            if not group_result:
                errors.append(f"Строка {i + 1}: группа '{group_display}' не найдена")
                continue
            group_id = group_result[0]['ID']

            for j, existing_data in enumerate(workloads_data):
                if (existing_data['subject_id'] == subject_id and
                        existing_data['group_id'] == group_id):
                    duplicates.append(f"Строка {i + 1}: дублируется со строкой {j + 1}")
                    break

            if self.db_operations.check_workload_duplicate(teacher_id, subject_id, group_id):
                duplicates.append(f"Строка {i + 1}: такая нагрузка уже существует в базе данных")

            workload_data = {
                'Преподаватель': teacher,
                'Дисциплина': subject,
                'Группа': group_name,
                'Подгруппа': subgroup,
                'Часы в неделю': hours,
                'teacher_id': teacher_id,
                'subject_id': subject_id,
                'group_id': group_id
            }

            workloads_data.append(workload_data)

        if duplicates:
            for duplicate in duplicates[:3]:
                self.toast.show(duplicate, success=False)
            if len(duplicates) > 3:
                self.toast.show(f"... и еще {len(duplicates) - 3} дубликатов", success=False)
            return

        if errors:
            for error in errors[:3]:
                self.toast.show(error, success=False)
            if len(errors) > 3:
                self.toast.show(f"... и еще {len(errors) - 3} ошибок", success=False)
            return

        if not workloads_data:
            self.toast.show("Добавьте хотя бы одну строку нагрузки!", success=False)
            return

        for workload in workloads_data:
            workload.pop('teacher_id', None)
            workload.pop('subject_id', None)
            workload.pop('group_id', None)

        self.on_submit(workloads_data)

    def set_page(self, page: ft.Page):
        self.page = page


class StreamForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable, db_operations, toast,
                 edit_mode: bool = False, stream_data: Optional[Dict] = None):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_operations = db_operations
        self.toast = toast
        self.edit_mode = edit_mode
        self.original_stream_name = stream_data['Поток'] if stream_data and edit_mode else ""

        self.settings_manager = SettingsManager(db_operations)
        all_groups = self.db_operations.get_groups()
        groups_with_order = self.settings_manager.get_groups_with_exclusion_and_order()
        order_dict = {g['ID']: g['Порядок'] for g in groups_with_order}
        all_groups.sort(key=lambda g: (
            order_dict.get(g['ID'], 999),
            g['Группа'].lower(),
            g['Подгруппа'].lower() if g['Подгруппа'] != 'Нет' else ''
        ))
        all_subjects = self.db_operations.get_subjects_with_module_names()
        all_subjects.sort(key=lambda x: x['Дисциплина'].lower())

        self.group_options = []
        for group in all_groups:
            group_name = group['Группа']
            subgroup = group['Подгруппа']
            if subgroup and subgroup != 'Нет' and subgroup != 'None':
                display_name = f"{group_name} - {subgroup}"
            else:
                display_name = group_name
            self.group_options.append(
                ft.dropdown.Option(
                    str(group['ID']),
                    display_name
                )
            )

        self.subject_options = []
        for subject in all_subjects:
            self.subject_options.append(
                ft.dropdown.Option(
                    str(subject['ID']),
                    subject['Дисциплина']
                )
            )

        self.stream_name_field = ft.TextField(
            label="Название потока",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=stream_data['Поток'] if stream_data and edit_mode else "",  # ← Изменили ключ
        )

        self.group1_dropdown = ft.Dropdown(
            label="Группа 1 *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=self.group_options.copy(),
            value=str(stream_data.get('Группа1_ID', '')) if stream_data and edit_mode and stream_data.get(
                'Группа1_ID') else None,
        )

        self.group2_dropdown = ft.Dropdown(
            label="Группа 2 *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=self.group_options.copy(),
            value=str(stream_data.get('Группа2_ID', '')) if stream_data and edit_mode and stream_data.get(
                'Группа2_ID') else None,
        )

        self.group3_dropdown = ft.Dropdown(
            label="Группа 3 (необязательно)",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=self.group_options.copy(),
            value=str(stream_data.get('Группа3_ID', '')) if stream_data and edit_mode and stream_data.get(
                'Группа3_ID') else None,
        )

        self.group4_dropdown = ft.Dropdown(
            label="Группа 4 (необязательно)",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=self.group_options.copy(),
            value=str(stream_data.get('Группа4_ID', '')) if stream_data and edit_mode and stream_data.get(
                'Группа4_ID') else None,
        )

        self.subjects_dropdown = ft.Dropdown(
            label="Дисциплины для объединения *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=self.subject_options.copy(),
            hint_text="Выберите дисциплины...",
        )

        self.selected_subjects_container = ft.GridView(
            runs_count=3,
            spacing=8,
            run_spacing=8,
            child_aspect_ratio=2.5,
            max_extent=120,
            visible=False,
            padding=5,
        )

        self.selected_subjects = []
        self.selected_subject_ids = []

        if edit_mode and stream_data:
            subject_ids = stream_data.get('Дисциплины_ID', [])
            subject_names = stream_data.get('Дисциплины_список', [])

            self.selected_subject_ids = subject_ids
            self.selected_subjects = subject_names

            self._update_selected_subjects_display()

            current_subject_options = []
            for option in self.subject_options:
                subject_id = int(option.key)
                if subject_id in subject_ids:
                    continue
                current_subject_options.append(option)

            self.subjects_dropdown.options = current_subject_options

        self.no_groups_message = ft.Text(
            "Сначала добавьте группы в разделе 'Группы'",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(all_groups) == 0
        )

        self.no_subjects_message = ft.Text(
            "Сначала добавьте дисциплины в разделе 'Дисциплины'",
            size=14,
            color=ft.Colors.ORANGE_700,
            visible=len(all_subjects) == 0
        )

    def _update_selected_subjects_display(self):
        if not self.selected_subjects:
            self.selected_subjects_container.visible = False
            if hasattr(self, 'selected_subjects_label'):
                self.selected_subjects_label.visible = False
            return

        self.selected_subjects_container.controls.clear()

        for i, subject_name in enumerate(self.selected_subjects):
            chip = ft.Chip(
                label=ft.Text(subject_name, color=PALETTE[2]),
                bgcolor=PALETTE[4],
                on_delete=lambda e, idx=i: self._remove_subject(idx),
                delete_icon_color=PALETTE[2],
                delete_icon_tooltip="Удалить"
            )
            self.selected_subjects_container.controls.append(chip)

        self.selected_subjects_container.visible = True
        if hasattr(self, 'selected_subjects_label'):
            self.selected_subjects_label.visible = True

    def _remove_subject(self, index):
        if 0 <= index < len(self.selected_subjects):
            removed_subject_id = self.selected_subject_ids[index]
            removed_subject_name = self.selected_subjects[index]

            self.selected_subjects.pop(index)
            self.selected_subject_ids.pop(index)

            option = ft.dropdown.Option(
                str(removed_subject_id),
                removed_subject_name
            )
            self.subjects_dropdown.options.append(option)
            self.subjects_dropdown.options.sort(key=lambda x: x.text)
            self._update_selected_subjects_display()

            if hasattr(self, 'page'):
                self.page.update()

    def build(self) -> ft.Column:
        title = "Редактировать поток" if self.edit_mode else "Добавить поток"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),

            ft.Text("Основная информация", size=16, weight="bold", color=PALETTE[2]),
            self.stream_name_field,

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Группы в потоке", size=16, weight="bold", color=PALETTE[2]),
            ft.Text("Можно объединить от 2 до 4 групп",
                    size=12, color=ft.Colors.BLUE_700, italic=True),
            self.no_groups_message,
            self.group1_dropdown,
            self.group2_dropdown,
            self.group3_dropdown,
            self.group4_dropdown,

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Дисциплины для объединения", size=16, weight="bold", color=PALETTE[2]),
            ft.Text("Выберите дисциплины, на которых эти группы объединяются в поток",
                    size=12, color=ft.Colors.BLUE_700, italic=True),
            self.no_subjects_message,

            ft.Text("Выбранные дисциплины:",
                    size=14, color=PALETTE[2], weight="bold",
                    visible=bool(self.selected_subjects)),
            self.selected_subjects_container,

            ft.Row([
                self.subjects_dropdown,
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    icon_color=ft.Colors.WHITE,
                    bgcolor=PALETTE[3],
                    tooltip="Добавить дисциплину",
                    on_click=self._add_subject
                )
            ], spacing=10),
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

    def _add_subject(self, e):
        if not self.subjects_dropdown.value:
            self.toast.show("Выберите дисциплину!", success=False)
            return

        subject_id = int(self.subjects_dropdown.value)

        subject_name = None
        for option in self.subject_options:
            if option.key == self.subjects_dropdown.value:
                subject_name = option.text
                break

        if not subject_name:
            return

        if subject_id in self.selected_subject_ids:
            self.toast.show("Эта дисциплина уже добавлена!", success=False)
            return

        self.selected_subject_ids.append(subject_id)
        self.selected_subjects.append(subject_name)

        self._update_selected_subjects_display()

        parent = self.subjects_dropdown.parent

        remaining_options = [
            ft.dropdown.Option(key=opt.key, text=opt.text)
            for opt in self.subject_options
            if int(opt.key) not in self.selected_subject_ids
        ]

        new_dropdown = ft.Dropdown(
            label="Дисциплины для объединения *",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            options=remaining_options,
            hint_text="Выберите дисциплины...",
        )

        if parent and hasattr(parent, 'controls'):
            for i, control in enumerate(parent.controls):
                if control == self.subjects_dropdown:
                    parent.controls[i] = new_dropdown
                    self.subjects_dropdown = new_dropdown
                    break

        if hasattr(self, 'page'):
            self.page.update()

    def _on_form_submit(self, e):
        stream_name = self.stream_name_field.value.strip()
        group1_id = self.group1_dropdown.value
        group2_id = self.group2_dropdown.value
        group3_id = self.group3_dropdown.value
        group4_id = self.group4_dropdown.value

        if not stream_name:
            self.toast.show("Введите название потока!", success=False)
            return

        if not group1_id or not group2_id:
            self.toast.show("Выберите первую и вторую группу!", success=False)
            return

        if not self.selected_subject_ids:
            self.toast.show("Выберите хотя бы одну дисциплину для объединения!", success=False)
            return

        group_ids = []
        if group1_id and group1_id != 'None':
            try:
                group_ids.append(int(group1_id))
            except ValueError:
                self.toast.show(f"Некорректный ID группы 1: {group1_id}", success=False)
                return

        if group2_id and group2_id != 'None':
            try:
                group_ids.append(int(group2_id))
            except ValueError:
                self.toast.show(f"Некорректный ID группы 2: {group2_id}", success=False)
                return

        if group3_id and group3_id != 'None':
            try:
                group_ids.append(int(group3_id))
            except ValueError:
                self.toast.show(f"Некорректный ID группы 3: {group3_id}", success=False)
                return

        if group4_id and group4_id != 'None':
            try:
                group_ids.append(int(group4_id))
            except ValueError:
                self.toast.show(f"Некорректный ID группы 4: {group4_id}", success=False)
                return

        if len(set(group_ids)) != len(group_ids):
            self.toast.show("Группы не должны повторяться в потоке!", success=False)
            return

        stream_data = {
            'Поток': stream_name,
            'Группы_список': group_ids,
            'Дисциплины_ID': self.selected_subject_ids,
            'Дисциплины_список': self.selected_subjects
        }

        if len(group_ids) > 0:
            stream_data['Группа1_ID'] = group_ids[0]
        if len(group_ids) > 1:
            stream_data['Группа2_ID'] = group_ids[1]
        if len(group_ids) > 2:
            stream_data['Группа3_ID'] = group_ids[2]
        if len(group_ids) > 3:
            stream_data['Группа4_ID'] = group_ids[3]

        self.on_submit(stream_data)

    def set_page(self, page: ft.Page):
        self.page = page


class GroupsManagementForm:
    def __init__(self, on_submit: Callable, on_cancel: Callable,
                 db_operations, settings_manager, toast):
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.db_ops = db_operations
        self.settings_manager = settings_manager
        self.toast = toast

        self.all_groups = self.settings_manager.get_groups_with_exclusion_and_order()

        self.excluded_groups = self.settings_manager.get_excluded_groups()
        self.group_order = self.settings_manager.get_group_order()

        self._create_controls()

    def _create_controls(self):
        self.groups_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        self.order_text_field = ft.TextField(
            label="Порядок групп (ID через запятую)",
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=", ".join(str(id) for id in self.group_order),
            hint_text="Например: 1, 3, 5, 2, 4"
        )

        self.reset_order_button = ft.ElevatedButton(
            "Восстановить порядок по умолчанию",
            icon=ft.Icons.RESTORE,
            style=ft.ButtonStyle(bgcolor=PALETTE[2], color="white"),
            on_click=self._reset_order
        )

        self.info_text = ft.Text(
            "Группы, отмеченные галочкой, будут исключены из расписания. "
            "Порядок групп определяет их расположение в итоговом расписании.",
            size=12,
            color=ft.Colors.BLUE_700,
            italic=True
        )

        self._populate_groups_list()

    def _populate_groups_list(self):
        self.groups_list.controls.clear()

        for group in self.all_groups:
            group_id = group['ID']
            group_name = group['Группа']
            subgroup = group['Подгруппа']

            if subgroup and subgroup != 'Нет':
                display_name = f"{group_name} - {subgroup}"
            else:
                display_name = group_name

            order = group['Порядок']
            order_text = f"#{order + 1}" if order < 999 else "не задан"

            row = ft.Row([
                ft.Checkbox(
                    value=group['Исключена'],
                    on_change=lambda e, gid=group_id: self._on_exclusion_change(gid, e.control.value),
                    border_side=ft.BorderSide(width=2, color=PALETTE[2]),
                    label_style=ft.TextStyle(color=PALETTE[2])
                ),
                ft.Text(
                    f"{display_name} (ID: {group_id}, Порядок: {order_text})",
                    color=PALETTE[2],
                    expand=True
                ),
                ft.Container(
                    width=50,
                    content=ft.Text(
                        f"#{order + 1}" if order < 999 else "",
                        color=ft.Colors.GREEN if order < 999 else ft.Colors.GREY,
                        weight="bold"
                    ),
                    alignment=ft.alignment.center
                )
            ], spacing=15, alignment=ft.MainAxisAlignment.START)

            self.groups_list.controls.append(row)

    def _on_exclusion_change(self, group_id: int, is_excluded: bool):
        if is_excluded:
            if group_id not in self.excluded_groups:
                self.excluded_groups.append(group_id)
        else:
            if group_id in self.excluded_groups:
                self.excluded_groups.remove(group_id)

    def _reset_order(self, e):
        all_group_ids = [group['ID'] for group in self.all_groups if not group['Исключена']]
        self.group_order = all_group_ids
        self.order_text_field.value = ", ".join(str(id) for id in self.group_order)
        if hasattr(self, 'page'):
            self.page.update()
        self.toast.show("Порядок сброшен по умолчанию", success=True)

    def build(self) -> ft.Column:
        title = "Управление группами в расписании"

        scrollable_content = ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            ft.Divider(height=10, color=PALETTE[1]),

            ft.Text("Исключение групп из расписания", size=16, weight="bold", color=PALETTE[2]),
            ft.Text("Отметьте группы, которые не должны попадать в итоговое расписание:",
                    size=12, color=PALETTE[2]),

            ft.Container(
                content=self.groups_list,
                height=300,
                border=ft.border.all(1, PALETTE[1]),
                border_radius=5,
                padding=10
            ),

            ft.Divider(height=20, color=PALETTE[1]),

            ft.Text("Порядок групп в расписании", size=16, weight="bold", color=PALETTE[2]),
            ft.Text("Укажите ID групп через запятую в нужном порядке:",
                    size=12, color=PALETTE[2]),

            self.order_text_field,

            ft.Row([
                self.reset_order_button,
                ft.Text("(неисключенные группы будут отсортированы по ID)",
                        size=11, color=ft.Colors.GREY_600, italic=True)
            ], spacing=10),

            ft.Divider(height=20, color=PALETTE[1]),

            self.info_text,

            ft.Text(f"Всего групп: {len(self.all_groups)}, "
                    f"Исключено: {len(self.excluded_groups)}, "
                    f"Активных: {len(self.all_groups) - len(self.excluded_groups)}",
                    size=12, color=PALETTE[2], weight="bold"),
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
        try:
            order_text = self.order_text_field.value.strip()
            if order_text:
                new_order = [int(id.strip()) for id in order_text.split(',') if id.strip().isdigit()]
            else:
                new_order = []

            all_group_ids = {group['ID'] for group in self.all_groups}
            for group_id in new_order:
                if group_id not in all_group_ids:
                    self.toast.show(f"Группа с ID {group_id} не существует!", success=False)
                    return

            for excluded_id in self.excluded_groups:
                if excluded_id in new_order:
                    self.toast.show(f"Исключенная группа с ID {excluded_id} не может быть в порядке!", success=False)
                    return

            self.group_order = new_order

            params = {
                'excluded_groups': self.excluded_groups,
                'group_order': self.group_order
            }

            if self.settings_manager.save_generation_params(params):
                self.toast.show("Настройки групп успешно сохранены!", success=True)
                self.on_submit(params)
            else:
                self.toast.show("Ошибка при сохранении настроек!", success=False)

        except ValueError:
            self.toast.show("Некорректный формат ID групп!", success=False)
        except Exception as ex:
            self.toast.show(f"Ошибка: {str(ex)}", success=False)

    def set_page(self, page: ft.Page):
        self.page = page
