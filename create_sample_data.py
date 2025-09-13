import sqlite3


def create_sample_data(db_name="schedule.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Добавляем тестовые данные
    cursor.executescript("""
    INSERT OR IGNORE INTO Группы (Название) VALUES 
    ('1 Ан/9'), ('2 Ан/9'), ('3 Ан/9'), ('4 Ан/9'), ('1 Ан/11');

    INSERT OR IGNORE INTO Преподаватели (ФИО) VALUES 
    ('Власова'), ('Ермолова'), ('Аксютина'), ('Иванов'), ('Кашорик');

    INSERT OR IGNORE INTO Территории (Название, Цвет) VALUES 
    ('ул. Радио', '#FFCCCC'), ('1-й Амбулаторный проезд', '#CCFFCC');

    INSERT OR IGNORE INTO Кабинеты (Номер, ТерриторияID, Вместимость) VALUES 
    ('403', 1, 25), ('405', 1, 30), ('205', 1, 20), ('302', 1, 15);

    INSERT OR IGNORE INTO ТипПредмета (Название) VALUES 
    ('Общеобразовательный'), ('Специальный'), ('Практический');

    INSERT OR IGNORE INTO Предметы (Название, ТипID, Модуль, Количество) VALUES 
    ('Математика', 1, '1 семестр', 72),
    ('Рис.с осн.перспект', 2, '1 семестр', 48),
    ('Литература', 1, '1 семестр', 68);
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_sample_data()
