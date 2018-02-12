#!/usr/bin/python3

import sys
import random
import time
import re
from datetime import datetime
from math import log
import vocabulary as vocab
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from typing import List, Optional


class VocabularyApp(QMainWindow):
    def __init__(self, filename: str = '') -> None:
        super().__init__()

        self.filename = filename
        self.db_model = DatabaseModel()

        self.init_ui()
        self.load_db()

        if self.db:
            self.enable_view()

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
        #self.search_field.textEdited.connect(self.update_vocab)

        vocab_view = QTableView()
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.db_model)
        vocab_view.setModel(proxy_model)
        vocab_view.setSortingEnabled(True)

        add_button = QPushButton('&Add')
        add_button.clicked.connect(self.add)

        learn_button = QPushButton('&Learn')
        learn_button.clicked.connect(self.learn)

        buttons = QVBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(learn_button)
        buttons.addStretch(1)

        buttons_and_vocab = QHBoxLayout()
        buttons_and_vocab.addWidget(vocab_view)
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

    def load_db(self):
        if not self.filename:
            return
        
        self.db_model.load(self.filename)
        self.enable_view()

    def enable_view(self):
        self.main_widget.setEnabled(True)
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)

    def open(self, filename:str = ''):
        filename = QFileDialog.getOpenFileName(self, 'Open Vocabulary Database', '', 'JSON files (*.json);;All Files (*)')[0]
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
        filename = QFileDialog.getSaveFileName(self, 'Save Vocabulary Database As', 'vocabulary.json', 'JSON file (*.json)')[0]
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
            self.db_model.add(d.card)

    def learn(self, event):
        if not self.db.cards or not self.db.top().is_due():
            QMessageBox.information(self, 'No Cards to Learn',
                                    'There are currently no cards to learn.')
            return

        LearnDialog(self.db, self).exec_()
        self.db_model.layoutChanged.emit()

    @property
    def db(self):
        return self.db_model.db


class NewDatabaseDialog(QDialog):
    def __init__(self, parent: QObject = None):
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
        self.db_model.db = vocab.Database([lang.text() for lang in self.langs[:self.langno.value()]])

        self.accept()


class AddDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle('Add New Card')

        entry_layout = QGridLayout()

        self.entries = []

        for row, lang in enumerate(parent.db_model.db.langs + ["Comment"]):
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


class DatabaseModel(QAbstractTableModel):
    def __init__(self, db: vocab.Database=None, parent: QObject = None) -> None:
        super().__init__(parent)
        self._db = db

    def add(self, card: vocab.Card) -> None:
        self._db.add(card)
        self.layoutChanged.emit()

    def remove(self, card: vocab.Card) -> None:
        self._db.remove(card)
        self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex) -> int:
        if self._db:
            return len(self._db.cards)
        else:
            return 0

    def columnCount(self, parent: QModelIndex) -> int:
        if self._db:
            return len(self._db.langs) + 3   # 3 ^= comment, added, due
        else:
            return 0

    def load(self, filename: str) -> None:
        self._db = vocab.Database.load(filename)
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int):
        if not self._db:
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            card = self._db.cards[index.row()]
            if index.column() < len(self._db.langs):
                return card.entries[index.column()].text
            elif index.column() == len(self._db.langs):
                return card.comment
            elif index.column() == len(self._db.langs) + 1:
                return datetime.fromtimestamp(card.added).isoformat(' ', 'minutes')
            elif index.column() == len(self._db.langs) + 2:
                return datetime.fromtimestamp(card.due_at()).isoformat(' ', 'minutes')

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Optional[str]:
        if not self._db or orientation == Qt.Vertical:
            return None
        
        if role == Qt.DisplayRole:
            if section < len(self._db.langs):
                return self._db.langs[section]
            elif section == len(self._db.langs):
                return 'Comment'
            elif section == len(self._db.langs) + 1:
                return 'Added'
            elif section == len(self._db.langs) + 2:
                return 'Due'

        return None

    def setData(self, index: QModelIndex, value, role: int) -> bool:
        card = self._db.cards[index.row()]

        if role == Qt.EditRole:
            if index.column() < len(self._db.langs):
                card.entries[index.column()].text = value
            elif index.column() == len(self._db.langs):
                card.comment = value
            
            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        card = self._db.cards[index.row()]

        if index.column() <= len(self._db.langs):  # includes comment field
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled

    @property
    def db(self):
        return self._db


class LearnDialog(QDialog):
    def __init__(self, db: vocab.Database, parent: QObject = None) -> None:
        super().__init__(parent)

        self.db = db

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
        if not self.db.top().is_due():
            self.accept()
            return
        
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
        if self.card:
            self.db.add(self.card)
            self.card = None

def arg_min(xs):
    mx = xs[0]
    mi = 0
    for i, x in enumerate(xs[1:]):
        if x < mx: mx, mi = x, i+1

    return mi


if __name__ == '__main__':
    app = QApplication(sys.argv)

    filename = ''
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    vocab_app = VocabularyApp(filename)
    sys.exit(app.exec_())
