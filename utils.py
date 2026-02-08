from typing import List, Dict, Any
from database.operations import DBOperations
from database.settings_manager import SettingsManager


class ScheduleGeneratorUtils:
    def __init__(self, db_ops: DBOperations):
        self.db_ops = db_ops
        self.settings_manager = SettingsManager(db_ops)

    def get_active_groups(self) -> List[Dict[str, Any]]:
        all_groups = self.settings_manager.get_groups_with_exclusion_and_order()

        active_groups = [group for group in all_groups if not group['Исключена']]

        active_groups.sort(key=lambda x: x['Порядок'])

        return active_groups

    def get_groups_for_schedule(self) -> List[Dict[str, Any]]:
        active_groups = self.get_active_groups()

        return active_groups

    def validate_schedule_settings(self) -> List[str]:
        errors = []

        active_groups = self.get_active_groups()
        if not active_groups:
            errors.append("Нет активных групп для генерации расписания")

        all_groups = self.db_ops.get_groups()
        all_group_ids = {group['ID'] for group in all_groups}
        group_order = self.settings_manager.get_group_order()

        for group_id in group_order:
            if group_id not in all_group_ids:
                errors.append(f"Группа с ID {group_id} из порядка не существует в базе")

        excluded_groups = self.settings_manager.get_excluded_groups()
        for group_id in excluded_groups:
            if group_id not in all_group_ids:
                errors.append(f"Исключенная группа с ID {group_id} не существует в базе")

        return errors

    def prepare_generation_data(self) -> Dict[str, Any]:
        return {
            'active_groups': self.get_active_groups(),
            'excluded_groups': self.settings_manager.get_excluded_groups(),
            'group_order': self.settings_manager.get_group_order(),
            'streams': self.settings_manager.get_streams_with_subjects(),
            'workloads': self.db_ops.get_workloads(),
            'teachers': self.db_ops.get_teachers_with_preferences(),
            'classrooms': self.db_ops.get_classrooms_with_territory_names(),
            'subjects': self.db_ops.get_subjects_with_module_names(),
        }
