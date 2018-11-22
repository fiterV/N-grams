"""
Після встановлення бібліотеки nltk потрібно також встановити пакет 'punkt', що забезпечує поділ тексту на речення
"""

import nltk

if __name__ == "__main__":
    directory = r"venv\nltk_data"
    nltk.download('punkt', download_dir=directory)
