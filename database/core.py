import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path


class Database:
    def __init__(self, db_name: str = "schedule.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Модули (
            Код TEXT PRIMARY KEY,
            Название TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Группы (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Название TEXT NOT NULL,
            Самообразование TEXT,
            [Разговоры о важном] BOOLEAN DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS Подгруппы (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ГруппаID INTEGER NOT NULL,
            Название TEXT NOT NULL,
            FOREIGN KEY (ГруппаID) REFERENCES Группы(ID)
        );

        CREATE TABLE IF NOT EXISTS Потоки (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Название TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS СоставПотока (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ПотокID INTEGER NOT NULL,
            ПодгруппаID INTEGER NOT NULL,
            FOREIGN KEY (ПотокID) REFERENCES Потоки(ID),
            FOREIGN KEY (ПодгруппаID) REFERENCES Подгруппы(ID)
        );

        CREATE TABLE IF NOT EXISTS Территории (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Название TEXT NOT NULL,
            Цвет TEXT
        );

        CREATE TABLE IF NOT EXISTS Кабинеты (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Номер TEXT NOT NULL,
            ТерриторияID INTEGER NOT NULL,
            Вместимость INTEGER,
            FOREIGN KEY (ТерриторияID) REFERENCES Территории(ID)
        );

        CREATE TABLE IF NOT EXISTS Предметы (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Название TEXT NOT NULL,
            МодульКод TEXT NOT NULL,
            FOREIGN KEY (МодульКод) REFERENCES Модули(Код)
        );

        CREATE TABLE IF NOT EXISTS Преподаватели (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ФИО TEXT NOT NULL,
            Нагрузка INTEGER,
            Дни TEXT,
            Уроки INTEGER
        );

        CREATE TABLE IF NOT EXISTS Преподаватель_Территория (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ПреподавательID INTEGER NOT NULL,
            ТерриторияID INTEGER NOT NULL,
            FOREIGN KEY (ПреподавательID) REFERENCES Преподаватели(ID),
            FOREIGN KEY (ТерриторияID) REFERENCES Территории(ID)
        );

        CREATE TABLE IF NOT EXISTS Преподаватель_Предмет (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ПреподавательID INTEGER NOT NULL,
            ПредметID INTEGER NOT NULL,
            FOREIGN KEY (ПреподавательID) REFERENCES Преподаватели(ID),
            FOREIGN KEY (ПредметID) REFERENCES Предметы(ID)
        );

        CREATE TABLE IF NOT EXISTS Предмет_Кабинет (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ПредметID INTEGER NOT NULL,
            КабинетID INTEGER NOT NULL,
            FOREIGN KEY (ПредметID) REFERENCES Предметы(ID),
            FOREIGN KEY (КабинетID) REFERENCES Кабинеты(ID)
        );

        CREATE TABLE IF NOT EXISTS Нагрузка (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ПреподавательID INTEGER NOT NULL,
            ПредметID INTEGER NOT NULL,
            ПодгруппаID INTEGER,
            ПотокID INTEGER,
            Часы INTEGER NOT NULL,
            FOREIGN KEY (ПреподавательID) REFERENCES Преподаватели(ID),
            FOREIGN KEY (ПредметID) REFERENCES Предметы(ID),
            FOREIGN KEY (ПодгруппаID) REFERENCES Подгруппы(ID),
            FOREIGN KEY (ПотокID) REFERENCES Потоки(ID)
        );
        """)

        conn.commit()
        conn.close()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []
        finally:
            conn.close()

    def execute_command(self, query: str, params: tuple = ()) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка выполнения команды: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
