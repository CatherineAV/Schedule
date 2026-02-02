import flet as ft
import re
from typing import Callable, List, Dict, Optional, Any
from ui.components import PALETTE, Validator


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
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=group_data['Группа'] if group_data and edit_mode else "",
            on_change=self._update_subgroup_options
        )

        current_group_name = group_data['Группа'] if group_data and edit_mode else ""
        subgroup_options = self._get_subgroup_options(current_group_name)

        self.subgroup_dropdown = ft.Dropdown(
            label="Подгруппа",
            width=300,
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
            width=300,
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
            expand=True,
            border_color=PALETTE[3],
            color=PALETTE[2],
            visible=False,
        )

        self.new_module_name_field = ft.TextField(
            label="Название нового модуля",
            expand=True,
            border_color=PALETTE[3],
            color=PALETTE[2],
            visible=False,
        )

        self.territory_dropdown1 = ft.Dropdown(
            label="Основная территория",
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory1_change
        )

        self.classrooms_container1 = ft.Row(
            spacing=10,
            run_spacing=10,
            alignment=ft.MainAxisAlignment.START,
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
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory2_change
        )

        self.classrooms_container2 = ft.Row(
            spacing=10,
            run_spacing=10,
            alignment=ft.MainAxisAlignment.START,
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

        options2 = []
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

        if not territory_id:
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
                elif not self.territory_dropdown2.value:
                    self.territory_dropdown2.value = str(territory_id)
                    self._load_classrooms_for_territory2()
                elif self.territory_dropdown2.value == str(territory_id):
                    self._load_classrooms_for_territory2()

        self._update_territory_options()

        if self.territory_dropdown1.value:
            self._load_classrooms_for_territory1()
        if self.territory_dropdown2.value:
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

        self._update_territory_options()

        if self.territory_dropdown1.value:
            self._load_classrooms_for_territory1()
        if self.territory_dropdown2.value:
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

        territories_block.append(ft.Divider(height=20, color=PALETTE[1]))

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
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=module_data['Код'] if module_data and edit_mode else "",
        )

        self.module_name_field = ft.TextField(
            label="Название модуля",
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
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=classroom_data['Кабинет'] if classroom_data and edit_mode else "",
        )

        territory_options = [ft.dropdown.Option(str(territory['ID']), territory['Территория'])
                             for territory in self.territories]

        self.territory_dropdown = ft.Dropdown(
            label="Территория",
            expand=True,
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
            expand=True,
            border_color=PALETTE[3],
            bgcolor=ft.Colors.BLUE_GREY,
            color=PALETTE[2],
            on_change=self._on_territory1_change
        )

        self.territory_dropdown2 = ft.Dropdown(
            label="Дополнительная территория (необязательно)",
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
            ("пн", "Понедельник"),
            ("вт", "Вторник"),
            ("ср", "Среда"),
            ("чт", "Четверг"),
            ("пт", "Пятница"),
            ("сб", "Суббота")
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
                    border_side=ft.BorderSide(width=1, color=PALETTE[2]),
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

        options2 = []
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
        if territory2:
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
            value=initial_color,
            border_color=PALETTE[3],
            color=PALETTE[2],
            width=200,
            on_change=self._on_hex_change,
            # prefix_text="#"
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

        teachers = self.db_operations.get_table_data("Преподаватели")
        subjects = self.db_operations.get_subjects_with_module_names()
        groups = self.db_operations.get_groups()

        teacher_options = [ft.dropdown.Option(t['ФИО'], t['ФИО']) for t in teachers]
        subject_options = [ft.dropdown.Option(s['Дисциплина'], s['Дисциплина']) for s in subjects]

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
            border_color=PALETTE[3],
            color=PALETTE[2],
            value=hours_value,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Сообщения если нет данных
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
