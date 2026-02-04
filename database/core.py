import sqlite3
from typing import List, Dict, Any
from contextlib import contextmanager


class Database:
    def __init__(self, db_name: str = "schedule.db"):
        self.db_name = db_name
        self.init_db()

    @contextmanager
    def _get_cursor(self):
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Ошибка SQLite: {e}")
            raise
        finally:
            conn.close()

    def init_db(self):
        with self._get_cursor() as cursor:
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS Модули (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Код TEXT NOT NULL UNIQUE,
                Название TEXT NOT NULL
            );
    
            CREATE TABLE IF NOT EXISTS Группы (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Группа TEXT NOT NULL,
                Подгруппа TEXT NOT NULL DEFAULT 'Нет',
                Самообразование TEXT,
                [Разговоры о важном] BOOLEAN DEFAULT 0
            );
    
            CREATE TABLE IF NOT EXISTS Территории (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Территория TEXT NOT NULL,
                Цвет TEXT DEFAULT '#FFFFFF'
            );
        
            CREATE TABLE IF NOT EXISTS Кабинеты (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Кабинет TEXT NOT NULL,
                ТерриторияID INTEGER NOT NULL,
                Вместимость INTEGER,
                FOREIGN KEY (ТерриторияID) REFERENCES Территории(ID) ON DELETE CASCADE
            );
    
            CREATE TABLE IF NOT EXISTS Дисциплины (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Дисциплина TEXT NOT NULL,
                Модуль TEXT NOT NULL,
                FOREIGN KEY (Модуль) REFERENCES Модули(Код)
            );
        
            CREATE TABLE IF NOT EXISTS Преподаватели (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ФИО TEXT NOT NULL,
                Совместитель BOOLEAN DEFAULT 0,
                [Дни занятий] TEXT
            );
    
            CREATE TABLE IF NOT EXISTS Преподаватель_Территория (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ПреподавательID INTEGER NOT NULL,
                ТерриторияID INTEGER NOT NULL,
                FOREIGN KEY (ПреподавательID) REFERENCES Преподаватели(ID),
                FOREIGN KEY (ТерриторияID) REFERENCES Территории(ID)
            );
        
            CREATE TABLE IF NOT EXISTS Преподаватель_Дисциплина (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ПреподавательID INTEGER NOT NULL,
                ДисциплинаID INTEGER NOT NULL,
                FOREIGN KEY (ПреподавательID) REFERENCES Преподаватели(ID),
                FOREIGN KEY (ДисциплинаID) REFERENCES Дисциплины(ID)
            );
        
            CREATE TABLE IF NOT EXISTS Дисциплина_Кабинет (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ДисциплинаID INTEGER NOT NULL,
                КабинетID INTEGER NOT NULL,
                FOREIGN KEY (ДисциплинаID) REFERENCES Дисциплины(ID) ON DELETE CASCADE,
                FOREIGN KEY (КабинетID) REFERENCES Кабинеты(ID) ON DELETE CASCADE
            );
        
            CREATE TABLE IF NOT EXISTS Нагрузка (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ПреподавательID INTEGER NOT NULL,
                ДисциплинаID INTEGER NOT NULL,
                ГруппаID INTEGER NOT NULL,
                Часы INTEGER NOT NULL,
                FOREIGN KEY (ПреподавательID) REFERENCES Преподаватели(ID),
                FOREIGN KEY (ДисциплинаID) REFERENCES Дисциплины(ID),
                FOREIGN KEY (ГруппаID) REFERENCES Группы(ID)
            );
            """)

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_command(self, query: str, params: tuple = ()) -> bool:
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, params)
            return True
        except sqlite3.Error as e:
            print(f"Ошибка выполнения команды: {e}")
            return False
