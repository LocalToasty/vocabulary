#!/usr/bin/python3

import sys
import random
import time
import re
from datetime import datetime
from math import log
import vocabulary as vocab
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QKeySequence
from typing import List, Optional

class VocabularyApp(QMainWindow):
    def __init__(self, filename: str = '') -> None:
        super().__init__()

        self.filename = filename
        self.init_ui()
        self.load_db()

    def init_ui(self) -> None:
        new_action = QAction('&New', self)
        new_action.setShortcuts(QKeySequence.New)
        new_action.triggered.connect(self.new)

        open_action = QAction('&Open', self)
        open_action.setShortcuts(QKeySequence.Open)
        open_action.triggered.connect(self.open)

        self.save_action = QAction('&Save', self)
        self.save_action.setEnabled(False)
        self.save_action.setShortcuts(QKeySequence.Save)
        self.save_action.triggered.connect(self.save)

        self.save_as_action = QAction('Save &As', self)
        self.save_as_action.setEnabled(False)
        self.save_as_action.setShortcuts(QKeySequence.SaveAs)
        self.save_as_action.triggered.connect(self.save_as)

        quit_action = QAction('&Quit', self)
        quit_action.setShortcuts(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)

        menubar = self.menuBar()
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(new_action)
        filemenu.addAction(open_action)
        filemenu.addAction(self.save_action)
        filemenu.addAction(self.save_as_action)
        filemenu.addAction(quit_action)

        self.search_field = QLineEdit()
        self.search_field.textEdited.connect(self.update_vocab)

        self.vocab_table = QTableWidget()
        self.vocab_table.cellClicked.connect(self.update_current_card)
        current_card = None

        self.vocab_table.verticalHeader().hide()

        add_button = QPushButton('&Add')
        add_button.clicked.connect(self.add)

        learn_button = QPushButton('&Learn')
        learn_button.clicked.connect(self.learn)

        buttons = QVBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(learn_button)
        buttons.addStretch(1)

        buttons_and_vocab = QHBoxLayout()
        buttons_and_vocab.addWidget(self.vocab_table)
        buttons_and_vocab.addLayout(buttons)

        layout = QVBoxLayout()
        layout.addWidget(self.search_field)
        layout.addLayout(buttons_and_vocab)

        self.main_widget = QWidget()
        self.main_widget.setLayout(layout)
        self.main_widget.setEnabled(False)
        self.setCentralWidget(self.main_widget)
        self.setWindowTitle('Vocabulary')
        self.show()


    def new(self):
        d = NewDatabaseDialog(self)
        if d.exec_():
            self.db = d.db
            self.setup_view()


    def load_db(self):
        if not self.filename:
            self.db = None
            return
        
        self.db = vocab.Database.load(self.filename)

        self.setup_view()


    def setup_view(self):
        cols = len(self.db.langs) + 3
        self.vocab_table.setColumnCount(cols)
        self.vocab_table.setHorizontalHeaderLabels(self.db.langs + ["Comment", "Added", "Due"])

        self.enable_view()


    def enable_view(self):
        self.vocab_table.sortItems(len(self.db.langs) + 1, 1)

        self.refresh_view()

        self.main_widget.setEnabled(True)
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)


    def refresh_view(self):
        self.update_vocab(self.search_field.text())
        

    def update_vocab(self, query=''):
        self.vocab_table.setSortingEnabled(False)
        cards = []

        try:
            regex = re.compile('.*' + query)
        except re.error as e:
            return
    
        for card in self.db.cards:
            if any(regex.match(entry.text) for entry in card.entries) or regex.match(card.comment):
                cards += [card]

        self.vocab_table.setRowCount(len(cards))

        for row, card in enumerate(cards):
            self.vocab_table.setItem(row, len(self.db.langs), QTableWidgetItem(card.comment))
            self.vocab_table.setItem(row, len(self.db.langs) + 1, QTableWidgetItem(datetime.fromtimestamp(card.added).isoformat(' ', 'minutes')))
            self.vocab_table.setItem(row, len(self.db.langs) + 2, QTableWidgetItem(datetime.fromtimestamp(card.due_at()).isoformat(' ', 'minutes')))

            for col, entry in enumerate(card.entries):
                self.vocab_table.setItem(row, col, QTableWidgetItem(entry.text))

        self.vocab_table.setSortingEnabled(True)


    def open(self, filename:str = ''):
        filename = QFileDialog.getOpenFileName(self, 'Open Vocabulary Database')[0]
        if filename:
            self.filename = filename
            self.load_db()

    def save(self):
        if not self.filename:
            return self.save_as()
        else:
            self.db.save(self.filename)
            return True

    def save_as(self):
        filename = QFileDialog.getSaveFileName(self, 'Save Vocabulary Database As')[0]
        if filename:
            self.filename = filename
            self.db.save(filename)
        else:
            return False

    def closeEvent(self, event):
        if self.db and self.db.changes:
            res = QMessageBox.warning(self, 'Unsaved Changes',
                                      'There are unsaved changes. Do you want to save?',
                                      QMessageBox.Discard | QMessageBox.Cancel | QMessageBox.Save,
                                      QMessageBox.Cancel)
            if res == QMessageBox.Discard or (
                    res == QMessageBox.Save and self.save()):
                event.accept()
            else:
                event.ignore()

    def add(self, event):
        d = AddDialog(self)
        if d.exec_():
            self.db.add(d.card)

        self.refresh_view()

    def learn(self, event):
        if not self.db.cards or not self.db.top().is_due():
            QMessageBox.information(self, 'No Cards to Learn',
                                    'There are currently no cards to learn.')
            return

        LearnDialog(self).exec_()
        self.refresh_view()

    def update_current_card(self, x: int, y: int) -> None:
        pass


def find_closest(entries: List[str], db: vocab.Database) -> Optional[vocab.Card]:
    for card in db.cards:
        if all([entries[i] == card.entries[i].text]):
            return card
    return None


class NewDatabaseDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle('Create New Database')


        label = QLabel('Number of sides:')
        self.langno = langno = QSpinBox()
        langno.valueChanged.connect(self.change_language_no)

        entry_layout = QHBoxLayout()
        entry_layout.addWidget(label)
        entry_layout.addWidget(langno)

        self.langs = []
        self.lang_layout = QVBoxLayout()

        create_button = QPushButton('&Create', self)
        create_button.clicked.connect(self.make_database)
        create_button.setDefault(True)

        cancel_button = QPushButton('&Cancel', self)
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel_button)
        buttons.addWidget(create_button)

        layout = QVBoxLayout()
        layout.addLayout(entry_layout)
        layout.addLayout(self.lang_layout)
        layout.addStretch(1)
        layout.addLayout(buttons)

        self.setLayout(layout)


    def change_language_no(self, no):
        if no > len(self.langs):
            for i in range(no - len(self.langs)):
                self.langs += [QLineEdit()]
                self.lang_layout.addWidget(self.langs[-1])
        elif no < len(self.langs):
            pass #TODO


    def make_database(self):
        self.db = vocab.Database([lang.text() for lang in self.langs[:self.langno.value()]])

        self.accept()


class AddDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle('Add New Card')

        entry_layout = QGridLayout()

        self.entries = []

        for row, lang in enumerate(parent.db.langs + ["Comment"]):
            entry_layout.addWidget(QLabel(lang + ':'), row, 0)
            self.entries += [QLineEdit(self)]
            entry_layout.addWidget(self.entries[-1], row, 1)

        self.entries[0].setFocus(True)

        ok_button = QPushButton('&Add', self)
        ok_button.clicked.connect(self.make_card)
        ok_button.setDefault(True)

        cancel_button = QPushButton('&Cancel', self)
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel_button)
        buttons.addWidget(ok_button)

        layout = QVBoxLayout()
        layout.addLayout(entry_layout)
        layout.addStretch(1)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def make_card(self):
        self.card = vocab.Card(
            [vocab.Entry(x.text()) for x in self.entries[:-1]],
            self.entries[-1].text())

        self.accept()


class LearnDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.db = parent.db

        self.setWindowTitle('Learn')

        entry_layout = QGridLayout()

        self.entries = []

        for row, lang in enumerate(parent.db.langs + ["Comment"]):
            entry_layout.addWidget(QLabel(lang + ':'), row, 0)
            self.entries += [QLabel(self)]
            entry_layout.addWidget(self.entries[-1], row, 1)

        self.reveal_button = QPushButton('&Show', self)
        self.reveal_button.clicked.connect(self.reveal)
        self.reveal_button.setFocus(True)

        self.correct_label = QLabel('Correct?')

        self.yes_button = QPushButton('&Yes')
        self.yes_button.clicked.connect(self.correct)

        self.no_button = QPushButton('&No')
        self.no_button.clicked.connect(self.incorrect)

        buttons = QHBoxLayout()
        buttons.addWidget(self.correct_label)
        buttons.addStretch(1)
        buttons.addWidget(self.yes_button)
        buttons.addWidget(self.no_button)
        buttons.addWidget(self.reveal_button)

        layout = QVBoxLayout()
        layout.addLayout(entry_layout)
        layout.addStretch(1)
        layout.addLayout(buttons)

        self.setLayout(layout)

        self.finished.connect(self.put_back_card)
        self.next_card()

    def next_card(self):
        if not self.db.top().is_due(): self.accept()
        
        self.correct_label.hide()
        self.yes_button.hide()
        self.no_button.hide()
        self.reveal_button.show()
        self.reveal_button.setFocus(True)

        for entry in self.entries:
            entry.clear()

        self.card = self.db.pop()
        i = arg_min(self.card.entries)
        self.entry = self.card.entries[i]
        self.entries[i].setText(self.entry.text)

    def reveal(self):
        self.reveal_button.hide()
        self.correct_label.show()
        self.yes_button.show()
        self.yes_button.setFocus(True)
        self.no_button.show()
        
        self.entries[-1].setText(self.card.comment)
        for i, entry in enumerate(self.card.entries):
            self.entries[i].setText(entry.text)

    def correct(self):
        self.db.retention[1] += self.entry.proficiency
        self.db.retention[0] += self.entry.proficiency
        self.entry.proficiency = self.entry.proficiency * 2 + random.random() * 3600 * log((time.time() - self.entry.due)/3600 * 0.125 + 1) * 24 / log(24*0.125 + 1)
        self.entry.due = time.time() + self.entry.proficiency
        self.put_back_card()
        self.next_card()

    def incorrect(self):
        self.db.retention[1] += self.entry.proficiency
        self.entry.proficiency = max(self.entry.proficiency / 16, 60.)
        self.db.retention[0] += self.entry.proficiency
        self.entry.due = time.time() + self.entry.proficiency
        self.put_back_card()
        self.next_card()

    def put_back_card(self):
        self.db.add(self.card)


def arg_min(xs):
    mx = xs[0]
    mi = 0
    for i, x in enumerate(xs[1:]):
        if x < mx: mx, mi = x, i+1

    return mi


if __name__ == '__main__':
    app = QApplication(sys.argv)

    filename = ''
    if sys.argv[1]:
        filename = sys.argv[1]

    vocab_app = VocabularyApp(filename)
    sys.exit(app.exec_())
