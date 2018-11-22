class FrequencyChart:
    """
    Клас, що відповідає за побудову графіка частот частот
    """

    @staticmethod
    def chart_draw(f, chart_data):
        """
        Функція відповідає за побудову графіка
        :param f: фігура, що створється на полотні canvas
        :param chart_data: дані для побудови графіка, список списків, де кожний елемент представлений у вигляді  [x,y]
        """
        p = f.add_subplot(111)  # додавання полотна на фігуру, де буде намальовано графік
        p.cla()  # очищення полотна перед малюванням нового графіка
        x = []
        y = []
        for i in range(len(chart_data)):  # розпаковка даних по осях x, y
            x.append(chart_data[i][0])
            y.append(chart_data[i][1])

        x_labels = x.copy()  # підписи осі x - частоти
        p.set_xticks(x_labels)
        y_labels = y.copy()  # підписи осі y - відповідні кількості частот
        p.set_yticks(y_labels)

        p.plot(x, y, 'g-')  # нанесення на графік, точки з'єднуються зеленою лінією
        p.plot(x, y, 'bo')  # нанесення на графік (синій маркер)
        p.fill_between(x, y, 0, color='b', alpha=.1, hatch="/")  # зафарбовування області під графіком
        # Підпис горизонтальної осі
        p.annotate('Frequency', xy=(0.98, 0), ha='left', va='top', xycoords='axes fraction', fontsize=10)
        # Підпис вертикальної осі
        p.annotate('Quantity', xy=(0, 1.03), xytext=(-15, 2), ha='left', va='top', xycoords='axes fraction',
                   textcoords='offset points', fontsize=10)
