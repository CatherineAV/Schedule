import os
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter
from typing import List, Dict, Any
from database.operations import DBOperations
from database.settings_manager import SettingsManager


class SimpleTemplateGenerator:
    def __init__(self, db_ops: DBOperations):
        self.db_ops = db_ops
        self.settings_manager = SettingsManager(db_ops)

        self.lesson_times = [
            "9.00 - 9.45", "9.55 - 10.40", "10.50 - 11.35",
            "11.45 - 12.30", "13.00-13.45", "14.15-15.00",
            "15.15 - 16.00", "16.10 - 16.55", "17.05 - 17.50",
            "18.00 - 18.45", "18.55 - 19.40"
        ]

        self.days_vertical = {
            'пн': ['п', 'о', 'н', 'е', 'д', 'е', 'л', 'ь', 'н', 'и', 'к'],
            'вт': ['в', 'т', 'о', 'р', 'н', 'и', 'к'],
            'ср': ['с', 'р', 'е', 'д', 'а'],
            'чт': ['ч', 'е', 'т', 'в', 'е', 'р', 'г'],
            'пт': ['п', 'я', 'т', 'н', 'и', 'ц', 'а'],
            'сб': ['с', 'у', 'б', 'б', 'о', 'т', 'а']
        }

        self.days_order = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']

        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    def generate_template_with_groups(self, output_path: str) -> str:
        wb = Workbook()
        ws = wb.active
        ws.title = "Расписание I семестр"

        # Получаем активные группы в правильном порядке
        active_groups = self._get_active_groups()

        # Формируем структуру групп с учетом подгрупп
        group_structure = self._build_group_structure(active_groups)

        # ========== ШАПКА ДОКУМЕНТА ==========
        self._create_document_header(ws)

        # ========== ЗАГОЛОВОК ТАБЛИЦЫ ==========
        self._create_table_header(ws, group_structure)

        # ========== ДНИ И УРОКИ ==========
        self._create_days_and_lessons(ws)

        # ========== ПОДВАЛ ==========
        self._create_footer(ws)

        # ========== НАСТРОЙКА СТИЛЕЙ ==========
        self._apply_styles(ws)
        self._adjust_column_widths(ws)

        # Сохранение
        wb.save(output_path)
        return os.path.abspath(output_path)

    def _get_active_groups(self) -> List[Dict[str, Any]]:
        """
        Получает активные группы в порядке, заданном в настройках
        """
        groups = self.settings_manager.get_groups_with_exclusion_and_order()

        # Фильтруем исключенные группы
        active_groups = [g for g in groups if not g['Исключена']]

        # Сортируем по порядку из настроек
        active_groups.sort(key=lambda x: x['Порядок'])

        return active_groups

    def _build_group_structure(self, groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Строит структуру групп с учетом подгрупп
        Группирует группы по названию и собирает все их подгруппы
        """
        # Группируем группы по названию
        grouped = {}

        for group in groups:
            name = group['Группа']
            subgroup = group.get('Подгруппа', 'Нет')

            if name not in grouped:
                grouped[name] = {
                    'name': name,
                    'subgroups': [],
                    'has_subgroups': False,
                    'self_education': group.get('Самообразование'),
                    'important_talks': group.get('Разговоры о важном', 0)
                }

            if subgroup != 'Нет' and subgroup != 'None':
                grouped[name]['subgroups'].append(subgroup)
                grouped[name]['has_subgroups'] = True

        # Преобразуем в список и сортируем подгруппы
        structure = []
        for name, group_info in grouped.items():
            if group_info['has_subgroups']:
                # Сортируем подгруппы в правильном порядке
                subgroups = group_info['subgroups']

                # Специальная сортировка для разных типов групп
                if 'ХКО' in name.upper():
                    # Для ХКО: Женская, Мужская
                    order = {'Женская': 1, 'Мужская': 2}
                    subgroups.sort(key=lambda x: order.get(x, 999))
                elif 'ХБО' in name.upper():
                    # Для ХБО: Кукольники, Бутафоры
                    order = {'Кукольники': 1, 'Бутафоры': 2}
                    subgroups.sort(key=lambda x: order.get(x, 999))
                else:
                    # Для обычных групп: 1, 2, 3
                    subgroups.sort(key=lambda x: int(x) if x.isdigit() else 999)

                group_info['subgroups'] = subgroups
                structure.append(group_info)
            else:
                # Группа без подгрупп
                structure.append({
                    'name': name,
                    'subgroups': [],
                    'has_subgroups': False,
                    'colspan': 1
                })

        return structure

    def _create_document_header(self, ws):
        """
        Создает шапку документа
        """
        # Заголовок
        ws.merge_cells('A1:CN1')
        ws['A1'] = 'Расписание занятий в I полугодии 2025/26 учебного года'
        ws['A1'].font = Font(size=16, bold=True)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

        # Утверждаю
        ws.merge_cells('AP3:AP5')
        ws['AP3'] = 'УТВЕРЖДАЮ'
        ws['AP3'].font = Font(bold=True)
        ws['AP3'].alignment = Alignment(horizontal='center', vertical='center')

        ws.merge_cells('AP6:AP7')
        ws['AP6'] = 'Директор ГБПОУ г. Москвы "ТХТК"'
        ws['AP6'].font = Font(bold=True)
        ws['AP6'].alignment = Alignment(horizontal='center', vertical='center')

        ws.merge_cells('AP8:AP9')
        ws['AP8'] = '____________Подбуртная Н.Н.'
        ws['AP8'].alignment = Alignment(horizontal='center', vertical='center')

        ws.merge_cells('AP10:AP11')
        ws['AP10'] = '"______"  _____________  20____ г.'
        ws['AP10'].alignment = Alignment(horizontal='center', vertical='center')

    def _create_table_header(self, ws, group_structure: List[Dict[str, Any]]):
        """
        Создает заголовок таблицы с группами
        Название группы объединяется на количество подгрупп
        Подгруппы пишутся каждая в своей ячейке
        """
        header_row = 12  # Строка с названиями групп
        subgroup_row = 13  # Строка с подгруппами

        # Фиксированные колонки
        ws[f'A{header_row}'] = 'Дни'
        ws[f'B{header_row}'] = 'Уроки'
        ws[f'C{header_row}'] = 'Расписание звонков на ул. Радио'

        # Стиль для фиксированных заголовков
        for col in ['A', 'B', 'C']:
            cell = ws[f'{col}{header_row}']
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        # Начинаем с колонки D
        current_col = 4

        for group in group_structure:
            if group['has_subgroups']:
                # Количество подгрупп = количество колонок
                subgroup_count = len(group['subgroups'])

                # Объединяем ячейки для названия группы
                start_col = current_col
                end_col = current_col + subgroup_count - 1

                start_letter = get_column_letter(start_col)
                end_letter = get_column_letter(end_col)

                # Объединяем ячейки
                merge_range = f'{start_letter}{header_row}:{end_letter}{header_row}'
                ws.merge_cells(merge_range)

                # Устанавливаем название группы
                group_cell = ws[f'{start_letter}{header_row}']
                group_cell.value = group['name']
                group_cell.font = Font(bold=True)
                group_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

                # Заполняем подгруппы каждая в своей колонке
                for i, subgroup in enumerate(group['subgroups']):
                    col = current_col + i
                    col_letter = get_column_letter(col)

                    sub_cell = ws[f'{col_letter}{subgroup_row}']

                    # Форматируем отображение подгруппы
                    if subgroup in ['1', '2', '3']:
                        sub_cell.value = f'{subgroup} п/гр'
                    elif subgroup == 'Женская':
                        sub_cell.value = 'Женская'
                    elif subgroup == 'Мужская':
                        sub_cell.value = 'Мужская'
                    elif subgroup == 'Кукольники':
                        sub_cell.value = 'Кукольники'
                    elif subgroup == 'Бутафоры':
                        sub_cell.value = 'Бутафоры'
                    else:
                        sub_cell.value = subgroup

                    sub_cell.font = Font(italic=True)
                    sub_cell.alignment = Alignment(horizontal='center', vertical='center')

                # Сдвигаем текущую колонку на количество подгрупп
                current_col += subgroup_count

            else:
                # Группа без подгрупп - одна колонка
                col_letter = get_column_letter(current_col)

                # Название группы
                group_cell = ws[f'{col_letter}{header_row}']
                group_cell.value = group['name']
                group_cell.font = Font(bold=True)
                group_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

                # В строке подгрупп оставляем пусто или ставим прочерк
                sub_cell = ws[f'{col_letter}{subgroup_row}']
                sub_cell.value = ''
                sub_cell.font = Font(italic=True)
                sub_cell.alignment = Alignment(horizontal='center', vertical='center')

                current_col += 1

    def _create_days_and_lessons(self, ws):
        """
        Создает строки с днями недели (вертикально) и уроками
        """
        start_row = 14

        for day_idx, day_letter in enumerate(self.days_order):
            # Определяем диапазон строк для этого дня (11 уроков)
            day_start_row = start_row + (day_idx * 11)
            day_end_row = day_start_row + 10

            # Получаем вертикальное написание дня
            day_vertical = self.days_vertical[day_letter]

            # Очищаем объединенные ячейки если были
            for row in range(day_start_row, day_end_row + 1):
                ws[f'A{row}'] = None

            # Заполняем каждую букву в отдельной строке
            for i, letter in enumerate(day_vertical):
                if i < 11:  # Не более 11 строк
                    row = day_start_row + i
                    cell = ws.cell(row=row, column=1)
                    cell.value = letter
                    cell.alignment = Alignment(
                        horizontal='center',
                        vertical='center'
                    )
                    cell.font = Font(bold=True)

            # Заполняем уроки и время для всех 11 строк
            for lesson_idx in range(11):
                row = day_start_row + lesson_idx

                # Номер урока
                ws.cell(row=row, column=2, value=lesson_idx + 1)
                ws.cell(row=row, column=2).alignment = Alignment(horizontal='center', vertical='center')

                # Время урока
                ws.cell(row=row, column=3, value=self.lesson_times[lesson_idx])
                ws.cell(row=row, column=3).alignment = Alignment(horizontal='center', vertical='center')

    def _create_footer(self, ws):
        """
        Создает подвал документа
        """
        # Находим последнюю использованную строку
        last_row = ws.max_row + 3

        # Подпись заместителя директора
        ws.merge_cells(f'CH{last_row}:CN{last_row}')
        ws[f'CH{last_row}'] = 'Заместитель директора по УР________________Соломина И.Д.'
        ws[f'CH{last_row}'].alignment = Alignment(horizontal='right')

        # Адреса территорий
        addr_row = last_row + 2
        ws.merge_cells(f'D{addr_row}:H{addr_row}')
        ws[f'D{addr_row}'] = 'Ул. Радио, д. 6/4, стр.1'
        ws[f'D{addr_row}'].font = Font(italic=True)

        ws.merge_cells(f'T{addr_row}:X{addr_row}')
        ws[f'T{addr_row}'] = '1-й Амбулаторный проезд, д. 8, стр. 2'
        ws[f'T{addr_row}'].font = Font(italic=True)

        ws.merge_cells(f'AJ{addr_row}:AN{addr_row}')
        ws[f'AJ{addr_row}'] = 'Московский драматический театр им. М.Н. Ермоловой'
        ws[f'AJ{addr_row}'].font = Font(italic=True)

    def _apply_styles(self, ws):
        """
        Применяет стили к таблице (только границы, без заливки)
        """
        # Применяем границы ко всей таблице
        for row in ws.iter_rows(min_row=12, max_row=ws.max_row - 5, max_col=50):
            for cell in row:
                if cell.value is not None or (cell.row >= 14 and cell.column >= 4):
                    cell.border = self.thin_border

    def _adjust_column_widths(self, ws):
        """
        Настраивает ширину колонок
        """
        # Фиксированные колонки
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 6
        ws.column_dimensions['C'].width = 15

        for col in range(4, 50):
            col_letter = get_column_letter(col)
            ws.column_dimensions[col_letter].width = 12