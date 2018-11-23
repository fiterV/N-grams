from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import *

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure

from src.chart import FrequencyChart
from src.ngrams import Ngrams, Database


class TkinterApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("NGRAMS")
        # У графічному інтерфейсі об'єкти на формі (віджети) розміщуються у спеціальні контейнери - рамки (фрейми)
        # У першу рамку помістимо підписи (лейбли) параметру N, що позначає N-грами, порогу Катца, нижньої та верхньої
        # меж частот для графіка; та відповідні їм текстові поля (Entry)
        frame1 = Frame(self)
        # anchor=W означає вирівнювання по лівому краю, fill=X - що вміст рамки розтягується по ширині вікна
        frame1.pack(anchor=W, fill=X)  # pack - розміщуємо елемент на формі
        # у другу розміщуємо підпис та текстове поле для шляху файлу бази даних, а також кнопку Load Database,
        # що записує шлях вибраного файлу бази даних до текстового поля
        frame2 = Frame(self)
        frame2.pack(anchor=W, fill=X)
        # У третій рамці - аналогічно для корпусу тексту: підпис, текстове поле для шляху файлу і кнопка Load Corpus,
        # що завантажує шлях вибраного текстового файлу до текстового поля
        frame3 = Frame(self)
        frame3.pack(anchor=W, fill=X)
        # четверта рамка містить дві кнопки
        # 1) Write to Database - здійснює обробку корпусу тексту, записує дані до бази даних та виводить на екран
        # графік частот частот N-грам
        # 2) Update Chart - за вказаним шляхом файлу бази даних та межами частот (Frequency lower / upper bound)
        # видобуває з бази даних відповідні значення та оновлює графік на екрані
        frame4 = Frame(self)
        frame4.pack(anchor=W, fill=X)
        # у наступній рамці розмістимо полотно canvas, на якому малюється графік
        frame_for_canvas = Frame(self)
        # fill=BOTH - означає, що рамка розтягується в обох напрямках (і по ширині, і по висоті)
        # expand=1 - рамка розтягується при зміні розмірів вікна
        frame_for_canvas.pack(anchor=W, fill=BOTH, expand=1)
        # рамка для matplotlib-панелі з кнопками
        frame_for_toolbar = Frame(self)
        frame_for_toolbar.pack(anchor=W)

        # Розміщуємо елементи першої рамки
        n_label = Label(frame1, text="N for N-grams")  # підпис для N-грам
        # padx, pady - відступи по горизонталі, вертикалі від краю вікна, або попереднього віджета
        n_label.pack(side=LEFT, padx=10, pady=10)
        # self означає, що цей об'єкт належить класу, тобто його можна викликати з будь-якого місця в класі
        self.n_entry = Entry(frame1, width=7)  # текстове поле для числа N
        self.n_entry.insert(0, '2')  # вставка значення за замовчуванням
        self.n_entry.pack(side=LEFT)

        k_label = Label(frame1, text="Katz threshold")  # підпис для порогу Катца
        k_label.pack(side=LEFT, padx=10, pady=10)
        self.k_entry = Entry(frame1, width=7)  # текстове поле для введення порогу Катца
        self.k_entry.insert(0, '5')  # значення за замовчуванням
        self.k_entry.pack(side=LEFT)

        lower_bound_label = Label(frame1, text="Frequency lower bound")  # підпис для нижньої межі частот
        lower_bound_label.pack(side=LEFT, padx=10, pady=10)
        self.lower_bound_entry = Entry(frame1, width=10)  # текстове поле для нижньої межі
        self.lower_bound_entry.pack(side=LEFT)

        upper_bound_label = Label(frame1, text="Frequency upper bound")  # підпис для верхньої межі частот
        upper_bound_label.pack(side=LEFT, padx=10, pady=10)
        self.upper_bound_entry = Entry(frame1, width=10)  # текстове поле для верхньої межі частот
        self.upper_bound_entry.pack(side=LEFT, padx=(0, 10))

        # розміщуємо елементи другої рамки
        db_path_label = Label(frame2, text="Database path")  # підпис
        db_path_label.pack(side=LEFT, padx=(10, 11), pady=10)
        self.db_path_entry = Entry(frame2)  # текстове поле для шляху бази даних
        self.db_path_entry.pack(side=LEFT, fill=X, expand=1)
        # Кнопка Load Database, що завантажує до поля шляху файлу бази даних шлях до вибраного файлу
        load_db_btn = Button(frame2, text="Load Database",
                             command=lambda: self.load_path_to_entry(self.db_path_entry, ("Database files", "*.db")))
        load_db_btn.pack(side=LEFT, padx=10, pady=10, ipadx=20)  # ipadx - відступ всередині віджета (по горизонталі)

        # розміщуємо елементи третьої рамки
        corpus_path_label = Label(frame3, text="Corpus path")  # підпис
        corpus_path_label.pack(side=LEFT, padx=(10, 20), pady=10)
        self.corpus_path_entry = Entry(frame3)  # текстове поле для шляху файлу корпусу тексту
        self.corpus_path_entry.pack(side=LEFT, fill=X, expand=1)
        # Кнопка Load Corpus - завантажує до текстового поля шлях вибраного текстового файлу
        load_corpus_btn = Button(frame3, text="Load Corpus",
                                 command=lambda: self.load_path_to_entry(self.corpus_path_entry,
                                                                         ("Txt files", "*.txt")))
        load_corpus_btn.pack(side=LEFT, padx=10, pady=10, ipadx=25)

        # розміщуємо елементи четвертої рамки
        # кнопка Write to Database
        write_db_btn = Button(frame4, text="Write to Database", command=lambda: self.write_to_database())
        write_db_btn.pack(side=LEFT, padx=10, pady=10, fill=X, expand=1)
        # Кнопка Update Frequency Chart
        update_chart_btn = Button(frame4, text="Update Frequency Chart", command=lambda: self.update_chart())
        update_chart_btn.pack(side=LEFT, padx=10, pady=10, fill=X, expand=1)
        # налаштування елементів, що відповідають за графік
        self.figure = Figure(figsize=(1, 1), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame_for_canvas)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)
        toolbar = NavigationToolbar2Tk(self.canvas, frame_for_toolbar)
        toolbar.update()

    def load_path_to_entry(self, entry_widget, file_types):
        """
        Функція виконується, коли користувач натискає на кнопки Load Database або Load Corpus
        Відкривається вікно вибору файлу, користувач обирає файл, і до відповідного текстового поля записується шлях
        # вибраного файлу
        :param entry_widget: текстове поле, куди записується шлях вибраного файлу
        :param file_types: фільтр файлових типів, файли яких типів можна вибрати
        """
        filename = filedialog.askopenfilename(filetypes=(file_types, ("All files", "*.*")))
        if filename:
            self.set_entry_widget_content(entry_widget, filename)

    @staticmethod
    def get_entry_widget_content(entry_widget):
        """
        Повертає вміст текстового поля
        :param entry_widget: текстове поле
        :return: вміст текстового поля у вигляді рядка тексту
        """
        return entry_widget.get()

    @staticmethod
    def set_entry_widget_content(entry_widget, content):
        """
        Встановлює вміст текстого поля
        :param entry_widget: текстове поле, де потрібно оновити вміст
        :param content: вміст (контент), який буде вставлено до текстового поля
        """
        entry_widget.delete(0, END)  # очищення вмісту текстового поля
        entry_widget.insert(0, content)  # вставка нового вмісту

    def draw_chart(self, data):
        """
        побудова графіка частот частот
        :param data: дані для побудови графіка
        """
        fc = FrequencyChart()
        fc.chart_draw(self.figure, data)
        self.canvas.draw()

    @staticmethod
    def read_file(filename):
        """
        Прочитання текстового файлу корпусу тексту
        :param filename: ім'я текстового файлу
        :return: вміст прочитаного текстового файлу
        """
        try:  # спочатку відкриємо файл у кодування utf-8
            # суфікс -sig означає, що не враховуємо BOM-байт (Byte Order Mark)
            with open(filename, 'r', encoding='utf-8-sig') as f:
                data = f.readlines()  # список рядків прочитаного файлу
                f.close()  # закриваємо файловий потік
        # Якщо виникає помилка декодування Юнікоду, прочитуємо файл в ANSI-кодуванні windows-1251
        except UnicodeDecodeError:
            with open(filename, 'r', encoding='windows-1251') as f:
                data = f.readlines()
                f.close()
        return data

    @staticmethod
    def parse_params(parameter, bound, default_value):
        """
        Парсинг параметрів, введених на формі
        :param parameter: параметр, значення якого перевіряємо
        :param bound: число, що позначає нижню межу параметра
        :param default_value: значення за замовчуванням
        :return: відкоректоване значення параметра
        """
        try:
            # конвертація у цілочисельний тип
            parameter = int(parameter)
            # якщо параметр менше нижньої межі, присвоюємо значення за замовчуванням
            if parameter < bound:
                parameter = default_value
        # якщо виникає помилка при конвертуванні до цілочисельного типу, присвоюємо значення за замовчуванням
        except ValueError:
            parameter = default_value
        return parameter

    @staticmethod
    def parse_upper_bound(parameter, min_bound, max_bound):
        """
        Парсинг параметра верхньої межі частот для графіка.
        :param parameter: значення верхньої межі частот для графіка
        :param min_bound: значення нижньої межі частот
        :param max_bound: максимально можливе значення верхньої межі (визначається максимальною
        частотою, що є в корпусі)
        :return: відкоректоване значення верхньої межі частот для графіка
        """
        try:
            # конвертація до цілочисельного типу
            parameter = int(parameter)
            # якщо значення параметра не в межах від нижньої межі до максимально можливої верхньої вежі
            if not min_bound <= parameter <= max_bound:
                parameter = max_bound  # то присвоїти значення максимально можливої верхньої межі
        # якщо виникає помилка при конвертуванні до цілочисельного типу, присвоюємо максимально можливе значення
        # верхньої межі
        except ValueError:
            parameter = max_bound
        return parameter

    def write_to_database(self):
        """
        Функція виконується, коли користувач натискає на кнопку Write to Database
        """
        # зчитуємо значення параметрів на формі
        n = self.get_entry_widget_content(self.n_entry)
        k = self.get_entry_widget_content(self.k_entry)
        # парсимо їх
        n = self.parse_params(n, 2, 2)
        k = self.parse_params(k, 0, 5)
        # шлях до файлу бази даних
        db = self.get_entry_widget_content(self.db_path_entry)
        # шлях до файлу корпусу тексту
        corpus_path = self.get_entry_widget_content(self.corpus_path_entry)
        # прочитуємо вміст файлу корпусу тексту
        try:
            corpus = self.read_file(corpus_path)
        # якщо файл не знайдено, виведення вікна про помилку
        except FileNotFoundError:
            messagebox.showerror("Corpus file error", "Unable to open corpus file\n{}".format(corpus_path))
            return
        # обробка корпусу тексту
        ngrams = Ngrams(n, k, corpus, db)
        # таблиця з розрахованими частотами частот для побудови графіка
        gt_table = ngrams.gt_table
        # зчитуємо з форми значення полів нижньої та верхньої межі частот
        lower_bound = self.get_entry_widget_content(self.lower_bound_entry)
        upper_bound = self.get_entry_widget_content(self.upper_bound_entry)
        # парсинг значень
        lower_bound = self.parse_params(lower_bound, 0, 0)
        max_upper_bound = max(list(zip(*gt_table))[0])  # визначення максильно можливої верхньої межі
        # zip(*gt_table) - означає транспонування таблиці - тепер перший елемент списку - це частоти, другий - частоти частот
        # до транспонування кожен елемент був представлений у вигляді списку [частота, кількість цієї частоти]
        upper_bound = self.parse_upper_bound(upper_bound, lower_bound, max_upper_bound)
        # до текстових полів записуємо відкоректовані значення параметрів
        self.set_entry_widget_content(self.n_entry, str(n))
        self.set_entry_widget_content(self.k_entry, str(k))
        self.set_entry_widget_content(self.lower_bound_entry, str(lower_bound))
        self.set_entry_widget_content(self.upper_bound_entry, str(upper_bound))

        # побудова графіка
        self.draw_chart(gt_table[lower_bound:upper_bound + 1])

    def update_chart(self):
        """
        Функція виконується, коли користувач натискає на кнопку "Update Frequency Chart"
        Відбувається підключення до вказаного файлу бази даних, з неї зчитуються дані для побудови графіка
        Та на основі вказаних меж частот будується новий графік (без обробки корпусу тексту)
        """
        # зчитуємо шлях до файлу бази даних
        db_path = self.get_entry_widget_content(self.db_path_entry)
        if db_path == "":  # якщо шлях порожній, виводимо повідомлення про помилку
            messagebox.showerror("Database file error", "Database path cannot be empty")
            return
        # підключення до бази даних
        db = Database(db_path, drop=False)
        # завантаження даних для побудови графіка
        gt_table = db.load_gt_estimation_data()
        # якщо даних в базі немає виводимо повідомлення про помилку
        if len(gt_table) == 0:
            messagebox.showerror("Database file error", "Cannot load data from database\n{}".format(db_path))
            return
        # зчитування та парсинг значень нижньої та верхньої межі частот
        lower_bound = self.get_entry_widget_content(self.lower_bound_entry)
        upper_bound = self.get_entry_widget_content(self.upper_bound_entry)
        lower_bound = self.parse_params(lower_bound, 0, 0)
        max_upper_bound = max(list(zip(*gt_table))[0])
        upper_bound = self.parse_upper_bound(upper_bound, lower_bound, max_upper_bound)
        # встановлення відкоректованих значень нижньої та верхньої межі частот
        self.set_entry_widget_content(self.lower_bound_entry, str(lower_bound))
        self.set_entry_widget_content(self.upper_bound_entry, str(upper_bound))

        # побудова нового графіка
        self.draw_chart(gt_table[lower_bound:upper_bound + 1])
