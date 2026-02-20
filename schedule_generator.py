import random, os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from database.operations import DBOperations
from database.settings_manager import SettingsManager
from schedule_template import SimpleTemplateGenerator
from excel_filler import ExcelFiller


class ScheduleGenerator:
    def __init__(self, db_ops: DBOperations):
        self.db_ops = db_ops
        self.settings_manager = SettingsManager(db_ops)
        self.template_generator = SimpleTemplateGenerator(db_ops)

        # Константы из примера
        self.DAYS = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
        self.LESSONS_PER_DAY = 11
        self.MAX_LESSONS_PER_DAY = 10
        self.MAX_HOURS_PER_WEEK = 44

        # Структуры данных
        self.schedule = {}  # [group_id][day][lesson] = урок
        self.teacher_schedule = {}  # [teacher_id][day][lesson] = group_id
        self.classroom_schedule = {}  # [classroom_id][day][lesson] = group_id
        self.lessons_per_day = {}  # [group_id][day] = количество уроков
        self.teacher_territories = {}  # [teacher_id] = [территории]

    def generate_schedule(self, output_path: str = None) -> str:
        """Генерирует расписание на основе данных из нагрузки"""

        # 1. Загружаем данные
        data = self._load_data()

        # 2. Создаем словарь с названиями групп для Excel
        self.group_names = {}
        for group in data['active_groups']:
            group_id = group['ID']
            group_name = group['Группа']
            subgroup = group.get('Подгруппа', 'Нет')

            if subgroup != 'Нет':
                full_name = f"{group_name} ({subgroup})"
            else:
                full_name = group_name

            self.group_names[group_id] = {
                'name': group_name,
                'subgroup': subgroup,
                'full_name': full_name
            }

        # 3. Инициализируем структуры
        self._initialize_structures(data)

        # 4. Группируем нагрузку по группам
        workload_by_group = self._group_workload_by_group(data)

        # 5. Размещаем потоки (ВРЕМЕННО ОТКЛЮЧАЕМ)
        # self._place_streams(data)

        # 6. Размещаем обычные предметы для каждой группы
        self._place_regular_subjects(workload_by_group, data)

        # 7. Генерируем Excel
        return self._generate_excel(output_path, data)

    def _load_data(self) -> Dict:
        """Загружает все необходимые данные"""
        active_groups = self.settings_manager.get_groups_with_exclusion_and_order()
        active_groups = [g for g in active_groups if not g['Исключена']]

        # Загружаем преподавателей с их территориями
        teachers = self.db_ops.get_teachers_with_preferences()
        for teacher in teachers:
            teacher_id = teacher['ID']
            territories = self.db_ops.get_teacher_territories(teacher_id)
            self.teacher_territories[teacher_id] = [t['Территория'] for t in territories]

        return {
            'active_groups': active_groups,
            'streams': self.settings_manager.get_streams_with_subjects(),
            'workloads': self.db_ops.get_workloads(),
            'teachers': teachers,
            'classrooms': self.db_ops.get_classrooms_with_territory_names(),
            'subjects': self.db_ops.get_subjects_with_module_names(),
        }

    def _initialize_structures(self, data: Dict):
        """Инициализирует все структуры"""
        for group in data['active_groups']:
            group_id = group['ID']
            self.schedule[group_id] = {day: [None] * self.LESSONS_PER_DAY for day in self.DAYS}
            self.lessons_per_day[group_id] = {day: 0 for day in self.DAYS}

        for teacher in data['teachers']:
            teacher_id = teacher['ID']
            self.teacher_schedule[teacher_id] = {day: [None] * self.LESSONS_PER_DAY for day in self.DAYS}

        for classroom in data['classrooms']:
            classroom_id = classroom['ID']
            self.classroom_schedule[classroom_id] = {day: [None] * self.LESSONS_PER_DAY for day in self.DAYS}

    def _group_workload_by_group(self, data: Dict) -> Dict:
        """Группирует нагрузку по группам с учетом подгрупп"""

        # Создаем маппинг названий групп на ID
        group_name_to_id = {}
        for group in data['active_groups']:
            group_name = group['Группа']
            subgroup = group.get('Подгруппа', 'Нет')

            if subgroup != 'Нет':
                full_name = f"{group_name} ({subgroup})"
            else:
                full_name = group_name
            group_name_to_id[full_name] = group['ID']

        # Группируем нагрузку
        workload_by_group = {}

        for w in data['workloads']:
            group_name = w['Группа']
            subgroup = w.get('Подгруппа', 'Нет')

            if subgroup != 'Нет':
                full_name = f"{group_name} ({subgroup})"
            else:
                full_name = group_name

            group_id = group_name_to_id.get(full_name)
            if group_id:
                if group_id not in workload_by_group:
                    workload_by_group[group_id] = []
                workload_by_group[group_id].append(w)

        return workload_by_group

    def _can_place_with_movement(self, group_id: int, day: str, lesson: int,
                                 territory: str, data: Dict[str, Any]) -> bool:
        """
        Проверяет, можно ли разместить предмет с учетом перемещений по территориям
        """
        # Если это первый урок в этот день, перемещение не нужно
        if lesson == 0:
            return True

        # Получаем предыдущий урок
        prev_lesson = self.schedule[group_id][day][lesson - 1]

        # Если предыдущего урока нет, считаем что группа была на своей территории
        if prev_lesson is None:
            # Проверяем, не перемещались ли мы уже сегодня
            if len(self.group_movements[group_id][day]) >= 2:
                return False  # Уже было 2 перемещения

            # Находим предыдущий непустой урок
            prev_filled = None
            for l in range(lesson - 1, -1, -1):
                if self.schedule[group_id][day][l] is not None:
                    prev_filled = self.schedule[group_id][day][l]
                    break

            if prev_filled and prev_filled.get('territory') != territory:
                # Нужно перемещение
                if len(self.group_movements[group_id][day]) >= 1:
                    return False  # Уже было перемещение
                return True
            return True

        # Если есть предыдущий урок, проверяем его территорию
        prev_territory = prev_lesson.get('territory')

        if prev_territory != territory:
            # Нужно перемещение
            if len(self.group_movements[group_id][day]) >= 1:
                return False  # Уже было перемещение
            return True

        return True

    def _place_subject_with_parity(self, group_id: int, subject_name: str,
                                   subject_id: int, teacher: Dict,
                                   classrooms: List[Dict], hours: int,
                                   parity: str, data: Dict[str, Any]) -> bool:
        """
        Размещает предмет с учетом четности недели
        """
        teacher_id = teacher['ID'] if teacher else None
        teacher_days = self._get_teacher_available_days(teacher)

        # Инициализируем запись о четности для этого предмета
        if subject_id not in self.week_parity[group_id]:
            self.week_parity[group_id][subject_id] = {
                'parity': parity,
                'placed_weeks': []
            }

        hours_remaining = hours

        while hours_remaining > 0:
            placed = False

            # Перемешиваем дни
            days = self.DAYS.copy()
            random.shuffle(days)

            for day in days:
                # Проверяем, может ли преподаватель в этот день
                if teacher_days and day not in teacher_days:
                    continue

                # Проверяем, не превышен ли лимит уроков в этот день
                if self.lessons_per_day[group_id][day] >= self.MAX_LESSONS_PER_DAY:
                    continue

                for lesson in range(self.LESSONS_PER_DAY - 1):
                    # Проверяем, свободен ли урок у группы
                    if self.schedule[group_id][day][lesson] is not None:
                        continue

                    # Определяем территорию для проверки перемещений
                    territory = None
                    if classrooms:
                        # Пробуем разные возможные ключи для территории
                        if 'Территория' in classrooms[0]:
                            territory = classrooms[0]['Территория']
                        elif 'territory' in classrooms[0]:
                            territory = classrooms[0]['territory']
                        elif 'Territory' in classrooms[0]:
                            territory = classrooms[0]['Territory']

                    # Проверяем, можно ли разместить с учетом перемещений
                    if not self._can_place_with_movement(group_id, day, lesson, territory, data):
                        continue

                    # Проверяем, свободен ли преподаватель
                    if teacher_id and self.teacher_schedule[teacher_id][day][lesson] is not None:
                        continue

                    # Проверяем, свободен ли кабинет
                    classroom = None
                    classroom_id = None
                    classroom_number = None

                    if classrooms:
                        # Ищем свободный кабинет
                        for c in classrooms:
                            c_id = c['ID']
                            if self.classroom_schedule[c_id][day][lesson] is None:
                                classroom = c
                                classroom_id = c_id

                                # Пробуем разные возможные ключи для номера кабинета
                                if 'Номер кабинета' in c:
                                    classroom_number = c['Номер кабинета']
                                elif 'Кабинет' in c:
                                    classroom_number = c['Кабинет']
                                elif 'number' in c:
                                    classroom_number = c['number']
                                elif 'classroom' in c:
                                    classroom_number = c['classroom']
                                else:
                                    classroom_number = str(c_id)

                                # Пробуем разные возможные ключи для территории
                                if 'Территория' in c:
                                    territory = c['Территория']
                                elif 'territory' in c:
                                    territory = c['territory']

                                break

                        if not classroom:
                            continue

                    # Определяем, на какие недели ставить
                    weeks_to_place = ['обе']
                    if parity == 'верхняя':
                        weeks_to_place = ['верхняя']
                    elif parity == 'нижняя':
                        weeks_to_place = ['нижняя']

                    for week in weeks_to_place:
                        if week not in self.week_parity[group_id][subject_id]['placed_weeks']:
                            # Размещаем предмет
                            self.schedule[group_id][day][lesson] = {
                                'subject': subject_name,
                                'subject_id': subject_id,
                                'teacher': teacher['ФИО'] if teacher else None,
                                'teacher_id': teacher_id,
                                'classroom': classroom_number,
                                'classroom_id': classroom_id,
                                'territory': territory,
                                'is_stream': False,
                                'stream_id': None,
                                'week_parity': week,
                                'weeks': [week]
                            }

                            # Отмечаем занятость
                            if teacher_id:
                                self.teacher_schedule[teacher_id][day][lesson] = group_id

                            if classroom_id:
                                self.classroom_schedule[classroom_id][day][lesson] = group_id

                            self.lessons_per_day[group_id][day] += 1
                            self.week_parity[group_id][subject_id]['placed_weeks'].append(week)

                            hours_remaining -= 1
                            placed = True

                            # Если предмет на обе недели, ставим сдвоенный урок
                            if parity == 'обе' and lesson + 1 < self.LESSONS_PER_DAY:
                                next_lesson = lesson + 1
                                if (self.schedule[group_id][day][next_lesson] is None and
                                        self.lessons_per_day[group_id][day] < self.MAX_LESSONS_PER_DAY and
                                        (not teacher_id or self.teacher_schedule[teacher_id][day][
                                            next_lesson] is None)):

                                    second_week = 'нижняя' if week == 'верхняя' else 'верхняя'

                                    if second_week not in self.week_parity[group_id][subject_id]['placed_weeks']:
                                        self.schedule[group_id][day][next_lesson] = {
                                            'subject': subject_name,
                                            'subject_id': subject_id,
                                            'teacher': teacher['ФИО'] if teacher else None,
                                            'teacher_id': teacher_id,
                                            'classroom': classroom_number,
                                            'classroom_id': classroom_id,
                                            'territory': territory,
                                            'is_stream': False,
                                            'stream_id': None,
                                            'week_parity': second_week,
                                            'weeks': [second_week]
                                        }

                                        if teacher_id:
                                            self.teacher_schedule[teacher_id][day][next_lesson] = group_id

                                        if classroom_id:
                                            self.classroom_schedule[classroom_id][day][next_lesson] = group_id

                                        self.lessons_per_day[group_id][day] += 1
                                        self.week_parity[group_id][subject_id]['placed_weeks'].append(second_week)
                                        hours_remaining -= 1

                            break

                    if placed:
                        break

                if placed:
                    break

            if not placed:
                print(f"Не удалось разместить {subject_name} для группы {group_id}, осталось {hours_remaining} часов")
                return False

        return True

    def _get_display_name(self, subject: Dict) -> str:
        """Получает отображаемое название предмета"""
        name = subject['Дисциплина']

        # Если есть скобки, берем то, что в скобках
        import re
        match = re.search(r'\(([^)]+)\)', name)
        if match:
            return match.group(1)

        # Если МДК и длинное название, сокращаем
        if 'МДК' in name and len(name) > 15:
            return name[:12] + '...'

        return name

    def _place_important_talks(self, data: Dict[str, Any]):
        """
        Размещает "Разговоры о важном" в расписании
        Ставятся либо в начале, либо в конце дня
        """
        for group in data['active_groups']:
            if group.get('important_talks'):
                group_id = group['ID']

                # Выбираем случайный день (кроме субботы)
                available_days = [d for d in self.DAYS if d != 'сб']
                day = random.choice(available_days)

                # Выбираем позицию: 0 - начало дня, -1 - конец дня
                position = random.choice([0, -1])

                if position == 0:
                    lesson = 0  # Первый урок
                else:
                    # Ищем последний свободный урок
                    for lesson in range(self.LESSONS_PER_DAY - 1, -1, -1):
                        if self.schedule[group_id][day][lesson] is None:
                            break

                if lesson >= 0:
                    self.schedule[group_id][day][lesson] = {
                        'subject': 'Разговоры о важном',
                        'teacher': None,
                        'classroom': None,
                        'territory': None,
                        'is_stream': False,
                        'stream_id': None,
                        'week_parity': 'обе'
                    }

    def _place_streams(self, data: Dict[str, Any]):
        """
        Размещает предметы, которые идут потоком для нескольких групп
        """
        print("\n" + "=" * 50)
        print("РАЗМЕЩЕНИЕ ПОТОКОВ")
        print("=" * 50)

        for stream in data['streams']:
            stream_id = stream['ID']
            stream_name = stream['Поток']

            # Получаем ID групп из потока
            group_ids = []
            if stream.get('Группа1_ID'):
                group_ids.append(stream['Группа1_ID'])
            if stream.get('Группа2_ID'):
                group_ids.append(stream['Группа2_ID'])
            if stream.get('Группа3_ID'):
                group_ids.append(stream['Группа3_ID'])
            if stream.get('Группа4_ID'):
                group_ids.append(stream['Группа4_ID'])

            if not group_ids:
                continue

            # Получаем предметы для потока
            subject_ids = stream.get('Дисциплины_ID', [])
            subject_names = stream.get('Дисциплины_список', [])

            print(f"\nПоток {stream_id}: {stream_name}, группы: {group_ids}, предметы: {subject_names}")

            for subject_id in subject_ids:
                # Находим нагрузку для этого предмета
                workload = None
                for w in data['workloads']:
                    subject_name = w.get('Дисциплина')
                    # Проверяем, что предмет принадлежит потоку
                    if subject_name in subject_names:
                        # Проверяем, что нагрузка относится к одной из групп потока
                        group_name = w.get('Группа')
                        subgroup = w.get('Подгруппа', 'Нет')

                        # Формируем полное имя группы из нагрузки
                        if subgroup != 'Нет' and subgroup != 'None':
                            w_full_name = f"{group_name} ({subgroup})"
                        else:
                            w_full_name = group_name

                        # Ищем эту группу среди групп потока
                        for group_id in group_ids:
                            # Находим группу по ID
                            for g in data['active_groups']:
                                if g['ID'] == group_id:
                                    g_name = g['Группа']
                                    g_sub = g.get('Подгруппа', 'Нет')

                                    if g_sub != 'Нет':
                                        g_full_name = f"{g_name} ({g_sub})"
                                    else:
                                        g_full_name = g_name

                                    if g_full_name == w_full_name:
                                        workload = w
                                        break
                            if workload:
                                break
                    if workload:
                        break

                if not workload:
                    print(f"  Не найдена нагрузка для предмета {subject_id}")
                    continue

                # Находим преподавателя
                teacher_name = workload.get('Преподаватель')
                teacher = None
                for t in data['teachers']:
                    if t['ФИО'] == teacher_name:
                        teacher = t
                        break

                if not teacher:
                    print(f"  Преподаватель {teacher_name} не найден")
                    continue

                # Находим предмет
                subject = next((s for s in data['subjects'] if s['ID'] == subject_id), {})
                display_name = self._get_display_name(subject)

                # Получаем количество часов
                hours = workload.get('Часы в неделю', 0)

                print(f"  Предмет: {display_name}, часы: {hours}, преподаватель: {teacher_name}")

                # Определяем четность недели
                if hours <= 2:
                    parity = random.choice(['верхняя', 'нижняя'])
                else:
                    parity = 'обе'

                # Размещаем поток
                self._place_stream_with_parity(
                    group_ids, stream_id, display_name, subject_id,
                    teacher, hours, parity, data
                )

    def _place_stream_with_parity(self, group_ids: List[int], stream_id: int,
                                  subject_name: str, subject_id: int,
                                  teacher: Dict, hours: int, parity: str,
                                  data: Dict[str, Any]):
        """
        Размещает поток с учетом четности недели
        """
        teacher_id = teacher['ID'] if teacher else None
        teacher_days = self._get_teacher_available_days(teacher)

        # Получаем территории преподавателя
        teacher_territories = []
        if teacher_id:
            teacher_territories = self.db_ops.get_teacher_territories(teacher_id)

        print(
            f"\n  Размещение потока {stream_id}: {subject_name}, групп: {len(group_ids)}, часов: {hours}, четность: {parity}")
        print(f"  Преподаватель: {teacher['ФИО']}, территории: {[t['Территория'] for t in teacher_territories]}")

        # Инициализируем запись о четности для каждой группы
        for group_id in group_ids:
            if subject_id not in self.week_parity[group_id]:
                self.week_parity[group_id][subject_id] = {
                    'parity': parity,
                    'placed_weeks': []
                }

        hours_remaining = hours

        while hours_remaining > 0:
            placed = False

            days = self.DAYS.copy()
            random.shuffle(days)

            for day in days:
                # Проверяем, может ли преподаватель в этот день
                if teacher_days and day not in teacher_days:
                    continue

                # Проверяем лимит уроков для всех групп
                max_lessons_ok = True
                for group_id in group_ids:
                    if self.lessons_per_day[group_id][day] >= self.MAX_LESSONS_PER_DAY:
                        max_lessons_ok = False
                        break

                if not max_lessons_ok:
                    continue

                for lesson in range(self.LESSONS_PER_DAY - 1):
                    # Проверяем, свободен ли урок у всех групп
                    all_free = True
                    for group_id in group_ids:
                        if self.schedule[group_id][day][lesson] is not None:
                            all_free = False
                            break

                    if not all_free:
                        continue

                    # Проверяем, свободен ли преподаватель
                    if teacher_id:
                        teacher_free = True
                        for group_id in group_ids:
                            if self.teacher_schedule[teacher_id][day][lesson] is not None:
                                teacher_free = False
                                break

                        if not teacher_free:
                            continue

                    # Определяем территорию для занятия (приоритет у преподавателя)
                    territory = None
                    if teacher_territories:
                        # Берем первую территорию преподавателя
                        territory = teacher_territories[0]['Территория']

                    # Проверяем перемещения для каждой группы
                    movements_ok = True
                    for group_id in group_ids:
                        if not self._can_place_with_movement(group_id, day, lesson, territory, data):
                            movements_ok = False
                            break

                    if not movements_ok:
                        continue

                    # Определяем, на какие недели ставить
                    weeks_to_place = ['обе']
                    if parity == 'верхняя':
                        weeks_to_place = ['верхняя']
                    elif parity == 'нижняя':
                        weeks_to_place = ['нижняя']

                    for week in weeks_to_place:
                        # Проверяем, не поставили ли уже эту неделю для какой-то группы
                        week_available = True
                        for group_id in group_ids:
                            if week in self.week_parity[group_id][subject_id]['placed_weeks']:
                                week_available = False
                                break

                        if not week_available:
                            continue

                        # Размещаем предмет для всех групп
                        for group_id in group_ids:
                            self.schedule[group_id][day][lesson] = {
                                'subject': subject_name,
                                'subject_id': subject_id,
                                'teacher': teacher['ФИО'] if teacher else None,
                                'teacher_id': teacher_id,
                                'classroom': None,  # Для потока кабинет не указываем
                                'classroom_id': None,
                                'territory': territory,
                                'is_stream': True,
                                'stream_id': stream_id,
                                'week_parity': week,
                                'weeks': [week]
                            }

                            if teacher_id:
                                self.teacher_schedule[teacher_id][day][lesson] = group_id

                            self.lessons_per_day[group_id][day] += 1
                            self.week_parity[group_id][subject_id]['placed_weeks'].append(week)

                        hours_remaining -= 1
                        placed = True

                        # Если предмет на обе недели, ставим сдвоенный урок
                        if parity == 'обе' and lesson + 1 < self.LESSONS_PER_DAY:
                            next_lesson = lesson + 1

                            # Проверяем, свободен ли следующий урок
                            next_free = True
                            for group_id in group_ids:
                                if self.schedule[group_id][day][next_lesson] is not None:
                                    next_free = False
                                    break
                                if self.lessons_per_day[group_id][day] >= self.MAX_LESSONS_PER_DAY:
                                    next_free = False
                                    break

                            if next_free and (
                                    not teacher_id or self.teacher_schedule[teacher_id][day][next_lesson] is None):
                                second_week = 'нижняя' if week == 'верхняя' else 'верхняя'

                                # Проверяем, доступна ли вторая неделя
                                second_week_available = True
                                for group_id in group_ids:
                                    if second_week in self.week_parity[group_id][subject_id]['placed_weeks']:
                                        second_week_available = False
                                        break

                                if second_week_available:
                                    for group_id in group_ids:
                                        self.schedule[group_id][day][next_lesson] = {
                                            'subject': subject_name,
                                            'subject_id': subject_id,
                                            'teacher': teacher['ФИО'] if teacher else None,
                                            'teacher_id': teacher_id,
                                            'classroom': None,
                                            'classroom_id': None,
                                            'territory': territory,
                                            'is_stream': True,
                                            'stream_id': stream_id,
                                            'week_parity': second_week,
                                            'weeks': [second_week]
                                        }

                                        if teacher_id:
                                            self.teacher_schedule[teacher_id][day][next_lesson] = group_id

                                        self.lessons_per_day[group_id][day] += 1
                                        self.week_parity[group_id][subject_id]['placed_weeks'].append(second_week)

                                    hours_remaining -= 1

                        break

                if placed:
                    break

            if not placed:
                print(f"    Не удалось разместить поток {subject_name}, осталось {hours_remaining} часов")
                break

    def _place_subject_for_stream(self, group_ids: List[int], stream_id: int,
                                  subject_name: str, teacher: Dict,
                                  classrooms: List[Dict], hours: int,
                                  data: Dict[str, Any]):
        """
        Размещает предмет для потока групп
        """
        # Определяем четность недели для этого предмета
        if hours <= 2:
            # 1 час в неделю - ставим либо на верхнюю, либо на нижнюю
            parity = random.choice(['верхняя', 'нижняя'])
        else:
            # 2+ часа - ставим на обе недели
            parity = 'обе'

        # Ищем свободное время для всех групп одновременно
        for day in self.DAYS:
            for lesson in range(self.LESSONS_PER_DAY - 1):
                # Проверяем, свободен ли этот урок у всех групп
                all_free = True
                for group_id in group_ids:
                    if self.schedule[group_id][day][lesson] is not None:
                        all_free = False
                        break

                if all_free:
                    # Проверяем свободен ли преподаватель
                    teacher_id = teacher['ID'] if teacher else None
                    if teacher_id and self.teacher_schedule[teacher_id][day][lesson] is not None:
                        continue

                    # Проверяем свободен ли кабинет
                    if classrooms:
                        classroom = random.choice(classrooms)
                        classroom_id = classroom['ID']
                        if self.classroom_schedule[classroom_id][day][lesson] is not None:
                            continue
                    else:
                        classroom = None
                        classroom_id = None

                    # Размещаем предмет для всех групп
                    for group_id in group_ids:
                        self.schedule[group_id][day][lesson] = {
                            'subject': subject_name,
                            'teacher': teacher['ФИО'] if teacher else None,
                            'teacher_id': teacher_id,
                            'classroom': classroom['Номер кабинета'] if classroom else None,
                            'classroom_id': classroom_id,
                            'territory': classroom['Территория'] if classroom else None,
                            'is_stream': True,
                            'stream_id': stream_id,
                            'week_parity': parity
                        }

                        # Отмечаем занятость преподавателя
                        if teacher_id:
                            self.teacher_schedule[teacher_id][day][lesson] = group_id

                        # Отмечаем занятость кабинета
                        if classroom_id:
                            self.classroom_schedule[classroom_id][day][lesson] = group_id

                    # Уменьшаем оставшиеся часы
                    hours -= 2 if parity == 'обе' else 1
                    if hours <= 0:
                        return

                    # Если поставили на обе недели, используем 2 часа
                    if parity == 'обе':
                        # Пробуем поставить еще один урок в тот же день
                        if lesson + 1 < self.LESSONS_PER_DAY:
                            next_lesson = lesson + 1
                            all_free_next = True
                            for group_id in group_ids:
                                if self.schedule[group_id][day][next_lesson] is not None:
                                    all_free_next = False
                                    break

                            if all_free_next and (
                                    not teacher_id or self.teacher_schedule[teacher_id][day][next_lesson] is None):
                                for group_id in group_ids:
                                    self.schedule[group_id][day][next_lesson] = {
                                        'subject': subject_name,
                                        'teacher': teacher['ФИО'] if teacher else None,
                                        'teacher_id': teacher_id,
                                        'classroom': classroom['Номер кабинета'] if classroom else None,
                                        'classroom_id': classroom_id,
                                        'territory': classroom['Территория'] if classroom else None,
                                        'is_stream': True,
                                        'stream_id': stream_id,
                                        'week_parity': parity
                                    }

                                    if teacher_id:
                                        self.teacher_schedule[teacher_id][day][next_lesson] = group_id

                                    if classroom_id:
                                        self.classroom_schedule[classroom_id][day][next_lesson] = group_id

                                hours -= 1
                                if hours <= 0:
                                    return

    def _place_regular_subjects(self, workload_by_group: Dict, data: Dict):
        """Размещает обычные предметы для каждой группы"""

        for group_id, workloads in workload_by_group.items():
            print(f"\nГруппа {group_id}: {len(workloads)} предметов")

            # Сортируем предметы по часам (от большего к меньшему)
            workloads.sort(key=lambda x: x['Часы в неделю'], reverse=True)

            for w in workloads:
                subject_name = w['Дисциплина']
                teacher_name = w['Преподаватель']
                hours = w['Часы в неделю']

                # Находим преподавателя
                teacher = next((t for t in data['teachers'] if t['ФИО'] == teacher_name), None)
                if not teacher:
                    continue

                # Находим предмет
                subject = next((s for s in data['subjects'] if s['Дисциплина'] == subject_name), None)
                if not subject:
                    continue

                # Находим кабинеты для предмета
                classrooms = self.db_ops.get_classrooms_by_subject(subject['ID'])

                # Получаем территории преподавателя
                teacher_terr = self.teacher_territories.get(teacher['ID'], [])

                # Фильтруем кабинеты по территориям преподавателя
                preferred_classrooms = [c for c in classrooms if c.get('Территория') in teacher_terr]
                other_classrooms = [c for c in classrooms if c.get('Территория') not in teacher_terr]
                all_classrooms = preferred_classrooms + other_classrooms

                # Размещаем предмет
                self._place_subject(
                    group_id=group_id,
                    subject_name=self._get_display_name(subject),
                    teacher=teacher,
                    classrooms=all_classrooms,
                    hours=hours,
                    data=data
                )

    def _place_subject(self, group_id: int, subject_name: str, teacher: Dict,
                       classrooms: List[Dict], hours: int, data: Dict):
        """Размещает один предмет для группы"""

        teacher_id = teacher['ID']
        teacher_days = self._get_teacher_available_days(teacher)

        # Определяем, сколько уроков нужно поставить
        if hours >= 2:
            lessons_needed = hours // 2
            if hours % 2 != 0:
                lessons_needed += 1
            print(f"  {subject_name}: {hours}ч -> {lessons_needed} сдвоенных уроков")
        else:
            lessons_needed = hours
            print(f"  {subject_name}: {hours}ч -> {lessons_needed} одиночных уроков")

        lessons_placed = 0

        while lessons_placed < lessons_needed:
            placed = False

            # Перебираем дни, начиная с наименее загруженных
            days_with_load = [(day, self.lessons_per_day[group_id][day]) for day in self.DAYS]
            days_with_load.sort(key=lambda x: x[1])

            for day, current_load in days_with_load:
                # Проверяем, может ли преподаватель в этот день
                if teacher_days and day not in teacher_days:
                    continue

                # Проверяем лимит уроков в день
                if current_load >= self.MAX_LESSONS_PER_DAY:
                    continue

                # Для сдвоенных уроков нужно больше места
                if hours >= 2 and current_load >= self.MAX_LESSONS_PER_DAY - 1:
                    continue

                # Ищем свободный слот
                for lesson in range(self.LESSONS_PER_DAY):
                    # Для сдвоенных уроков нужны два подряд
                    if hours >= 2:
                        if lesson + 1 >= self.LESSONS_PER_DAY:
                            continue
                        if (self.schedule[group_id][day][lesson] is not None or
                                self.schedule[group_id][day][lesson + 1] is not None):
                            continue
                    else:
                        if self.schedule[group_id][day][lesson] is not None:
                            continue

                    # Проверяем преподавателя
                    if hours >= 2:
                        if (self.teacher_schedule[teacher_id][day][lesson] is not None or
                                self.teacher_schedule[teacher_id][day][lesson + 1] is not None):
                            continue
                    else:
                        if self.teacher_schedule[teacher_id][day][lesson] is not None:
                            continue

                    # Ищем кабинет
                    classroom = None
                    classroom_number = None
                    classroom_id = None
                    territory = None

                    if classrooms:
                        for c in classrooms:
                            c_id = c['ID']
                            if hours >= 2:
                                if (self.classroom_schedule[c_id][day][lesson] is None and
                                        self.classroom_schedule[c_id][day][lesson + 1] is None):
                                    classroom = c
                                    classroom_id = c_id
                                    # Пробуем разные ключи для номера кабинета
                                    if 'Номер кабинета' in c:
                                        classroom_number = c['Номер кабинета']
                                    elif 'Кабинет' in c:
                                        classroom_number = c['Кабинет']
                                    else:
                                        classroom_number = str(c_id)

                                    # Пробуем разные ключи для территории
                                    if 'Территория' in c:
                                        territory = c['Территория']
                                    elif 'territory' in c:
                                        territory = c['territory']
                                    break
                            else:
                                if self.classroom_schedule[c_id][day][lesson] is None:
                                    classroom = c
                                    classroom_id = c_id
                                    if 'Номер кабинета' in c:
                                        classroom_number = c['Номер кабинета']
                                    elif 'Кабинет' in c:
                                        classroom_number = c['Кабинет']
                                    else:
                                        classroom_number = str(c_id)

                                    if 'Территория' in c:
                                        territory = c['Территория']
                                    elif 'territory' in c:
                                        territory = c['territory']
                                    break

                    # Размещаем урок(и)
                    if hours >= 2:
                        # Сдвоенный урок
                        for l in [lesson, lesson + 1]:
                            self.schedule[group_id][day][l] = {
                                'subject': subject_name,
                                'teacher': teacher['ФИО'],
                                'teacher_id': teacher_id,
                                'classroom': classroom_number,
                                'classroom_id': classroom_id,
                                'territory': territory,
                                'is_double': True
                            }
                            self.teacher_schedule[teacher_id][day][l] = group_id
                            if classroom_id:
                                self.classroom_schedule[classroom_id][day][l] = group_id

                        self.lessons_per_day[group_id][day] += 2
                        lessons_placed += 1
                        print(f"    ✓ {day} {lesson + 1}-{lesson + 2}: {subject_name} ({teacher['ФИО']})")
                    else:
                        # Одиночный урок
                        self.schedule[group_id][day][lesson] = {
                            'subject': subject_name,
                            'teacher': teacher['ФИО'],
                            'teacher_id': teacher_id,
                            'classroom': classroom_number,
                            'classroom_id': classroom_id,
                            'territory': territory,
                            'is_double': False
                        }
                        self.teacher_schedule[teacher_id][day][lesson] = group_id
                        if classroom_id:
                            self.classroom_schedule[classroom_id][day][lesson] = group_id

                        self.lessons_per_day[group_id][day] += 1
                        lessons_placed += 1
                        print(f"    ✓ {day} {lesson + 1}: {subject_name} ({teacher['ФИО']})")

                    placed = True
                    break

                if placed:
                    break

            if not placed:
                print(f"    ✗ Не удалось разместить {subject_name}")
                break

    def _place_subject_correctly(self, group_id: int, subject_name: str,
                                 subject_id: int, teacher: Dict,
                                 classrooms: List[Dict], hours: int,
                                 data: Dict[str, Any],
                                 teacher_territories: List[str]) -> bool:
        """
        Размещает предмет ПРАВИЛЬНО с учетом всех требований
        """
        teacher_id = teacher['ID'] if teacher else None
        teacher_days = self._get_teacher_available_days(teacher)

        # Инициализируем запись о четности для этого предмета
        if subject_id not in self.week_parity[group_id]:
            self.week_parity[group_id][subject_id] = {
                'hours': hours,
                'placed_hours': 0,
                'parity': None
            }

        hours_remaining = hours

        # Определяем, нужна ли четность недели
        # Если 1 час в нагрузке -> ставим 2 часа в расписании на одной неделе
        if hours == 1:
            # Ставим 2 часа на одной неделе
            weeks = random.choice(['верхняя', 'нижняя'])
            lesson_hours = 2
            print(f"    Предмет с 1 часом -> ставим 2 часа на {weeks} неделе")
        else:
            # 2+ часа -> ставим на обе недели, по half_hours часов на каждой
            weeks = 'обе'
            lesson_hours = hours // 2
            if hours % 2 != 0:
                lesson_hours += 1
            print(f"    Предмет с {hours} часами -> ставим по {lesson_hours} часов на каждой неделе")

        # Определяем, сколько уроков нужно поставить (каждый урок = 1 час в расписании)
        if hours == 1:
            lessons_needed = 2  # 2 урока на одной неделе
        else:
            lessons_needed = hours  # hours уроков, распределенных по двум неделям

        print(f"    Нужно поставить {lessons_needed} уроков")

        placed_lessons = 0
        placed_on_weeks = {'верхняя': 0, 'нижняя': 0}

        # Размещаем уроки
        while placed_lessons < lessons_needed:
            placed = False

            # Перебираем дни, начиная с тех, где меньше всего уроков
            days_with_lessons = [(day, self.lessons_per_day[group_id][day]) for day in self.DAYS]
            days_with_lessons.sort(key=lambda x: x[1])

            for day, current_lessons in days_with_lessons:
                # Проверяем, может ли преподаватель в этот день
                if teacher_days and day not in teacher_days:
                    continue

                # Проверяем лимит уроков (максимум 10 в день)
                if current_lessons >= self.MAX_LESSONS_PER_DAY:
                    continue

                # Проверяем, сколько еще уроков можно поставить в этот день
                available_slots = self.MAX_LESSONS_PER_DAY - current_lessons

                # Для предметов с 1 часом в нагрузке (2 урока в расписании)
                # ищем пару подряд идущих свободных уроков
                if hours == 1:
                    # Нужно поставить 2 урока подряд
                    for lesson in range(self.LESSONS_PER_DAY - 1):
                        # Проверяем, хватит ли места для двух уроков подряд
                        if lesson + 1 >= self.LESSONS_PER_DAY:
                            continue

                        # Проверяем, свободны ли оба урока
                        if (self.schedule[group_id][day][lesson] is not None or
                                self.schedule[group_id][day][lesson + 1] is not None):
                            continue

                        # Определяем территорию
                        territory = teacher_territories[0] if teacher_territories else None

                        # Проверяем перемещения для первого урока
                        if not self._can_place_with_movement(group_id, day, lesson, territory, data):
                            continue

                        # Проверяем преподавателя
                        if teacher_id:
                            if (self.teacher_schedule[teacher_id][day][lesson] is not None or
                                    self.teacher_schedule[teacher_id][day][lesson + 1] is not None):
                                continue

                        # Ищем кабинет, свободный на оба урока
                        classroom = None
                        classroom_id = None
                        classroom_number = None

                        if classrooms:
                            for c in classrooms:
                                c_id = c['ID']
                                if (self.classroom_schedule[c_id][day][lesson] is None and
                                        self.classroom_schedule[c_id][day][lesson + 1] is None):
                                    classroom = c
                                    classroom_id = c_id
                                    classroom_number = c.get('Номер кабинета') or c.get('Кабинет') or str(c_id)
                                    if not territory:
                                        territory = c.get('Территория')
                                    break

                            if not classroom:
                                continue

                        # Определяем, на какую неделю ставить
                        if weeks != 'обе':
                            week = weeks
                        else:
                            # Чередуем недели
                            if placed_on_weeks['верхняя'] < placed_on_weeks['нижняя']:
                                week = 'верхняя'
                            else:
                                week = 'нижняя'

                        # Размещаем два урока подряд
                        for l in [lesson, lesson + 1]:
                            self.schedule[group_id][day][l] = {
                                'subject': subject_name,
                                'subject_id': subject_id,
                                'teacher': teacher['ФИО'],
                                'teacher_id': teacher_id,
                                'classroom': classroom_number,
                                'classroom_id': classroom_id,
                                'territory': territory,
                                'is_stream': False,
                                'stream_id': None,
                                'week_parity': week,
                                'lesson_group': placed_lessons // 2
                            }

                            if teacher_id:
                                self.teacher_schedule[teacher_id][day][l] = group_id

                            if classroom_id:
                                self.classroom_schedule[classroom_id][day][l] = group_id

                        self.lessons_per_day[group_id][day] += 2
                        placed_on_weeks[week] += 2
                        placed_lessons += 2
                        placed = True
                        print(f"      ✅ Сдвоенный урок в {day} {lesson + 1}-{lesson + 2} ({teacher['ФИО']}, {week})")
                        break
                else:
                    # Для предметов с 2+ часами в нагрузке ставим обычные уроки
                    for lesson in range(self.LESSONS_PER_DAY):
                        if self.schedule[group_id][day][lesson] is not None:
                            continue

                        # Определяем территорию
                        territory = teacher_territories[0] if teacher_territories else None

                        # Проверяем перемещения
                        if not self._can_place_with_movement(group_id, day, lesson, territory, data):
                            continue

                        # Проверяем преподавателя
                        if teacher_id and self.teacher_schedule[teacher_id][day][lesson] is not None:
                            continue

                        # Ищем кабинет
                        classroom = None
                        classroom_id = None
                        classroom_number = None

                        if classrooms:
                            for c in classrooms:
                                c_id = c['ID']
                                if self.classroom_schedule[c_id][day][lesson] is None:
                                    classroom = c
                                    classroom_id = c_id
                                    classroom_number = c.get('Номер кабинета') or c.get('Кабинет') or str(c_id)
                                    if not territory:
                                        territory = c.get('Территория')
                                    break

                            if not classroom:
                                continue

                        # Определяем, на какую неделю ставить
                        if weeks != 'обе':
                            week = weeks
                        else:
                            # Чередуем недели
                            if placed_on_weeks['верхняя'] < placed_on_weeks['нижняя']:
                                week = 'верхняя'
                            else:
                                week = 'нижняя'

                        # Размещаем урок
                        self.schedule[group_id][day][lesson] = {
                            'subject': subject_name,
                            'subject_id': subject_id,
                            'teacher': teacher['ФИО'],
                            'teacher_id': teacher_id,
                            'classroom': classroom_number,
                            'classroom_id': classroom_id,
                            'territory': territory,
                            'is_stream': False,
                            'stream_id': None,
                            'week_parity': week,
                            'lesson_id': placed_lessons
                        }

                        if teacher_id:
                            self.teacher_schedule[teacher_id][day][lesson] = group_id

                        if classroom_id:
                            self.classroom_schedule[classroom_id][day][lesson] = group_id

                        self.lessons_per_day[group_id][day] += 1
                        placed_on_weeks[week] += 1
                        placed_lessons += 1
                        placed = True
                        print(f"      ✅ Урок в {day} {lesson + 1} ({teacher['ФИО']}, {week})")
                        break

                if placed:
                    break

            if not placed:
                print(f"    ❌ Не удалось разместить оставшиеся {lessons_needed - placed_lessons} уроков")
                return False

        return True

    def _place_subject_efficiently(self, group_id: int, subject_name: str,
                                   subject_id: int, teacher: Dict,
                                   classrooms: List[Dict], hours: int,
                                   parity: str, data: Dict[str, Any],
                                   teacher_territories: List[str]) -> bool:
        """
        Размещает предмет ЭФФЕКТИВНО
        """
        teacher_id = teacher['ID'] if teacher else None
        teacher_days = self._get_teacher_available_days(teacher)

        # Инициализируем запись о четности для этого предмета
        if subject_id not in self.week_parity[group_id]:
            self.week_parity[group_id][subject_id] = {
                'parity': parity,
                'placed_weeks': []
            }

        hours_remaining = hours

        # Определяем, сколько уроков нужно поставить
        if parity == 'обе':
            # Для предметов с 2+ часами ставим сдвоенные уроки
            lessons_needed = hours // 2
            if hours % 2 != 0:
                lessons_needed += 1
            print(f"    Нужно поставить {lessons_needed} сдвоенных уроков")
        else:
            lessons_needed = hours
            print(f"    Нужно поставить {lessons_needed} одиночных уроков")

        placed_lessons = 0

        # Размещаем уроки
        while hours_remaining > 0:
            placed = False

            # Перебираем дни, начиная с тех, где меньше всего уроков
            days_with_lessons = [(day, self.lessons_per_day[group_id][day]) for day in self.DAYS]
            days_with_lessons.sort(key=lambda x: x[1])

            for day, _ in days_with_lessons:
                # Проверяем, может ли преподаватель в этот день
                if teacher_days and day not in teacher_days:
                    continue

                # Проверяем лимит уроков
                if self.lessons_per_day[group_id][day] >= self.MAX_LESSONS_PER_DAY:
                    continue

                # Для сдвоенных уроков нужно больше места
                if parity == 'обе' and self.lessons_per_day[group_id][day] >= self.MAX_LESSONS_PER_DAY - 1:
                    continue

                # Ищем свободный урок
                for lesson in range(self.LESSONS_PER_DAY):
                    # Для сдвоенных уроков нужны два подряд
                    if parity == 'обе' and lesson + 1 >= self.LESSONS_PER_DAY:
                        continue

                    # Проверяем, свободен ли урок (уроки)
                    if parity == 'обе':
                        if (self.schedule[group_id][day][lesson] is not None or
                                self.schedule[group_id][day][lesson + 1] is not None):
                            continue
                    else:
                        if self.schedule[group_id][day][lesson] is not None:
                            continue

                    # Определяем территорию (приоритет у преподавателя)
                    territory = None
                    if teacher_territories:
                        territory = teacher_territories[0]

                    # Проверяем перемещения
                    if not self._can_place_with_movement(group_id, day, lesson, territory, data):
                        continue

                    # Проверяем преподавателя
                    if teacher_id:
                        if parity == 'обе':
                            if (self.teacher_schedule[teacher_id][day][lesson] is not None or
                                    self.teacher_schedule[teacher_id][day][lesson + 1] is not None):
                                continue
                        else:
                            if self.teacher_schedule[teacher_id][day][lesson] is not None:
                                continue

                    # Ищем кабинет
                    classroom = None
                    classroom_id = None
                    classroom_number = None

                    if classrooms:
                        for c in classrooms:
                            c_id = c['ID']
                            if parity == 'обе':
                                if (self.classroom_schedule[c_id][day][lesson] is None and
                                        self.classroom_schedule[c_id][day][lesson + 1] is None):
                                    classroom = c
                                    classroom_id = c_id
                                    classroom_number = c.get('Номер кабинета') or c.get('Кабинет') or str(c_id)
                                    if not territory:
                                        territory = c.get('Территория')
                                    break
                            else:
                                if self.classroom_schedule[c_id][day][lesson] is None:
                                    classroom = c
                                    classroom_id = c_id
                                    classroom_number = c.get('Номер кабинета') or c.get('Кабинет') or str(c_id)
                                    if not territory:
                                        territory = c.get('Территория')
                                    break

                        if not classroom:
                            continue

                    # Определяем неделю
                    available_weeks = ['верхняя', 'нижняя']
                    if self.week_parity[group_id][subject_id]['placed_weeks']:
                        available_weeks = [w for w in available_weeks
                                           if w not in self.week_parity[group_id][subject_id]['placed_weeks']]

                    if not available_weeks:
                        available_weeks = ['верхняя', 'нижняя']

                    week = random.choice(available_weeks)

                    # Размещаем урок(и)
                    if parity == 'обе':
                        # Сдвоенный урок
                        for l in [lesson, lesson + 1]:
                            self.schedule[group_id][day][l] = {
                                'subject': subject_name,
                                'subject_id': subject_id,
                                'teacher': teacher['ФИО'],
                                'teacher_id': teacher_id,
                                'classroom': classroom_number,
                                'classroom_id': classroom_id,
                                'territory': territory,
                                'is_stream': False,
                                'stream_id': None,
                                'week_parity': week,
                                'weeks': [week]
                            }

                            if teacher_id:
                                self.teacher_schedule[teacher_id][day][l] = group_id

                            if classroom_id:
                                self.classroom_schedule[classroom_id][day][l] = group_id

                        self.lessons_per_day[group_id][day] += 2
                        self.week_parity[group_id][subject_id]['placed_weeks'].append(week)
                        hours_remaining -= 2
                        placed_lessons += 1
                        print(f"      ✅ Сдвоенный урок в {day} {lesson + 1}-{lesson + 2} ({teacher['ФИО']})")
                    else:
                        # Одиночный урок
                        self.schedule[group_id][day][lesson] = {
                            'subject': subject_name,
                            'subject_id': subject_id,
                            'teacher': teacher['ФИО'],
                            'teacher_id': teacher_id,
                            'classroom': classroom_number,
                            'classroom_id': classroom_id,
                            'territory': territory,
                            'is_stream': False,
                            'stream_id': None,
                            'week_parity': week,
                            'weeks': [week]
                        }

                        if teacher_id:
                            self.teacher_schedule[teacher_id][day][lesson] = group_id

                        if classroom_id:
                            self.classroom_schedule[classroom_id][day][lesson] = group_id

                        self.lessons_per_day[group_id][day] += 1
                        self.week_parity[group_id][subject_id]['placed_weeks'].append(week)
                        hours_remaining -= 1
                        placed_lessons += 1
                        print(f"      ✅ Одиночный урок в {day} {lesson + 1} ({teacher['ФИО']})")

                    placed = True
                    break

                if placed:
                    break

            if not placed:
                print(f"    ❌ Не удалось разместить оставшиеся {hours_remaining} часов для {subject_name}")
                return False

        return True

    def _place_subject_for_group(self, group_id: int, subject_name: str,
                                 teacher: Dict, classrooms: List[Dict],
                                 hours: int, parity: str,
                                 data: Dict[str, Any]):
        """
        Размещает предмет для одной группы
        """
        teacher_id = teacher['ID'] if teacher else None
        teacher_days = self._get_teacher_available_days(teacher)

        # Пытаемся разместить все часы
        hours_remaining = hours

        while hours_remaining > 0:
            placed = False

            # Перемешиваем дни для случайности
            days = self.DAYS.copy()
            random.shuffle(days)

            for day in days:
                # Проверяем, может ли преподаватель в этот день
                if teacher_days and day not in teacher_days:
                    continue

                for lesson in range(self.LESSONS_PER_DAY - 1):
                    # Проверяем, свободен ли урок у группы
                    if self.schedule[group_id][day][lesson] is not None:
                        continue

                    # Проверяем, свободен ли преподаватель
                    if teacher_id and self.teacher_schedule[teacher_id][day][lesson] is not None:
                        continue

                    # Проверяем, свободен ли кабинет
                    classroom = None
                    classroom_id = None
                    if classrooms:
                        # Ищем свободный кабинет
                        for c in classrooms:
                            c_id = c['ID']
                            if self.classroom_schedule[c_id][day][lesson] is None:
                                classroom = c
                                classroom_id = c_id
                                break

                        if not classroom:
                            continue

                    # Размещаем предмет
                    self.schedule[group_id][day][lesson] = {
                        'subject': subject_name,
                        'teacher': teacher['ФИО'] if teacher else None,
                        'teacher_id': teacher_id,
                        'classroom': classroom['Номер кабинета'] if classroom else None,
                        'classroom_id': classroom_id,
                        'territory': classroom['Территория'] if classroom else None,
                        'is_stream': False,
                        'stream_id': None,
                        'week_parity': parity
                    }

                    # Отмечаем занятость преподавателя
                    if teacher_id:
                        self.teacher_schedule[teacher_id][day][lesson] = group_id

                    # Отмечаем занятость кабинета
                    if classroom_id:
                        self.classroom_schedule[classroom_id][day][lesson] = group_id

                    hours_remaining -= 2 if parity == 'обе' else 1
                    placed = True

                    # Если предмет на обе недели, ставим сдвоенный урок
                    if parity == 'обе' and lesson + 1 < self.LESSONS_PER_DAY:
                        if (self.schedule[group_id][day][lesson + 1] is None and
                                (not teacher_id or self.teacher_schedule[teacher_id][day][lesson + 1] is None)):

                            self.schedule[group_id][day][lesson + 1] = {
                                'subject': subject_name,
                                'teacher': teacher['ФИО'] if teacher else None,
                                'teacher_id': teacher_id,
                                'classroom': classroom['Номер кабинета'] if classroom else None,
                                'classroom_id': classroom_id,
                                'territory': classroom['Территория'] if classroom else None,
                                'is_stream': False,
                                'stream_id': None,
                                'week_parity': parity
                            }

                            if teacher_id:
                                self.teacher_schedule[teacher_id][day][lesson + 1] = group_id

                            if classroom_id:
                                self.classroom_schedule[classroom_id][day][lesson + 1] = group_id

                    break

                if placed:
                    break

            if not placed:
                # Если не смогли разместить, пробуем другой день
                print(f"Предупреждение: не удалось разместить {subject_name} для группы {group_id}")

    def _is_already_placed_in_stream(self, group_id: int, subject_id: int, data: Dict[str, Any]) -> bool:
        """
        Проверяет, не был ли уже предмет размещен в потоке
        """
        for stream in data['streams']:
            stream_id = stream['ID']
            subject_ids = stream.get('Дисциплины_ID', [])

            if subject_id in subject_ids:
                group_ids = []
                if stream.get('Группа1_ID') == group_id:
                    return True
                if stream.get('Группа2_ID') == group_id:
                    return True
                if stream.get('Группа3_ID') == group_id:
                    return True
                if stream.get('Группа4_ID') == group_id:
                    return True

        return False

    def _get_teacher_available_days(self, teacher: Dict) -> List[str]:
        """Получает доступные дни преподавателя"""
        days_str = teacher.get('Дни занятий', '')
        if not days_str or days_str == 'Любые':
            return self.DAYS.copy()

        day_mapping = {'Пн': 'пн', 'Вт': 'вт', 'Ср': 'ср', 'Чт': 'чт', 'Пт': 'пт', 'Сб': 'сб'}
        available = []
        for d in days_str.split(','):
            d = d.strip()
            if d in day_mapping:
                available.append(day_mapping[d])

        return available if available else self.DAYS.copy()

    def _format_group_name(self, group: Dict) -> str:
        """
        Форматирует название группы
        """
        name = group['Группа']
        subgroup = group.get('Подгруппа', '')

        if subgroup and subgroup != 'Нет' and subgroup != 'None':
            return f"{name} ({subgroup})"
        return name

    def _validate_and_adjust(self):
        """
        Проверяет и корректирует расписание
        """
        # Проверка на максимальное количество уроков в день
        for group_id, group_schedule in self.schedule.items():
            for day, lessons in group_schedule.items():
                lesson_count = sum(1 for l in lessons if l is not None)
                if lesson_count > self.MAX_LESSONS_PER_DAY:
                    print(f"Группа {group_id} в день {day} имеет {lesson_count} уроков")

        # TODO: Добавить другие проверки

    def _generate_excel(self, output_path: str, data: Dict[str, Any]) -> str:
        """
        Генерирует Excel файл с расписанием
        """
        # Сначала создаем шаблон с группами
        template_path = self.template_generator.generate_template_with_groups(
            output_path.replace('.xlsx', '_template.xlsx')
        )

        # Получаем структуру групп
        group_structure = self.template_generator._build_group_structure(data['active_groups'])

        # Заполняем шаблон данными
        filler = ExcelFiller(self.db_ops)

        filled_path = filler.fill_schedule(
            template_path,
            self.schedule,
            group_structure,
            self.group_names,
            output_path
        )

        # Удаляем временный шаблон
        if os.path.exists(template_path) and template_path != output_path:
            os.remove(template_path)

        return filled_path

    def _get_group_info(self, group_id: int, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Возвращает название группы и подгруппу по ID
        """
        for group in data['active_groups']:
            if group['ID'] == group_id:
                return group['Группа'], group.get('Подгруппа', 'Нет')
        return f"Группа {group_id}", 'Нет'
