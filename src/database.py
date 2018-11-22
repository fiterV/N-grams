import sqlite3


class Database:
    def __init__(self, db, drop):
        """
        Клас, що відповідає за роботу з базою даних
        :param db: шлях до бази даних
        :param drop: булеве значення, визначає чи потрібно очистити базу даних при підключенні до неї.
        при повторному записі в базу даних дані будуть перезаписуватись (коли користувач натискає у вікні кнопку
        " Write to Database"

        Коли ж користувач натискає у вікні кнопку "Update Chart" відбувається підключення до бази з метою
        отримання даних для графіка, тому дані в базі не потрібно очищати
        """
        self.connection = sqlite3.connect(db)
        self.cursor = self.connection.cursor()
        # База даних містить п'ять таблиць:
        # 1) частотний словник n-грам
        # 2) частотний словник (n-1)-грам
        # 3) частотний словник слів корпуса
        # 4) Таблиця, що містить коефіцієнти згладжування Гуда-Тюрінга для кожної частоти n-грамм
        # 5) Таблиця, що містить кількість типів N-грам, які можна утворити з
        # даної (N-1)-грами в даному корпусі (для згладжування Віттена-Белла)
        self.tables_names = {
            "ngrams frequency table": "ngrams_freq",
            "(n-1)-grams frequency table": "n_minus1_grams_freq",
            "Vocabulary frequency table": "vocab_freq",
            "Good-Turing estimation table": "gt_estimation_counts",
            "Smoothing": "smoothing"
        }
        if drop:
            self.drop_db()
        self.create_tables()  # створення таблиць в базі даних

    def get_tables_names(self):
        """
        :return: функція повертає список назв таблиць бази даних
        """
        sql_command = """SELECT name FROM sqlite_master WHERE type = "table" """
        self.cursor.execute(sql_command)
        res = self.cursor.fetchall()
        result = [t[0] for t in res]
        return result

    def drop_tables(self, tables_names):
        """
        Видалення всіх даних з вказаних таблиць
        :param tables_names: список з назвами усіх таблиць бази даних
        """
        sql_command = ""
        for table in tables_names:
            sql_command += "DROP TABLE IF EXISTS '{}'; ".format(table)
        self.cursor.executescript(sql_command)
        self.connection.commit()

    def drop_db(self):
        """
        Очищення даних в базі
        """
        tables = self.get_tables_names()
        self.drop_tables(tables)

    def create_tables(self):
        """
        Створення таблиць
        """
        tables_list = [self.tables_names[table] for table in self.tables_names.keys() if "freq" in table]
        sql_command = ""
        for table in tables_list:
            sql_command += """
            CREATE TABLE IF NOT EXISTS '{}'
            (`id`	INTEGER,
            `word` TEXT,
            `freq` INTEGER,
            PRIMARY KEY(`id`));""".format(table)
        sql_command += """
        CREATE TABLE IF NOT EXISTS '{0}'
        (`id`	INTEGER,
        `freq` INTEGER,
        `count_` INTEGER,
        `gt_count` REAL,
        PRIMARY KEY(`id`));

        CREATE TABLE IF NOT EXISTS '{1}'
        (`id`	INTEGER,
        `n_minus1_gram` TEXT,
        `ngrams_types_count_` INTEGER,
        PRIMARY KEY(`id`));
        """.format(self.tables_names["Good-Turing estimation table"], self.tables_names["Smoothing"])
        self.cursor.executescript(sql_command)
        self.connection.commit()

    def add_freq_data(self, data, table):
        """
        Додавання даних у таблицю з частотами
        :param data: дані у форматі: слово, частота
        :param table: таблиця, в яку додаємо дані (для N-грам, (N-1)-грам, для словника слів корпуса)
        """
        self.cursor.execute("BEGIN TRANSACTION")
        for record in data:
            sql_command = """
            INSERT OR IGNORE INTO {0}(word, freq)
            VALUES(?,?)""".format(table)
            self.cursor.execute(sql_command, record)
        self.cursor.execute("COMMIT")

    def add_gt_estimation_data(self, data):
        """
        Додавання даних у таблицю оцінки параметрів згладжування Гуда-Тюрінга
        :param data: дані у такому форматі:
        1) частота n-грамм
        2) кількість типів N-грам з такою частотою
        3) коефіцієнт згладжування Гуда-Тюрінга для цієї частоти
        """
        self.cursor.execute("BEGIN TRANSACTION")
        for record in data:
            sql_command = """
            INSERT OR IGNORE INTO {0}(freq, count_, gt_count)
            VALUES(?,?,?)""".format(self.tables_names["Good-Turing estimation table"])
            self.cursor.execute(sql_command, record)
        self.cursor.execute("COMMIT")

    def add_smoothing_data(self, data):
        """
        Додавання даних у таблицю оцінки параметрів згладжування Віттена-Белла  (для згладжування Віттена-Белла)
        :param data: дані у такому форматі:
        1) (N-1)-грама
        2) кількість типів N-грам, які можна утворити з даної (N-1)-грами в даному корпусі
        """
        self.cursor.execute("BEGIN TRANSACTION")
        for record in data:
            sql_command = """
            INSERT OR IGNORE INTO {0}(n_minus1_gram, ngrams_types_count_)
            VALUES(?,?)""".format(self.tables_names["Smoothing"])
            self.cursor.execute(sql_command, record)
        self.cursor.execute("COMMIT")

    def load_gt_estimation_data(self):
        """
        :return: завантаження даних таблиці Гуда-Тюрінга (частоти та їх кількості) для побудови графіка
        """
        sql_command = "SELECT freq, count_ FROM {} ".format(self.tables_names["Good-Turing estimation table"])
        self.cursor.execute(sql_command)
        result = self.cursor.fetchall()
        return result
