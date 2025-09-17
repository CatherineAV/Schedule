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

        return ft.Column([
            ft.Text(title, size=18, weight="bold", color=PALETTE[2]),
            self.group_name_field,
            self.subgroup_label,
            self.subgroup_checkboxes,
            self.self_education_dropdown,
            self.important_talks_switch,

            ft.Container(expand=True),

            ft.Container(
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
        ], spacing=15, expand=True)

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
