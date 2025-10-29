import sqlite3
from datetime import datetime
import os


class DatabaseManager:
    """Класс для управления базой данных кондитерской"""

    def __init__(self, db_name="confectionery.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """Создание подключения к базе данных"""
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Таблица клиентов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    birth_date TEXT,
                    email TEXT
                )
            ''')

            # Таблица десертов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS desserts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    price_per_kg REAL,
                    price_per_unit REAL,
                    composition TEXT
                )
            ''')

            # Таблица заказов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    dessert_types TEXT,
                    order_date TEXT,
                    order_time TEXT,
                    delivery_type TEXT,
                    photo_path TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')

            # Проверяем, есть ли уже данные в таблицах
            cursor.execute("SELECT COUNT(*) FROM clients")
            clients_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM desserts")
            desserts_count = cursor.fetchone()[0]

            # Добавляем тестовые данные только если таблицы пустые
            if clients_count == 0 and desserts_count == 0:
                self._add_sample_data(cursor)

            conn.commit()

    def _add_sample_data(self, cursor):
        """Добавление тестовых данных только один раз при первом запуске"""
        print("Добавление тестовых данных...")

        # Тестовые клиенты
        clients = [
            ('Иванов Иван Иванович', '+79161234567', '1990-05-15', 'ivanov@mail.ru'),
            ('Петрова Мария Сергеевна', '+79167654321', '1985-12-20', 'petrova@gmail.com'),
            ('Сидоров Алексей Петрович', '+79031112233', '1992-08-03', 'sidorov@yandex.ru')
        ]

        cursor.executemany('''
            INSERT INTO clients (full_name, phone, birth_date, email)
            VALUES (?, ?, ?, ?)
        ''', clients)

        # Тестовые десерты
        desserts = [
            ('Торт "Наполеон"', 1200.0, None, 'мука, масло, яйца, молоко, сахар'),
            ('Торт "Медовик"', 1100.0, None, 'мука, мед, яйца, сметана, сахар'),
            ('Эклеры', None, 150.0, 'заварной крем, тесто, глазурь'),
            ('Макаруны', None, 80.0, 'миндальная мука, сахар, яичный белок, начинка'),
            ('Чизкейк Нью-Йорк', 1400.0, None, 'творожный сыр, печенье, сливки, яйца')
        ]

        cursor.executemany('''
            INSERT INTO desserts (name, price_per_kg, price_per_unit, composition)
            VALUES (?, ?, ?, ?)
        ''', desserts)

        # Получаем ID добавленных клиентов и десертов
        cursor.execute("SELECT id FROM clients")
        client_ids = [row[0] for row in cursor.fetchall()]

        # Тестовые заказы (только 2 заказа)
        orders = [
            (client_ids[0], 'Торт "Наполеон",Эклеры', '2024-01-15', '14:30', 'Доставка', ''),
            (client_ids[1], 'Макаруны,Чизкейк Нью-Йорк', '2024-01-16', '10:00', 'Самовывоз', '')
        ]

        cursor.executemany('''
            INSERT INTO orders (client_id, dessert_types, order_date, order_time, delivery_type, photo_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', orders)

        print("Тестовые данные успешно добавлены!")

    def clear_test_data(self):
        """Очистка всех тестовых данных (для отладки)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM desserts")
            cursor.execute("DELETE FROM clients")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('clients', 'desserts', 'orders')")
            conn.commit()
        print("Все тестовые данные очищены!")

    def get_table_counts(self):
        """Получение количества записей в таблицах (для отладки)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clients")
            clients_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM desserts")
            desserts_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM orders")
            orders_count = cursor.fetchone()[0]

            return {
                'clients': clients_count,
                'desserts': desserts_count,
                'orders': orders_count
            }

    # Методы для работы с клиентами
    def get_all_clients(self):
        """Получение всех клиентов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clients ORDER BY full_name')
            return cursor.fetchall()

    def add_client(self, full_name, phone, birth_date, email):
        """Добавление нового клиента"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clients (full_name, phone, birth_date, email)
                VALUES (?, ?, ?, ?)
            ''', (full_name, phone, birth_date, email))
            return cursor.lastrowid

    def update_client(self, client_id, full_name, phone, birth_date, email):
        """Обновление данных клиента"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE clients 
                SET full_name=?, phone=?, birth_date=?, email=?
                WHERE id=?
            ''', (full_name, phone, birth_date, email, client_id))

    def delete_client(self, client_id):
        """Удаление клиента"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clients WHERE id=?', (client_id,))

    # Методы для работы с десертами
    def get_all_desserts(self):
        """Получение всех десертов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM desserts ORDER BY name')
            return cursor.fetchall()

    def add_dessert(self, name, price_per_kg, price_per_unit, composition):
        """Добавление нового десерта"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO desserts (name, price_per_kg, price_per_unit, composition)
                VALUES (?, ?, ?, ?)
            ''', (name, price_per_kg, price_per_unit, composition))
            return cursor.lastrowid

    def update_dessert(self, dessert_id, name, price_per_kg, price_per_unit, composition):
        """Обновление данных десерта"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE desserts 
                SET name=?, price_per_kg=?, price_per_unit=?, composition=?
                WHERE id=?
            ''', (name, price_per_kg, price_per_unit, composition, dessert_id))

    def delete_dessert(self, dessert_id):
        """Удаление десерта"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM desserts WHERE id=?', (dessert_id,))

    # Методы для работы с заказами
    def get_all_orders(self):
        """Получение всех заказов с информацией о клиентах"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, c.full_name, c.phone, o.dessert_types, o.order_date, 
                       o.order_time, o.delivery_type, o.photo_path
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                ORDER BY o.order_date DESC, o.order_time DESC
            ''')
            return cursor.fetchall()

    def add_order(self, client_id, dessert_types, order_date, order_time, delivery_type, photo_path):
        """Добавление нового заказа"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orders (client_id, dessert_types, order_date, order_time, delivery_type, photo_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (client_id, dessert_types, order_date, order_time, delivery_type, photo_path))
            return cursor.lastrowid

    def delete_order(self, order_id):
        """Удаление заказа"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM orders WHERE id=?', (order_id,))