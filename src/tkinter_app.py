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
        Grid.rowconfigure(self, 0, weight=1)
        Grid.columnconfigure(self, 0, weight=1)
        frame1 = Frame(self)
        frame1.pack(anchor=W, fill=X)
        frame2 = Frame(self)
        frame2.pack(anchor=W, fill=X)
        frame3 = Frame(self)
        frame3.pack(anchor=W, fill=X)
        frame4 = Frame(self)
        frame4.pack(anchor=W, fill=X)
        frame_for_canvas = Frame(self)
        frame_for_canvas.pack(anchor=W, fill=BOTH, expand=1)
        frame_for_toolbar = Frame(self)
        frame_for_toolbar.pack(anchor=W)
        n_label = Label(frame1, text="N for N-grams")
        n_label.pack(side=LEFT, padx=10, pady=10)
        self.n_entry = Entry(frame1, width=7)
        self.n_entry.insert(0, '2')
        self.n_entry.pack(side=LEFT)

        k_label = Label(frame1, text="Katz threshold")
        k_label.pack(side=LEFT, padx=10, pady=10)
        self.k_entry = Entry(frame1, width=7)
        self.k_entry.insert(0, '5')
        self.k_entry.pack(side=LEFT)

        lower_bound_label = Label(frame1, text="Frequency lower bound")
        lower_bound_label.pack(side=LEFT, padx=10, pady=10)
        self.lower_bound_entry = Entry(frame1, width=10)
        self.lower_bound_entry.pack(side=LEFT)

        upper_bound_label = Label(frame1, text="Frequency upper bound")
        upper_bound_label.pack(side=LEFT, padx=10, pady=10)
        self.upper_bound_entry = Entry(frame1, width=10)
        self.upper_bound_entry.pack(side=LEFT, padx=(0, 10))

        db_path_label = Label(frame2, text="Database path")
        db_path_label.pack(side=LEFT, padx=(10, 11), pady=10)
        self.db_path_entry = Entry(frame2)
        self.db_path_entry.pack(side=LEFT, fill=X, expand=1)
        load_db_btn = Button(frame2, text="Load Database",
                             command=lambda: self.load_path_to_entry(self.db_path_entry, ("Database files", "*.db")))
        load_db_btn.pack(side=LEFT, padx=10, pady=10, ipadx=20)

        corpus_path_label = Label(frame3, text="Corpus path")
        corpus_path_label.pack(side=LEFT, padx=(10, 20), pady=10)
        self.corpus_path_entry = Entry(frame3)
        self.corpus_path_entry.pack(side=LEFT, fill=X, expand=1)
        load_corpus_btn = Button(frame3, text="Load Corpus",
                                 command=lambda: self.load_path_to_entry(self.corpus_path_entry,
                                                                         ("Txt files", "*.txt")))
        load_corpus_btn.pack(side=LEFT, padx=10, pady=10, ipadx=25)

        write_db_btn = Button(frame4, text="Write to Database", command=lambda: self.write_to_database())
        write_db_btn.pack(side=LEFT, padx=10, pady=10, fill=X, expand=1)

        update_chart_btn = Button(frame4, text="Update Frequency Chart", command=lambda: self.update_chart())
        update_chart_btn.pack(side=LEFT, padx=10, pady=10, fill=X, expand=1)

        self.figure = Figure(figsize=(1, 1), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame_for_canvas)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)
        toolbar = NavigationToolbar2Tk(self.canvas, frame_for_toolbar)
        toolbar.update()

    def load_path_to_entry(self, entry_widget, file_types):
        filename = filedialog.askopenfilename(filetypes=(file_types, ("All files", "*.*")))
        if filename:
            self.set_entry_widget_content(entry_widget, filename)

    @staticmethod
    def get_entry_widget_content(entry_widget):
        return entry_widget.get()

    @staticmethod
    def set_entry_widget_content(entry_widget, content):
        entry_widget.delete(0, END)
        entry_widget.insert(0, content)

    def draw_chart(self, data):
        fc = FrequencyChart()
        fc.chart_draw(self.figure, data)
        self.canvas.draw()

    @staticmethod
    def read_file(filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                data = f.readlines()
                f.close()
        except UnicodeDecodeError:
            with open(filename, 'r', encoding='windows-1251') as f:
                data = f.readlines()
                f.close()
        return data

    @staticmethod
    def parse_params(parameter, bound, default_value):
        try:
            parameter = int(parameter)
            if parameter < bound:
                parameter = default_value
        except ValueError:
            parameter = default_value
        return parameter

    @staticmethod
    def parse_upper_bound(parameter, min_bound, max_bound):
        try:
            parameter = int(parameter)
            if not min_bound <= parameter <= max_bound:
                parameter = max_bound
        except ValueError:
            parameter = max_bound
        return parameter

    def write_to_database(self):
        n = self.get_entry_widget_content(self.n_entry)
        k = self.get_entry_widget_content(self.k_entry)
        n = self.parse_params(n, 2, 2)
        k = self.parse_params(k, 0, 5)
        db = self.get_entry_widget_content(self.db_path_entry)
        corpus_path = self.get_entry_widget_content(self.corpus_path_entry)
        try:
            corpus = self.read_file(corpus_path)
        except FileNotFoundError:
            messagebox.showerror("Corpus file error", "Unable to open corpus file\n{}".format(corpus_path))
            return
        ngrams = Ngrams(n, k, corpus, db)
        gt_table = ngrams.gt_table

        lower_bound = self.get_entry_widget_content(self.lower_bound_entry)
        upper_bound = self.get_entry_widget_content(self.upper_bound_entry)
        lower_bound = self.parse_params(lower_bound, 0, 0)
        max_upper_bound = max(list(zip(*gt_table))[0])
        upper_bound = self.parse_upper_bound(upper_bound, lower_bound, max_upper_bound)
        self.set_entry_widget_content(self.n_entry, str(n))
        self.set_entry_widget_content(self.k_entry, str(k))
        self.set_entry_widget_content(self.lower_bound_entry, str(lower_bound))
        self.set_entry_widget_content(self.upper_bound_entry, str(upper_bound))

        self.draw_chart(gt_table[lower_bound:upper_bound + 1])

    def update_chart(self):
        db_path = self.get_entry_widget_content(self.db_path_entry)
        if db_path == "":
            messagebox.showerror("Database file error", "Database path cannot be empty")
            return
        db = Database(db_path, drop=False)
        gt_table = db.load_gt_estimation_data()
        if len(gt_table) == 0:
            messagebox.showerror("Database file error", "Cannot load data from database\n{}".format(db_path))
            return
        lower_bound = self.get_entry_widget_content(self.lower_bound_entry)
        upper_bound = self.get_entry_widget_content(self.upper_bound_entry)
        lower_bound = self.parse_params(lower_bound, 0, 0)
        max_upper_bound = max(list(zip(*gt_table))[0])
        upper_bound = self.parse_upper_bound(upper_bound, lower_bound, max_upper_bound)
        self.set_entry_widget_content(self.lower_bound_entry, str(lower_bound))
        self.set_entry_widget_content(self.upper_bound_entry, str(upper_bound))

        self.draw_chart(gt_table[lower_bound:upper_bound + 1])
