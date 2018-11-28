import re
import csv
from nltk.tokenize import sent_tokenize
from nltk.util import ngrams

from src.database import Database


class Ngrams:
    def __init__(self, n, k, corpus, db_path):
        """
        Клас, що здійснює обробку даних корпуса з метою знаходження частот частот N-грам
        :param n: встановлює, які саме N-грами будувати: 2-грами, 3-грами...
        :param k: поріг Катца (Katz threshold) для оцінки параметрів згладжування Гуда-Тюрінга
        :param corpus: вміст текстового файлу з корпусом тексту. Дані подано у вигляді списку параграфів тексту
        :param db_path: шлях до бази даних
        """
        # в результаті обробки отримаємо таблицю згладжування Гуда-Тюрінга (візьмемо з неї частоти та відповідні
        # їм кількості частот для побудови графіки частот частот
        self.gt_table = self.process(n, k, corpus, db_path)

    def process(self, n, k, corpus, db_path):
        # підключення до бази даних, очищення старих даних в базі
        db = Database(db_path, drop=True)
        # Розбиваємо корпус на речення та слова
        # words - множина слів у корпусі (тобто словник слів)
        # all_words - усі слова корпуса з повторами
        sentences, words, all_words = self.get_sentences_words(corpus)
        # Побудова N-грам
        ngrams_list = self.ngrams_from_sentence(sentences, n)
        # Побудова (N-1)-грам
        n_minus1_grams_list = self.ngrams_from_sentence(sentences, n - 1)
        # Укладання частотного словника N-грам
        ngrams_dict = self.get_freq_dict(ngrams_list)
        # Укладання частотного словника (N-1)-грам
        n_minus1_grams_dict = self.get_freq_dict(n_minus1_grams_list)
        # Укладання частотного словника для словника слів корпуса
        vocab_dict = self.get_freq_dict(all_words)
        # для кожної (N-1)-грами отримуємо кількість типів N-грам, які можна утворити для даної (N-1)-грами
        # в даному корпусі
        smoothing_params = self.get_ngrams_types_counts_for_n_minus1_grams(ngrams_dict, n_minus1_grams_dict, words)
        # Загальна кількість N-грам в корпусі - це кількість (N-1)-грам помножена на розмір словника слів корпусу
        total_count_of_ngrams = len(n_minus1_grams_dict.keys()) * len(words)
        # отримуємо частоти частот N-грам
        frequencies_of_ngrams_frequencies = self.get_frequencies_of_ngrams_frequencies(ngrams_dict,
                                                                                       total_count_of_ngrams)
        # обчислюємо параметри згладжування Гуда-Тюрінга
        gt_counts_estimation = self.get_gt_counts_estimation(frequencies_of_ngrams_frequencies, k)
        # підготовка запису даних таблиць до бази даних
        ngrams_freq = self.freq_table_db(ngrams_dict)
        n_minus1_grams_freq = self.freq_table_db(n_minus1_grams_dict)
        vocab_freq = self.freq_table_db(vocab_dict)
        gt_estimation_table_db = self.gt_table_db(gt_counts_estimation)
        smoothing_table_db = self.freq_table_db(smoothing_params)
        # збереження даних до csv-файлу
        self.write_to_csv("../csv_files/ngrams.csv", ngrams_freq)
        self.write_to_csv("../csv_files/n_minus1_grams.csv", n_minus1_grams_freq)
        self.write_to_csv("../csv_files/witten-bell.csv", smoothing_table_db)
        self.write_to_csv("../csv_files/good-turing.csv", gt_estimation_table_db)


        # додавання даних відповідних таблиць до бази
        db.add_freq_data(ngrams_freq, db.tables_names["ngrams frequency table"])
        db.add_freq_data(n_minus1_grams_freq, db.tables_names["(n-1)-grams frequency table"])
        db.add_freq_data(vocab_freq, db.tables_names["Vocabulary frequency table"])
        db.add_gt_estimation_data(gt_estimation_table_db)
        db.add_smoothing_data(smoothing_table_db)
        return gt_estimation_table_db

    @staticmethod
    def write_to_csv(filename, data):
        with open(filename, mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in data:
                csv_writer.writerow(row)

    def get_sentences_words(self, paragraphs):
        """
        На вхід подається текст, поділений на параграфи (абзаци).
        На вих
        :param paragraphs: вхідний текст подається у вигляді списку параграфів
        :return: sentences - список речень, 
        words - множина слів тексту (словник слів тексту)
        all_words - усі слова, що є в тексті
        """
        # списки для збереження результату
        sentences, words, all_words = [], [], []
        for p in paragraphs:  # для кожного абзацу 
            sentence = sent_tokenize(p)  # за допомогою nltk.sent_tokenize розбиваємо абзац на речення
            sentences.extend(sentence)  # речення даного абзацу додаємо до списку речень
        for s in sentences:  # для кожного речення
            words_in_sentence = self.split_to_words(s)  # розбиваємо речення на слова
            all_words.extend(words_in_sentence)  # додаємо усі слова цього речення до списку all_words
        # до списку words додаємо слово, якщо його ще немає у списку words
        # у вас виникає запитання: чому просто не скористатися words = set(all_words)
        # потрібно зберегти порядок для відображення у базі даних таблиці частот словника слів (vocab_freq)
        for w in all_words:
            if w not in words:
                words.append(w)
        return sentences, words, all_words

    def ngrams_from_sentence(self, sentences, n):
        """
        Для кожного речення будуються N-грами
        :param sentences: речення, для потрібно побудувати n-грами
        :param n: означає, які саме n-грами будувати: 2-грами, 3-грами
        :return: список N-грам
        """
        ngrams_list = []
        for s in sentences:
            n_grams = self.get_ngrams(s, n)
            ngrams_list.extend(n_grams)
        return ngrams_list

    def get_ngrams(self, sentence, n):
        """
        На вхід подається речення, на виході - список його
        :param sentence:
        :param n: параметр для позначення N у N-грамах
        :return:  # список n-Грам цього речення. Кожна N-грама записується у вигляді рядка: слово1 слово2 ... словоN
        """
        words = self.split_to_words(sentence)
        if len(words) < n:  # якщо в реченні менше слів, ніж
            return []
        # оскільки це об'єкт-генератор, у наступному рядку конвертую отримані N-грами в список
        n_grams = ngrams(words, n)
        return [' '.join(grams) for grams in n_grams]

    @staticmethod
    def split_to_words(text):
        """
        Здійснюється поділ на слова
        :param text: текст, в якому здійснюється поділ на слова
        :return: список слів цього тексту
        """
        # поділ на слова
        # розділювачі
        delimiters = [".", ";", "!", "?", ":", ",", " ", "\n", "", "(", ")", "‘", "—"]
        # поділ на основі регулярного виразу
        # здійснюється поділ по перелічених в квадратних дужках символах + в кінці 0 або більше символів пробілів
        words_list = re.split(r'[.;!?:(),—"‘\s]\s*', text)
        # конвертуємо кожне слово до нижнього регістру та не враховуємо до нового списку words розділювачі
        words = [w.lower() for w in words_list if w not in delimiters]
        return words

    @staticmethod
    def get_freq_dict(data_list):
        """
        Побудова частотного словника для списку даних (використувується для N-грам, (N-1)-грам,
        словника слів, частот N-грам
        :param data_list: список з даними, для якого потрібно побудувати частотний словник
        :return: частотний словник для списку даних data_list
        """
        d = dict()  # оголошуємо словник - пари {ключ: значення}
        for item in data_list:  # для кожного елементу в списку
            if item in d.keys():  # якщо цей елемент вже є в списку ключів словника
                d[item] += 1  # зібльшуємо частоту на 1
            else:
                d[item] = 1  # інакше встановлюємо частоту = 1
        return d

    def get_frequencies_of_ngrams_frequencies(self, ngrams_freq_dict, total):
        """
        Знаходження частот для частот N-грам
        :param ngrams_freq_dict: частотний словник N-грам
        :param total: Загальна кількість N-грам, яку можна утворити в даному корпусі
        це кількість (N-1)-грам помножена на розмір словника слів корпусу
        :return: частотний словник для частот N-грам
        """
        frequencies = ngrams_freq_dict.values()  # добуваємо із частотного словника список значень (список з частотами)
        v_dict = self.get_freq_dict(frequencies)  # будуємо частотний словник частот N-грам
        # створюємо словник, де парою є {частота N-грам : кількість, скільки разів зустрічається ця частота}
        variation_dict = dict()
        # заповнюємо словник значеннями: від нуля до максимальної частоти, на даний момент кількість,
        # скільки разів зустрічається певна частота ініціалізуємо нулем
        # range(max(frequencies) + 1) - тому, що range(m) - це список від 0 до m-1
        for i in range(max(frequencies) + 1):
            variation_dict[i] = 0
        # заповнюємо словник variation_dict значеннями з побудованого частотного словника частот v_dict
        for freq in v_dict.keys():
            # частоти словника variation_dict, яких немає в списку ключів побудованого частотного словника v_dict,
            # залишаться незмінними (рівними нулю)
            variation_dict[freq] = v_dict[freq]
        # підраховуємо кількість N-грам частоти нуль: це загальна кількість N-грам, яку можна побудувати
        # в даному корпусі мінус сума всіх кількостей частот N-грам від 1 до максимальної частоти
        variation_dict[0] = total - sum(k * v for k, v in variation_dict.items())
        return variation_dict

    @staticmethod
    def get_gt_counts_estimation(n_c, k):
        """

        :param n_c: кількість N-грам, що зустрічаються c разів
        :param k: поріг Катца (Katz threshold)
        :return: для кожної частоти N-грам повертається її згладжена кількість Гуда-Тюрінга
        (див. останній стовпчик таблиці 6.10 на сторінці 213 (238 в рідері) книжки Журафського)
        """
        # словник
        # ключ: частота N-грам
        # значення: список у форматі:[скільки N-грам є в корпусі для цієї частоти,
        # згладжена кількість за Гудом-Тюрінгом (Good-Turing counts re_estimation) ]
        gt_counts = dict()
        m = max(n_c.keys())
        if k > m:
            for i in range(m + 1, k + 2):
                n_c[i] = 0
        for c in range(m + 1):
            # за формулою 6.29 на сторінці 214 (239 в рідері) книжки Журафського
            if 0 <= c <= k:
                estimated_count = (((c + 1) * (n_c[c + 1]) / (n_c[c])) - ((n_c[k + 1] * c * (k + 1)) / n_c[1])) \
                                  / (1 - (n_c[k + 1] * (k + 1)) / (n_c[1]))
            else:
                estimated_count = c
            gt_counts[c] = [n_c[c], estimated_count]
        return gt_counts

    @staticmethod
    def get_ngrams_types_counts_for_n_minus1_grams(ngrams_freq_dict, n_minus1_grams_freq_dict, words):
        """
        Для кожної (N-1)-грами знаходимо кількість типів N-грам, які можна утворити для цієї (N-1)-грами
        в даному корпусі
        :param ngrams_freq_dict: частотний словник N-грам
        :param n_minus1_grams_freq_dict: частотний словник (N-1)-грам
        :param words: словник слів у корпусі
        :return: словник у форматі: {(N-1)-грама: кількість типів N-грам, які можна утворити з даної (N-1)-грами в
        даному корпусі}
        """
        # словник t у форматі: {(N-1)-грама: кількість типів N-грам, які можна утворити з даної (N-1)-грами}
        t = dict()
        for i in n_minus1_grams_freq_dict.keys():
            t[i] = 0
        # Як утворюється N-грама: до кожної (N-1)-грами дописуємо почергово кожне слово зі словника слів
        # Як рахувати кількість типів N-грам, які утворюються з даної (N-1)-грами:
        # Якщо N-грама, утворена об'єднанням (N-1)-грами і певного слова зі словника слів,
        # є в частотному словнику N-грам, тобто частота N-грами в корпусі більше нуля, то цей тип N-грами
        # можна утворити з даної (N-1)-грами, і значення у словнику t збільшується на одиницю
        for first in n_minus1_grams_freq_dict.keys():  # для кожної (N-1)-грами
            for second in words:  # для кожного слова в словнику слів
                ngram = " ".join([first, second])  # об'єднання (N-1)-грами і слова зі словника слів у N-граму
                count = ngrams_freq_dict.get(ngram, 0)  # Пошук даної N-грами в частотному словнику,
                # якщо такої N-грами немає - повертається кількість нуль
                if count > 0:  # якщо кількість більше нуля, тобто така N-грама існує в корпусі, то
                    t[first] += 1  # збільшуємо кількість типів N-грам для цієї (N-1)-грами на одиницю
        return t

    @staticmethod
    def freq_table_db(d):
        """
        Функція для підготовки запису таблиць частот до бази даних. Таблиці частот представлено у вигляді словника
        Потрібно конвертувати словник у список кортежів
        :param d: частотний словник
        :return: список кортежів таблиці частотного словника (кожен кортеж - ця рядочок таблиці в базі даних)
        """
        results = []
        # k - сутності, для яких визначено частоти (N-грами, (N-1)-грами, слова зі словника слів,
        # у випадку частотного словника частот - частоти
        # v - частоти
        for k, v in d.items():
            t = tuple([k, v])
            results.append(t)
        return results

    @staticmethod
    def gt_table_db(d):
        """
        Конвертація таблиці з параметрами згладжування Гуда-Тюрінга для збереження в базі даних
        :param d: словник
        ключ: частота N-грам
        значення: список у форматі:[скільки N-грам є в корпусі для цієї частоти,
        згладжена кількість за Гудом-Тюрінгом (Good-Turing counts re_estimation) ]
        :return: список кортежів для збереження таблиці у базі даних
        """
        results = []
        for k, v in d.items():
            # дана функція відрізняється від попередньої наявністю * біля значень v словника
            # * означає розпакування елементів списку v (див. які значення (values) має словник d
            # тому кортеж t у даному випадку містить три елементи:
            # 1) частота N-грами
            # 2) скільки N-грам є в корпусі для цієї частоти
            # 3) згладжена кількість за Гудом-Тюрінгом для цієї частоти N-грам
            t = tuple([k, *v])
            results.append(t)
        return results
