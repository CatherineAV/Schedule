from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Group:
    id: Optional[int] = None
    name: str = ""
    self_education: Optional[str] = None
    important_talks: bool = False


@dataclass
class Subgroup:
    id: Optional[int] = None
    group_id: int = 0
    name: str = ""


@dataclass
class Teacher:
    id: Optional[int] = None
    full_name: str = ""
    is_part_timer: bool = False
    work_days: Optional[str] = None


@dataclass
class Subject:
    id: Optional[int] = None
    name: str = ""
    module_code: str = ""


@dataclass
class Territory:
    id: Optional[int] = None
    name: str = ""
    color: Optional[str] = None


@dataclass
class Classroom:
    id: Optional[int] = None
    number: str = ""
    territory_id: int = 0
    capacity: Optional[int] = None


@dataclass
class Module:
    code: str = ""
    name: str = ""


@dataclass
class Stream:
    id: Optional[int] = None
    name: str = ""


@dataclass
class GroupWithSubgroups:
    group: Group
    subgroups: List[Subgroup]

    def to_dict(self):
        return {
            "Название": self.group.name,
            "Подгруппа": ", ".join([s.name for s in self.subgroups]) if self.subgroups else "Нет",
            "Самообразование": self.group.self_education or "Нет",
            "Разговоры о важном": "Да" if self.group.important_talks else "Нет"
        }