import sqlite3
import datetime
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from tkinter import font as tkfont
import csv
import os
import qr_generator  # наш модуль для QR-кода

# ====================== КЛАСС ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ ======================
class DatabaseManager:
    """Класс для управления базой данных SQLite"""
    
    def __init__(self, db_name="autoservice.db"):
        self.db_name = db_name
        self.connection = None
        self.create_database()
        self.import_initial_data()
    
    def get_connection(self):
        """Получение соединения с БД"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None):
        """Выполнение запроса с возвратом результатов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor
    
    def fetch_all(self, query, params=None):
        """Получение всех записей"""
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        """Получение одной записи"""
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def hash_password(self, password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_database(self):
        """Создание структуры базы данных"""
        
        # Таблица пользователей
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS Пользователи (
                ID_пользователя INTEGER PRIMARY KEY AUTOINCREMENT,
                ФИО TEXT NOT NULL,
                Телефон TEXT NOT NULL,
                Логин TEXT UNIQUE NOT NULL,
                Пароль TEXT NOT NULL,
                Роль TEXT NOT NULL CHECK(Роль IN ('Менеджер', 'Автомеханик', 'Оператор', 'Заказчик', 'Менеджер по качеству'))
            )
        """)
        
        # Таблица заявок
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS Заявки (
                ID_заявки INTEGER PRIMARY KEY AUTOINCREMENT,
                Дата_создания DATE NOT NULL,
                Тип_авто TEXT NOT NULL,
                Модель_авто TEXT NOT NULL,
                Описание_проблемы TEXT,
                Статус TEXT NOT NULL CHECK(Статус IN ('Новая заявка', 'В процессе ремонта', 'Ожидание запчастей', 'Готова к выдаче', 'Завершена')),
                Дата_завершения DATE,
                Запчасти TEXT,
                ID_клиента INTEGER NOT NULL,
                ID_механика INTEGER,
                FOREIGN KEY (ID_клиента) REFERENCES Пользователи(ID_пользователя) ON DELETE RESTRICT,
                FOREIGN KEY (ID_механика) REFERENCES Пользователи(ID_пользователя) ON DELETE SET NULL
            )
        """)
        
        # Таблица комментариев
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS Комментарии (
                ID_комментария INTEGER PRIMARY KEY AUTOINCREMENT,
                Сообщение TEXT NOT NULL,
                Дата_создания TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ID_механика INTEGER NOT NULL,
                ID_заявки INTEGER NOT NULL,
                FOREIGN KEY (ID_механика) REFERENCES Пользователи(ID_пользователя) ON DELETE RESTRICT,
                FOREIGN KEY (ID_заявки) REFERENCES Заявки(ID_заявки) ON DELETE CASCADE
            )
        """)
        
        # Таблица оценки качества
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS Оценка_качества (
                ID_оценки INTEGER PRIMARY KEY AUTOINCREMENT,
                Оценка INTEGER CHECK(Оценка >= 1 AND Оценка <= 5),
                Отзыв TEXT,
                Дата_оценки DATE DEFAULT CURRENT_DATE,
                ID_заявки INTEGER UNIQUE NOT NULL,
                FOREIGN KEY (ID_заявки) REFERENCES Заявки(ID_заявки) ON DELETE CASCADE
            )
        """)
        
        # Индексы для ускорения
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_заявки_статус ON Заявки(Статус)")
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_заявки_механик ON Заявки(ID_механика)")
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_заявки_клиент ON Заявки(ID_клиента)")
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_комментарии_заявка ON Комментарии(ID_заявки)")
    
    def import_initial_data(self):
        """Импорт начальных данных"""
        
        # Проверяем, есть ли уже данные
        result = self.fetch_one("SELECT COUNT(*) as count FROM Пользователи")
        if result and result['count'] > 0:
            return  # Данные уже есть
        
        # Импорт пользователей
        users_data = [
            (1, 'Белов Александр Давидович', '89210563128', 'login1', self.hash_password('pass1'), 'Менеджер'),
            (2, 'Харитонова Мария Павловна', '89535078985', 'login2', self.hash_password('pass2'), 'Автомеханик'),
            (3, 'Марков Давид Иванович', '89210673849', 'login3', self.hash_password('pass3'), 'Автомеханик'),
            (4, 'Громова Анна Семёновна', '89990563748', 'login4', self.hash_password('pass4'), 'Оператор'),
            (5, 'Карташова Мария Данииловна', '89994563847', 'login5', self.hash_password('pass5'), 'Оператор'),
            (6, 'Касаткин Егор Львович', '89219567849', 'login11', self.hash_password('pass11'), 'Заказчик'),
            (7, 'Ильина Тамара Даниловна', '89219567841', 'login12', self.hash_password('pass12'), 'Заказчик'),
            (8, 'Елисеева Юлиана Алексеевна', '89219567842', 'login13', self.hash_password('pass13'), 'Заказчик'),
            (9, 'Никифорова Алиса Тимофеевна', '89219567843', 'login14', self.hash_password('pass14'), 'Заказчик'),
            (10, 'Васильев Али Евгеньевич', '89219567844', 'login15', self.hash_password('pass15'), 'Автомеханик')
        ]
        
        for user in users_data:
            try:
                self.execute_query(
                    "INSERT INTO Пользователи (ID_пользователя, ФИО, Телефон, Логин, Пароль, Роль) VALUES (?, ?, ?, ?, ?, ?)",
                    user
                )
            except:
                pass
        
        # Импорт заявок
        requests_data = [
            (1, '2023-06-06', 'Легковая', 'Hyundai Avante (CN7)', 'Отказали тормоза.', 'В процессе ремонта', None, '', 2, 7),
            (2, '2023-05-05', 'Легковая', 'Nissan 180SX', 'Отказали тормоза.', 'В процессе ремонта', None, '', 3, 8),
            (3, '2022-07-07', 'Легковая', 'Toyota 2000GT', 'В салоне пахнет бензином.', 'Готова к выдаче', '2023-01-01', '', 3, 9),
            (4, '2023-08-02', 'Грузовая', 'Citroen Berlingo (B9)', 'Руль плохо крутится.', 'Новая заявка', None, '', None, 8),
            (5, '2023-08-02', 'Грузовая', 'УАЗ 2360', 'Руль плохо крутится.', 'Новая заявка', None, '', None, 9)
        ]
        
        for req in requests_data:
            try:
                self.execute_query(
                    "INSERT INTO Заявки (ID_заявки, Дата_создания, Тип_авто, Модель_авто, Описание_проблемы, Статус, Дата_завершения, Запчасти, ID_механика, ID_клиента) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    req
                )
            except:
                pass
        
        # Импорт комментариев
        comments_data = [
            (1, 'Очень странно.', 2, 1),
            (2, 'Будем разбираться!', 3, 2),
            (3, 'Будем разбираться!', 3, 3)
        ]
        
        for comm in comments_data:
            try:
                self.execute_query(
                    "INSERT INTO Комментарии (ID_комментария, Сообщение, ID_механика, ID_заявки) VALUES (?, ?, ?, ?)",
                    comm
                )
            except:
                pass
    
    # ====================== ЗАПРОСЫ ДЛЯ ОТЧЕТОВ ======================
    
    def get_completed_requests_count(self):
        """Количество выполненных заявок"""
        result = self.fetch_one("SELECT COUNT(*) as count FROM Заявки WHERE Статус = 'Готова к выдаче'")
        return result['count'] if result else 0
    
    def get_average_completion_time(self):
        """Среднее время выполнения заявки в днях"""
        result = self.fetch_one("""
            SELECT AVG(julianday(Дата_завершения) - julianday(Дата_создания)) as avg_days
            FROM Заявки 
            WHERE Статус = 'Готова к выдаче' AND Дата_завершения IS NOT NULL
        """)
        return round(result['avg_days'], 1) if result and result['avg_days'] else 0
    
    def get_statistics_by_problem_type(self):
        """Статистика по типам неисправностей"""
        return self.fetch_all("""
            SELECT 
                CASE 
                    WHEN Описание_проблемы LIKE '%тормоз%' THEN 'Проблемы с тормозами'
                    WHEN Описание_проблемы LIKE '%руль%' THEN 'Проблемы с рулевым управлением'
                    WHEN Описание_проблемы LIKE '%бензин%' THEN 'Проблемы с топливной системой'
                    ELSE 'Прочие неисправности'
                END as Тип_неисправности,
                COUNT(*) as Количество
            FROM Заявки
            GROUP BY Тип_неисправности
            ORDER BY Количество DESC
        """)
    
    def get_requests_by_master(self, master_id):
        """Заявки конкретного механика"""
        return self.fetch_all("""
            SELECT 
                r.ID_заявки,
                r.Дата_создания,
                r.Модель_авто,
                r.Статус,
                u.ФИО as Клиент
            FROM Заявки r
            JOIN Пользователи u ON r.ID_клиента = u.ID_пользователя
            WHERE r.ID_механика = ?
            ORDER BY r.Дата_создания DESC
        """, (master_id,))
    
    def authenticate_user(self, login, password):
        """Аутентификация пользователя"""
        hashed_password = self.hash_password(password)
        result = self.fetch_one(
            "SELECT ID_пользователя, ФИО, Роль FROM Пользователи WHERE Логин = ? AND Пароль = ?",
            (login, hashed_password)
        )
        return result
    
    def get_all_requests(self):
        """Получение всех заявок"""
        return self.fetch_all("""
            SELECT 
                r.ID_заявки,
                r.Дата_создания,
                r.Тип_авто,
                r.Модель_авто,
                r.Описание_проблемы,
                r.Статус,
                r.Дата_завершения,
                r.Запчасти,
                u1.ФИО as Клиент,
                u2.ФИО as Механик
            FROM Заявки r
            LEFT JOIN Пользователи u1 ON r.ID_клиента = u1.ID_пользователя
            LEFT JOIN Пользователи u2 ON r.ID_механика = u2.ID_пользователя
            ORDER BY r.Дата_создания DESC
        """)
    
    def get_all_masters(self):
        """Получение всех автомехаников"""
        return self.fetch_all(
            "SELECT ID_пользователя, ФИО FROM Пользователи WHERE Роль = 'Автомеханик'"
        )
    
    def get_all_clients(self):
        """Получение всех клиентов (заказчиков)"""
        return self.fetch_all(
            "SELECT ID_пользователя, ФИО FROM Пользователи WHERE Роль = 'Заказчик'"
        )
    
    def update_request_status(self, request_id, new_status, master_id=None):
        """Обновление статуса заявки"""
        if new_status == 'Готова к выдаче' or new_status == 'Завершена':
            today = datetime.date.today().isoformat()
            self.execute_query(
                "UPDATE Заявки SET Статус = ?, Дата_завершения = ? WHERE ID_заявки = ?",
                (new_status, today, request_id)
            )
        else:
            self.execute_query(
                "UPDATE Заявки SET Статус = ? WHERE ID_заявки = ?",
                (new_status, request_id)
            )
    
    def assign_master(self, request_id, master_id):
        """Назначение механика на заявку"""
        self.execute_query(
            "UPDATE Заявки SET ID_механика = ? WHERE ID_заявки = ?",
            (master_id, request_id)
        )
    
    def add_comment(self, request_id, master_id, message):
        """Добавление комментария"""
        self.execute_query(
            "INSERT INTO Комментарии (Сообщение, ID_механика, ID_заявки) VALUES (?, ?, ?)",
            (message, master_id, request_id)
        )
    
    def get_comments_for_request(self, request_id):
        """Получение комментариев для заявки"""
        return self.fetch_all("""
            SELECT 
                c.Сообщение,
                c.Дата_создания,
                u.ФИО as Автор
            FROM Комментарии c
            JOIN Пользователи u ON c.ID_механика = u.ID_пользователя
            WHERE c.ID_заявки = ?
            ORDER BY c.Дата_создания DESC
        """, (request_id,))
    
    def backup_database(self, backup_path):
        """Резервное копирование базы данных"""
        try:
            import shutil
            shutil.copy2(self.db_name, backup_path)
            return True, "Резервная копия создана успешно"
        except Exception as e:
            return False, f"Ошибка при создании резервной копии: {str(e)}"
    
    def add_new_request(self, date, car_type, car_model, problem, status, client_id, master_id=None):
        """Добавление новой заявки"""
        try:
            self.execute_query("""
                INSERT INTO Заявки (Дата_создания, Тип_авто, Модель_авто, Описание_проблемы, Статус, ID_клиента, ID_механика)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, car_type, car_model, problem, status, client_id, master_id))
            return True, "Заявка успешно добавлена"
        except Exception as e:
            return False, f"Ошибка при добавлении заявки: {str(e)}"


# ====================== ОКНО АВТОРИЗАЦИИ ======================
class LoginWindow:
    def __init__(self, db_manager):
        self.db = db_manager
        self.window = tk.Tk()
        self.window.title("Авторизация - Автосервис")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # Центрирование окна
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        title_label = tk.Label(
            self.window, 
            text="АВТОСЕРВИС", 
            font=("Arial", 20, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=30)
        
        # Подзаголовок
        subtitle_label = tk.Label(
            self.window,
            text="Система учета заявок на ремонт",
            font=("Arial", 10),
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=5)
        
        # Фрейм для формы
        frame = tk.Frame(self.window, bg="#ecf0f1", padx=20, pady=20)
        frame.pack(pady=20, padx=40, fill="both")
        
        # Логин
        tk.Label(frame, text="Логин:", bg="#ecf0f1", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.login_entry = tk.Entry(frame, font=("Arial", 10), width=25)
        self.login_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Пароль
        tk.Label(frame, text="Пароль:", bg="#ecf0f1", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(frame, font=("Arial", 10), width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Кнопка входа
        login_btn = tk.Button(
            frame,
            text="ВОЙТИ",
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=5,
            command=self.login
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Информация
        info_text = "Тестовые данные:\nМенеджер: login1 / pass1\nОператор: login4 / pass4\nМеханик: login2 / pass2\nЗаказчик: login11 / pass11"
        info_label = tk.Label(
            self.window,
            text=info_text,
            font=("Arial", 8),
            fg="#95a5a6",
            justify="left"
        )
        info_label.pack(side="bottom", pady=10)
        
        # Нажатие Enter
        self.password_entry.bind("<Return>", lambda e: self.login())
        
    def login(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        
        user = self.db.authenticate_user(login, password)
        
        if user:
            self.window.destroy()
            app = MainApplication(self.db, dict(user))
            app.run()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
    
    def run(self):
        self.window.mainloop()


# ====================== ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ ======================
class MainApplication:
    def __init__(self, db_manager, current_user):
        self.db = db_manager
        self.current_user = current_user
        
        self.root = tk.Tk()
        self.root.title(f"Автосервис - Пользователь: {self.current_user['ФИО']} ({self.current_user['Роль']})")
        self.root.geometry("1200x700")
        
        # Центрирование
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.setup_menu()
        self.setup_ui()
        self.load_requests()
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Резервное копирование", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Отчеты
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Отчеты", menu=reports_menu)
        reports_menu.add_command(label="Статистика", command=self.show_statistics)
        reports_menu.add_command(label="Заявки по механику", command=self.show_requests_by_master)
        
        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def setup_ui(self):
        # Верхняя панель с информацией
        top_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        role_colors = {
            'Менеджер': '#e74c3c',
            'Оператор': '#3498db',
            'Автомеханик': '#2ecc71',
            'Заказчик': '#f39c12',
            'Менеджер по качеству': '#9b59b6'
        }
        
        role_label = tk.Label(
            top_frame,
            text=f" {self.current_user['Роль']} ",
            bg=role_colors.get(self.current_user['Роль'], '#95a5a6'),
            fg="white",
            font=("Arial", 10, "bold")
        )
        role_label.pack(side="left", padx=10, pady=10)
        
        user_label = tk.Label(
            top_frame,
            text=self.current_user['ФИО'],
            fg="white",
            bg="#2c3e50",
            font=("Arial", 12)
        )
        user_label.pack(side="left", padx=10)
        
        # Основной контент
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Левая панель - список заявок
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Заголовок и поиск
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill="x", pady=5)
        
        tk.Label(search_frame, text="Заявки:", font=("Arial", 14, "bold")).pack(side="left")
        
        tk.Label(search_frame, text="Поиск:").pack(side="left", padx=(20, 5))
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_requests())
        
        # Кнопка добавления заявки
        add_btn = tk.Button(
            search_frame,
            text="+ Добавить заявку",
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            command=self.add_new_request
        )
        add_btn.pack(side="right", padx=5)
        
        # Таблица заявок
        columns = ("ID", "Дата", "Модель", "Проблема", "Статус", "Клиент", "Механик")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)
        
        # Настройка колонок
        self.tree.heading("ID", text="№")
        self.tree.heading("Дата", text="Дата")
        self.tree.heading("Модель", text="Модель")
        self.tree.heading("Проблема", text="Проблема")
        self.tree.heading("Статус", text="Статус")
        self.tree.heading("Клиент", text="Клиент")
        self.tree.heading("Механик", text="Механик")
        
        self.tree.column("ID", width=50)
        self.tree.column("Дата", width=100)
        self.tree.column("Модель", width=150)
        self.tree.column("Проблема", width=200)
        self.tree.column("Статус", width=150)
        self.tree.column("Клиент", width=150)
        self.tree.column("Механик", width=150)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_request_select)
        self.tree.bind("<Double-1>", lambda e: self.edit_request())  # Двойной клик для редактирования
        
        # Правая панель - детали заявки
        right_frame = tk.Frame(content_frame, width=400, bg="#ecf0f1")
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Детали заявки
        tk.Label(right_frame, text="ДЕТАЛИ ЗАЯВКИ", font=("Arial", 12, "bold"), bg="#ecf0f1").pack(pady=10)
        
        self.details_text = scrolledtext.ScrolledText(
            right_frame, 
            width=45, 
            height=15, 
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        self.details_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Панель действий
        actions_frame = tk.Frame(right_frame, bg="#ecf0f1")
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        # Статус
        tk.Label(actions_frame, text="Статус:", bg="#ecf0f1").pack(anchor="w")
        self.status_var = tk.StringVar()
        status_combo = ttk.Combobox(
            actions_frame, 
            textvariable=self.status_var,
            values=['Новая заявка', 'В процессе ремонта', 'Ожидание запчастей', 'Готова к выдаче', 'Завершена'],
            state="readonly"
        )
        status_combo.pack(fill="x", pady=5)
        
        # Механик
        tk.Label(actions_frame, text="Механик:", bg="#ecf0f1").pack(anchor="w")
        self.master_var = tk.StringVar()
        self.master_combo = ttk.Combobox(actions_frame, textvariable=self.master_var, state="readonly")
        self.master_combo.pack(fill="x", pady=5)
        self.load_masters()
        
        # Кнопки
        btn_frame = tk.Frame(actions_frame, bg="#ecf0f1")
        btn_frame.pack(fill="x", pady=10)
        
        update_btn = tk.Button(
            btn_frame,
            text="Обновить статус",
            bg="#3498db",
            fg="white",
            command=self.update_request
        )
        update_btn.pack(side="left", padx=2, fill="x", expand=True)
        
        comment_btn = tk.Button(
            btn_frame,
            text="Комментарий",
            bg="#2ecc71",
            fg="white",
            command=self.add_comment
        )
        comment_btn.pack(side="left", padx=2, fill="x", expand=True)
        
        # Кнопка для QR-кода
        qr_btn = tk.Button(
            btn_frame,
            text="QR-код",
            bg="#9b59b6",
            fg="white",
            command=self.generate_qr_code
        )
        qr_btn.pack(side="left", padx=2, fill="x", expand=True)
        
        # Кнопка редактирования
        edit_btn = tk.Button(
            btn_frame,
            text="Редактировать",
            bg="#f39c12",
            fg="white",
            command=self.edit_request
        )
        edit_btn.pack(side="left", padx=2, fill="x", expand=True)
        
        # Поле для комментария
        tk.Label(actions_frame, text="Новый комментарий:", bg="#ecf0f1").pack(anchor="w", pady=(10, 0))
        self.comment_entry = tk.Text(actions_frame, height=3, font=("Arial", 9))
        self.comment_entry.pack(fill="x", pady=5)
        
        # Кнопка продления срока (только для менеджера по качеству)
        if self.current_user['Роль'] == 'Менеджер по качеству':
            extend_btn = tk.Button(
                actions_frame,
                text="Продлить срок",
                bg="#e67e22",
                fg="white",
                command=self.extend_deadline
            )
            extend_btn.pack(fill="x", pady=5)
    
    def load_masters(self):
        masters = self.db.get_all_masters()
        master_list = [f"{m['ID_пользователя']}: {m['ФИО']}" for m in masters]
        self.master_combo['values'] = master_list
    
    def load_requests(self):
        # Очистка таблицы
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Получение заявок
        requests = self.db.get_all_requests()
        
        # Поиск
        search_text = self.search_entry.get().strip().lower()
        
        for req in requests:
            if search_text:
                if (search_text not in str(req['ID_заявки']).lower() and 
                    search_text not in req['Модель_авто'].lower() and
                    search_text not in req['Клиент'].lower()):
                    continue
            
            # Цветовая индикация статуса
            tags = ()
            if req['Статус'] == 'Новая заявка':
                tags = ('new',)
            elif req['Статус'] == 'В процессе ремонта':
                tags = ('in_progress',)
            elif req['Статус'] == 'Готова к выдаче':
                tags = ('completed',)
            
            self.tree.insert("", "end", values=(
                req['ID_заявки'],
                req['Дата_создания'],
                req['Модель_авто'],
                req['Описание_проблемы'][:50] + "..." if len(req['Описание_проблемы'] or '') > 50 else req['Описание_проблемы'],
                req['Статус'],
                req['Клиент'],
                req['Механик'] or 'Не назначен'
            ), tags=tags)
        
        # Настройка цветов
        self.tree.tag_configure('new', background='#fff3cd')
        self.tree.tag_configure('in_progress', background='#d4edda')
        self.tree.tag_configure('completed', background='#d1ecf1')
    
    def on_request_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        request_id = item['values'][0]
        
        # Загрузка деталей
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM Заявки WHERE ID_заявки = ?
        """, (request_id,))
        request = cursor.fetchone()
        
        if request:
            # Отображение деталей
            self.details_text.delete(1.0, tk.END)
            
            details = f"""
ЗАЯВКА №{request['ID_заявки']}
═══════════════════════════════

📅 Дата создания: {request['Дата_создания']}
🚗 Тип авто: {request['Тип_авто']}
🚘 Модель: {request['Модель_авто']}

📝 Описание проблемы:
{request['Описание_проблемы']}

📊 Статус: {request['Статус']}

🔧 Запчасти: {request['Запчасти'] or 'Не указаны'}

📎 Дата завершения: {request['Дата_завершения'] or 'Не завершена'}

КОММЕНТАРИИ:
═══════════════════════════════
            """
            self.details_text.insert(1.0, details)
            
            # Загрузка комментариев
            comments = self.db.get_comments_for_request(request_id)
            for comment in comments:
                self.details_text.insert(tk.END, f"\n[{comment['Дата_создания']}] {comment['Автор']}:\n{comment['Сообщение']}\n{'-'*40}\n")
            
            # Установка текущих значений
            self.status_var.set(request['Статус'])
            
            # Поиск механика в комбобоксе
            if request['ID_механика']:
                for i, master in enumerate(self.master_combo['values']):
                    if master.startswith(f"{request['ID_механика']}:"):
                        self.master_combo.current(i)
                        break
            else:
                self.master_combo.set('')
    
    def update_request(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заявку")
            return
        
        item = self.tree.item(selection[0])
        request_id = item['values'][0]
        
        new_status = self.status_var.get()
        master_str = self.master_var.get()
        
        if not new_status:
            messagebox.showwarning("Предупреждение", "Выберите статус")
            return
        
        # Обновление статуса
        self.db.update_request_status(request_id, new_status)
        
        # Назначение механика
        if master_str:
            master_id = int(master_str.split(':')[0])
            self.db.assign_master(request_id, master_id)
        
        messagebox.showinfo("Успех", "Заявка обновлена")
        self.load_requests()
        self.on_request_select(None)
    
    def add_comment(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заявку")
            return
        
        item = self.tree.item(selection[0])
        request_id = item['values'][0]
        
        comment_text = self.comment_entry.get(1.0, tk.END).strip()
        
        if not comment_text:
            messagebox.showwarning("Предупреждение", "Введите текст комментария")
            return
        
        # Только механики и менеджеры могут добавлять комментарии
        if self.current_user['Роль'] not in ['Автомеханик', 'Менеджер', 'Менеджер по качеству']:
            messagebox.showerror("Ошибка", "У вас нет прав для добавления комментариев")
            return
        
        self.db.add_comment(request_id, self.current_user['ID_пользователя'], comment_text)
        
        messagebox.showinfo("Успех", "Комментарий добавлен")
        self.comment_entry.delete(1.0, tk.END)
        self.on_request_select(None)
    
    # ========== МЕТОД ДЛЯ ДОБАВЛЕНИЯ НОВОЙ ЗАЯВКИ (ОБЩИЙ) ==========
    def add_new_request(self):
        """Открывает окно для добавления новой заявки (разное для разных ролей)"""
        
        # Для заказчика - упрощённая форма
        if self.current_user['Роль'] == 'Заказчик':
            self.add_request_for_customer()
        else:
            # Для остальных ролей - полная форма
            self.add_request_for_staff()
    
    # ========== МЕТОД ДЛЯ ЗАКАЗЧИКА (РИСУНОК 1.15) ==========
    def add_request_for_customer(self):
        """Упрощённое окно добавления заявки для заказчика"""
        
        # Создаем окно добавления
        add_window = tk.Toplevel(self.root)
        add_window.title("Новая заявка")
        add_window.geometry("450x480")
        add_window.resizable(False, False)
        
        # Центрирование окна
        add_window.update_idletasks()
        width = add_window.winfo_width()
        height = add_window.winfo_height()
        x = (add_window.winfo_screenwidth() // 2) - (width // 2)
        y = (add_window.winfo_screenheight() // 2) - (height // 2)
        add_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Заголовок
        tk.Label(add_window, text="СОЗДАНИЕ НОВОЙ ЗАЯВКИ", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Информация о клиенте
        info_frame = tk.Frame(add_window, bg="#e8f4fd", padx=10, pady=5)
        info_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(info_frame, text="Клиент:", font=("Arial", 10, "bold"), 
                 bg="#e8f4fd").pack(side="left")
        tk.Label(info_frame, text=f"{self.current_user['ФИО']}", 
                 font=("Arial", 10), fg="blue", bg="#e8f4fd").pack(side="left", padx=5)
        
        # Поля ввода
        fields_frame = tk.Frame(add_window)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Дата создания (по умолчанию сегодня, не редактируется)
        default_date = datetime.date.today().isoformat()
        
        tk.Label(fields_frame, text="Дата создания:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        date_label = tk.Label(fields_frame, text=default_date, font=("Arial", 10), fg="gray")
        date_label.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        # Тип авто (выпадающий список)
        tk.Label(fields_frame, text="Тип автомобиля:*", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        type_combo = ttk.Combobox(fields_frame, 
                                   values=['Легковая', 'Грузовая', 'Микроавтобус', 'Мотоцикл', 'Спецтехника'], 
                                   font=("Arial", 10), width=27)
        type_combo.set('Легковая')
        type_combo.grid(row=1, column=1, pady=5, padx=10)
        
        # Модель авто
        tk.Label(fields_frame, text="Модель автомобиля:*", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        model_entry = tk.Entry(fields_frame, font=("Arial", 10), width=30)
        model_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Описание проблемы
        tk.Label(fields_frame, text="Описание проблемы:*", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="nw", pady=5)
        problem_text = tk.Text(fields_frame, font=("Arial", 10), width=30, height=5)
        problem_text.grid(row=3, column=1, pady=5, padx=10)
        
        # Статус (фиксированно "Новая заявка")
        tk.Label(fields_frame, text="Статус:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        status_label = tk.Label(fields_frame, text="Новая заявка", font=("Arial", 10), 
                               fg="#856404", bg="#fff3cd")
        status_label.grid(row=4, column=1, sticky="w", pady=5, padx=10)
        
        # Подпись об обязательных полях
        tk.Label(fields_frame, text="* - обязательные поля", font=("Arial", 8), 
                 fg="gray").grid(row=5, column=0, columnspan=2, pady=5)
        
        # Кнопки
        btn_frame = tk.Frame(add_window)
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        def save_new_request():
            """Сохранение новой заявки от заказчика"""
            try:
                # Собираем данные из полей
                new_date = default_date
                new_type = type_combo.get().strip()
                new_model = model_entry.get().strip()
                new_problem = problem_text.get(1.0, tk.END).strip()
                new_status = "Новая заявка"
                client_id = self.current_user['ID_пользователя']
                
                # Валидация
                if not new_type:
                    messagebox.showerror("Ошибка", "Выберите тип автомобиля")
                    return
                
                if not new_model:
                    messagebox.showerror("Ошибка", "Введите модель автомобиля")
                    return
                
                if not new_problem:
                    messagebox.showerror("Ошибка", "Введите описание проблемы")
                    return
                
                # Добавляем заявку в БД
                success, message = self.db.add_new_request(
                    new_date, new_type, new_model, new_problem, new_status, client_id, None
                )
                
                if success:
                    messagebox.showinfo("Успех", "Заявка успешно создана")
                    add_window.destroy()
                    self.load_requests()  # Обновляем список заявок
                else:
                    messagebox.showerror("Ошибка", message)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать заявку: {str(e)}")
        
        # Кнопки сохранения и отмены
        save_btn = tk.Button(btn_frame, text="Создать заявку", bg="#27ae60", fg="white",
                            font=("Arial", 11, "bold"), command=save_new_request)
        save_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        cancel_btn = tk.Button(btn_frame, text="Отмена", bg="#e74c3c", fg="white",
                              font=("Arial", 11, "bold"), command=add_window.destroy)
        cancel_btn.pack(side="right", padx=5, fill="x", expand=True)

    # ========== МЕТОД ДЛЯ СОТРУДНИКОВ ==========
    def add_request_for_staff(self):
        """Полная форма добавления заявки для сотрудников"""
        
        # Создаем окно добавления
        add_window = tk.Toplevel(self.root)
        add_window.title("Добавление новой заявки")
        add_window.geometry("550x650")
        add_window.resizable(False, False)
        
        # Центрирование окна
        add_window.update_idletasks()
        width = add_window.winfo_width()
        height = add_window.winfo_height()
        x = (add_window.winfo_screenwidth() // 2) - (width // 2)
        y = (add_window.winfo_screenheight() // 2) - (height // 2)
        add_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Основной фрейм с прокруткой
        canvas = tk.Canvas(add_window)
        scrollbar = tk.Scrollbar(add_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок
        tk.Label(scrollable_frame, text="ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Поля ввода
        fields_frame = tk.Frame(scrollable_frame)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Дата создания (по умолчанию сегодня)
        default_date = datetime.date.today().isoformat()
        
        tk.Label(fields_frame, text="Дата создания (ГГГГ-ММ-ДД):", 
                 font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        date_entry = tk.Entry(fields_frame, font=("Arial", 10), width=30)
        date_entry.insert(0, default_date)
        date_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Тип авто
        tk.Label(fields_frame, text="Тип авто:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        type_combo = ttk.Combobox(fields_frame, 
                                   values=['Легковая', 'Грузовая', 'Микроавтобус', 'Мотоцикл', 'Спецтехника'], 
                                   font=("Arial", 10), width=28)
        type_combo.set('Легковая')
        type_combo.grid(row=1, column=1, pady=5, padx=10)
        
        # Модель авто
        tk.Label(fields_frame, text="Модель авто:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        model_entry = tk.Entry(fields_frame, font=("Arial", 10), width=30)
        model_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Описание проблемы
        tk.Label(fields_frame, text="Описание проблемы:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="nw", pady=5)
        problem_text = tk.Text(fields_frame, font=("Arial", 10), width=30, height=4)
        problem_text.grid(row=3, column=1, pady=5, padx=10)
        
        # Статус (по умолчанию "Новая заявка")
        tk.Label(fields_frame, text="Статус:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        status_combo = ttk.Combobox(fields_frame, 
                                     values=['Новая заявка', 'В процессе ремонта', 'Ожидание запчастей', 'Готова к выдаче', 'Завершена'],
                                     font=("Arial", 10), width=28)
        status_combo.set('Новая заявка')
        status_combo.grid(row=4, column=1, pady=5, padx=10)
        
        # Клиент (выбор из списка заказчиков)
        tk.Label(fields_frame, text="Клиент:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        
        clients = self.db.get_all_clients()
        if not clients:
            # Если нет клиентов, добавляем тестового
            client_list = ["6: Касаткин Егор Львович", "7: Ильина Тамара Даниловна", "8: Елисеева Юлиана Алексеевна", "9: Никифорова Алиса Тимофеевна"]
        else:
            client_list = [f"{c['ID_пользователя']}: {c['ФИО']}" for c in clients]
        
        client_combo = ttk.Combobox(fields_frame, values=client_list, font=("Arial", 10), width=28)
        if client_list:
            client_combo.current(0)
        client_combo.grid(row=5, column=1, pady=5, padx=10)
        
        # Механик (опционально)
        tk.Label(fields_frame, text="Назначенный механик (опционально):", 
                 font=("Arial", 10, "bold")).grid(row=6, column=0, sticky="w", pady=5)
        
        masters = self.db.get_all_masters()
        master_list = [""] + [f"{m['ID_пользователя']}: {m['ФИО']}" for m in masters]
        master_combo = ttk.Combobox(fields_frame, values=master_list, font=("Arial", 10), width=28)
        master_combo.set("")
        master_combo.grid(row=6, column=1, pady=5, padx=10)
        
        # Кнопки
        btn_frame = tk.Frame(scrollable_frame)
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        def save_new_request():
            """Сохранение новой заявки"""
            try:
                # Собираем данные из полей
                new_date = date_entry.get().strip()
                new_type = type_combo.get().strip()
                new_model = model_entry.get().strip()
                new_problem = problem_text.get(1.0, tk.END).strip()
                new_status = status_combo.get().strip()
                client_str = client_combo.get().strip()
                master_str = master_combo.get().strip()
                
                # Валидация
                if not new_date:
                    messagebox.showerror("Ошибка", "Введите дату создания")
                    return
                
                if not new_type:
                    messagebox.showerror("Ошибка", "Выберите тип авто")
                    return
                
                if not new_model:
                    messagebox.showerror("Ошибка", "Введите модель авто")
                    return
                
                if not new_problem:
                    messagebox.showerror("Ошибка", "Введите описание проблемы")
                    return
                
                if not new_status:
                    messagebox.showerror("Ошибка", "Выберите статус")
                    return
                
                if not client_str:
                    messagebox.showerror("Ошибка", "Выберите клиента")
                    return
                
                # Проверка формата даты
                try:
                    datetime.datetime.strptime(new_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
                    return
                
                # Получаем ID клиента
                client_id = int(client_str.split(':')[0])
                
                # Получаем ID механика (если выбран)
                master_id = None
                if master_str:
                    master_id = int(master_str.split(':')[0])
                
                # Добавляем заявку в БД
                success, message = self.db.add_new_request(
                    new_date, new_type, new_model, new_problem, new_status, client_id, master_id
                )
                
                if success:
                    messagebox.showinfo("Успех", message)
                    add_window.destroy()
                    self.load_requests()  # Обновляем список заявок
                else:
                    messagebox.showerror("Ошибка", message)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить заявку: {str(e)}")
        
        # Кнопки сохранения и отмены
        save_btn = tk.Button(btn_frame, text="Добавить заявку", bg="#27ae60", fg="white",
                            font=("Arial", 11, "bold"), command=save_new_request)
        save_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        cancel_btn = tk.Button(btn_frame, text="Отмена", bg="#e74c3c", fg="white",
                              font=("Arial", 11, "bold"), command=add_window.destroy)
        cancel_btn.pack(side="right", padx=5, fill="x", expand=True)
    
    # ========== МЕТОДЫ ДЛЯ МОДУЛЯ 3 ==========
    
    def extend_deadline(self):
        """Продление срока выполнения заявки (только для менеджера по качеству)"""
        if self.current_user['Роль'] != 'Менеджер по качеству':
            messagebox.showerror("Ошибка", "Недостаточно прав для продления срока")
            return
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заявку")
            return
        
        item = self.tree.item(selection[0])
        request_id = item['values'][0]
        
        # Диалог ввода новой даты
        new_date_str = simpledialog.askstring(
            "Продление срока",
            "Введите новую дату завершения (ГГГГ-ММ-ДД):",
            parent=self.root
        )
        if not new_date_str:
            return
        
        # Проверка формата даты
        try:
            datetime.datetime.strptime(new_date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return
        
        # Имитация согласования с клиентом
        if messagebox.askyesno("Согласование", "Клиент согласовал новую дату?"):
            self.db.execute_query(
                "UPDATE Заявки SET Дата_завершения = ? WHERE ID_заявки = ?",
                (new_date_str, request_id)
            )
            messagebox.showinfo("Успех", "Срок заявки продлён")
            self.load_requests()
            self.on_request_select(None)
    
    def generate_qr_code(self):
        """Генерация QR-кода для выбранной заявки"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заявку")
            return
        
        item = self.tree.item(selection[0])
        request_id = item['values'][0]
        
        try:
            file_path = qr_generator.generate_qr(request_id)
            messagebox.showinfo("QR-код создан", f"QR-код сохранён в:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать QR-код:\n{str(e)}")
    
    # =================================================
    
    def backup_database(self):
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_file = f"{backup_dir}/backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        success, message = self.db.backup_database(backup_file)
        
        if success:
            messagebox.showinfo("Резервное копирование", f"Резервная копия создана:\n{backup_file}")
        else:
            messagebox.showerror("Ошибка", message)
    
    def show_statistics(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика")
        stats_window.geometry("600x400")
        
        # Получение статистики
        completed_count = self.db.get_completed_requests_count()
        avg_time = self.db.get_average_completion_time()
        problem_stats = self.db.get_statistics_by_problem_type()
        
        # Отображение
        frame = tk.Frame(stats_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="СТАТИСТИКА РАБОТЫ", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Карточки
        stats_frame = tk.Frame(frame)
        stats_frame.pack(fill="x", pady=20)
        
        # Выполненные заявки
        card1 = tk.Frame(stats_frame, bg="#2ecc71", width=200, height=100)
        card1.pack(side="left", padx=10, expand=True)
        card1.pack_propagate(False)
        
        tk.Label(card1, text="Выполнено заявок", bg="#2ecc71", fg="white", font=("Arial", 10)).pack(pady=10)
        tk.Label(card1, text=str(completed_count), bg="#2ecc71", fg="white", font=("Arial", 24, "bold")).pack()
        
        # Среднее время
        card2 = tk.Frame(stats_frame, bg="#3498db", width=200, height=100)
        card2.pack(side="left", padx=10, expand=True)
        card2.pack_propagate(False)
        
        tk.Label(card2, text="Ср. время (дни)", bg="#3498db", fg="white", font=("Arial", 10)).pack(pady=10)
        tk.Label(card2, text=str(avg_time), bg="#3498db", fg="white", font=("Arial", 24, "bold")).pack()
        
        # Статистика по проблемам
        tk.Label(frame, text="Статистика по типам неисправностей", font=("Arial", 12, "bold")).pack(pady=10)
        
        tree = ttk.Treeview(frame, columns=("Тип", "Количество"), show="headings", height=8)
        tree.heading("Тип", text="Тип неисправности")
        tree.heading("Количество", text="Количество")
        tree.column("Тип", width=300)
        tree.column("Количество", width=100)
        
        for stat in problem_stats:
            tree.insert("", "end", values=(stat['Тип_неисправности'], stat['Количество']))
        
        tree.pack(fill="both", expand=True)
    
    def show_requests_by_master(self):
        if self.current_user['Роль'] != 'Менеджер':
            messagebox.showwarning("Доступ запрещен", "Только менеджеры могут просматривать эту статистику")
            return
        
        # Окно выбора механика
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор механика")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Выберите механика:", font=("Arial", 12)).pack(pady=10)
        
        masters = self.db.get_all_masters()
        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        for master in masters:
            listbox.insert(tk.END, f"{master['ID_пользователя']}: {master['ФИО']}")
        
        def show_requests():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите механика")
                return
            
            master_str = listbox.get(selection[0])
            master_id = int(master_str.split(':')[0])
            
            dialog.destroy()
            
            # Показать заявки
            result_window = tk.Toplevel(self.root)
            result_window.title(f"Заявки механика")
            result_window.geometry("800x400")
            
            requests = self.db.get_requests_by_master(master_id)
            
            tree = ttk.Treeview(result_window, columns=("ID", "Дата", "Модель", "Статус", "Клиент"), show="headings")
            tree.heading("ID", text="№")
            tree.heading("Дата", text="Дата")
            tree.heading("Модель", text="Модель")
            tree.heading("Статус", text="Статус")
            tree.heading("Клиент", text="Клиент")
            
            tree.column("ID", width=50)
            tree.column("Дата", width=100)
            tree.column("Модель", width=200)
            tree.column("Статус", width=150)
            tree.column("Клиент", width=200)
            
            for req in requests:
                tree.insert("", "end", values=(
                    req['ID_заявки'],
                    req['Дата_создания'],
                    req['Модель_авто'],
                    req['Статус'],
                    req['Клиент']
                ))
            
            tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Button(dialog, text="Показать", command=show_requests, bg="#3498db", fg="white").pack(pady=10)
    
    def show_about(self):
        about_text = """
АВТОСЕРВИС
Система учета заявок на ремонт автомобилей

Версия: 2.0 (с доработками для модуля 3)
Модуль 3: Сопровождение и обслуживание

Добавлен функционал:
- Роль «Менеджер по качеству»
- Продление срока заявки
- Генерация QR-кода для оценки качества
- Полноценное окно редактирования заявки
- Добавление новых заявок (для сотрудников и заказчиков)
- Рисунок 1.15: упрощённое окно для заказчика

© 2026
        """
        messagebox.showinfo("О программе", about_text)
    
    def run(self):
        self.root.mainloop()


# ====================== ЗАПУСК ПРИЛОЖЕНИЯ ======================
if __name__ == "__main__":
    # Создание базы данных
    db = DatabaseManager()
    
    # Добавление пользователя «Менеджер по качеству», если его нет
    try:
        db.execute_query(
            "INSERT INTO Пользователи (ФИО, Телефон, Логин, Пароль, Роль) VALUES (?, ?, ?, ?, ?)",
            ('Соколова Елена Викторовна', '89997776655', 'quality_mgr', 
             db.hash_password('pass123'), 'Менеджер по качеству')
        )
    except sqlite3.IntegrityError:
        pass  # пользователь уже существует
    
    # Создание необходимых папок
    os.makedirs("qr_codes", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    # Запуск окна авторизации
    login = LoginWindow(db)
    login.run()
    
    # Закрытие соединения при выходе
    db.close()