#!/usr/bin/env python3

import random
import numpy.random
import pickle

class Card:
    def __init__(self, words, comment):
        self.words = words
        self.comment = comment

    def __str__(self):
        res = self.words[0]

        for lang in self.words[1:]:
            res += "\t{}".format(lang)

        if self.comment:
            res += "\t\t# " + self.comment

        return res

class Database:
    """Contains multiple words."""
    def __init__(self, langs):
        self.langs = langs
        self.categories = [set()]

    def __len__(self):
        return self.no_of_cards_easier_than(0)

    def no_of_cards_easier_than(self, difficulty):
        length = 0
        for category in self.categories[difficulty:]:
            length += len(category)

        return length

    def add_card(self, word):
        """Adds a new word to the data base.

        The word is given a difficulty of 0 (i.e. unknown)."
        """
        self.categories[0].add(word)

    def update(self, correct, incorrect):
        if len(correct) == len(self.categories) and correct[:-1]:
            self.categories += [set()]

        for difficulty, words in enumerate(correct):
            self.categories[difficulty] -= words
            self.categories[difficulty + 1].update(words)

        for difficulty, words in enumerate(incorrect[1:]):
            self.categories[difficulty + 1] -= words
            self.categories[0].update(words)


def main():
    main_menu(None)


def load_database(path):
    database = None
    with open(path, "rb") as dbfile:
        database = pickle.load(dbfile)

    return database


def main_menu(database):
    print("Vocabulary training program")

    while True:
        if database is None:
            print("[C]reate new database")
            print("[L]oad existing database")
            print("[Q]uit")

            answer = input("Select an option: ")

            if answer in ['C', 'c']:
                database = promt_for_database()

            elif answer in ['L', 'l']:
                path = input("Enter database location: ")
                database = load_database(path)
                if database is None:
                    print("Failed to load database")

            elif answer in ['Q', 'q']:
                break

        else:
            print("[A]dd new card")
            print("[R]emove a card")
            print("Take a qui[z]")
            print("[L]ist words")
            print("[F]ind words")
            print("S[t]atistics")
            print("[S]ave database")
            print("[C]lose database")
            print("[Q]uit")

            answer = input("Select an option: ")

            if answer in ['A', 'a']:
                word = promt_for_card(database.langs)
                database.add_card(word)

            if answer in ['R', 'r']:
                promt_remove_card(database)

            elif answer in ['Z', 'z']:
                take_quiz(database)

            elif answer in ['L', 'l']:
                for difficulty, category in enumerate(database.categories):
                    print("### Difficulty {} ###".format(difficulty))
                    for card in category:
                        print(card)

            elif answer in ['F', 'f']:
                keyword = input("Enter term to search for: ")
                for difficulty, category in enumerate(database.categories):
                    for card in category:
                        if any(keyword in word for word in card.words) or keyword in card.comment:
                            print(card)

            elif answer in ['T', 't']:
                print_statistics(database)

            elif answer in ['S', 's']:
                path = input("Save database as: ")
                with open(path, "wb") as dbfile:
                    pickle.dump(database, dbfile)

            elif answer in ['C', 'c']:
                database = None

            elif answer in ['Q', 'q']:
                break


def promt_for_database():
    lang_no = int(input("How many languages? "))
    langs = []
    for i in range(lang_no):
        lang = input("Enter name of language {}: ".format(i + 1))
        langs += [lang]

    return Database(langs)


def promt_for_card(langs):
    words = []
    for lang in langs:
        word = input("Enter your word in {}: ".format(lang))
        words.append(word)

    comment = input("Enter comment: ")
    return Card(words, comment)


def promt_remove_card(database):
    content = input("Enter card to remove: ")
    to_remove = None
    for category in database.categories:
        for card in category:
            if content in card.words:
                to_remove = (category, card)

    if to_remove is not None:
        category, card = to_remove
        print("Removed {}".format(card))
        category.remove(card)


def take_quiz(database):
    length = int(input("How many words should the quiz contain? "))
    quiz = make_quiz(database.categories, length)
    correct, incorrect = do_quiz(database, quiz)
    database.update(correct, incorrect)


def make_quiz(words, length):
    """Selects words for a quiz.

    words -- a list containing sets of words to form the quiz from
    n     -- length of questions in the quiz

    `words` is a list of sets of words, where `words[0]` contains words which
    the trainee is most inexperienced with, `words[1]` those they know better,
    and so forth.  The final quiz will contain n/(i+1) words from the list
    `words[i]`.

    If there are not enough words of a certain difficulty, words from the next
    harder one will be selected.

    """

    if not words or length == 0:
        return []

    # number of words from the list `words[0]`
    words_from_this_category = min(numpy.random.binomial(length, 0.5), len(words[0]))
    # number of words from the lists `words[1:]`
    words_from_other_categories = length - words_from_this_category

    quiz = [random.sample(words[0], words_from_this_category)]
    quiz += make_quiz(words[1:], words_from_other_categories)

    return quiz


def do_quiz(database, quiz):
    print("Which language should be shown?")
    for i, lang in enumerate(database.langs):
        print("{}: {}".format(i, lang))

    from_lang = int(input("> "))
        
    correct = [set() for _ in range(len(quiz))]
    incorrect = [set() for _ in range(len(quiz))]

    for difficulty, cards in enumerate(quiz):
        for question in cards:
            print(question.words[from_lang])

            input("Press [enter] to show solution")
            print(question)

            res = input("Did you answer correctly? [y/N] ")
            if res in ['Y', 'y']:
                correct[difficulty].add(question)
            else:
                incorrect[difficulty].add(question)

    print("{}/{} answered correctly".format(flat_len(correct), flat_len(correct) + flat_len(incorrect)))

    return (correct, incorrect)


def flat_len(xss):
    return sum([len(xs) for xs in xss])


def print_statistics(database):
    for difficulty, category in enumerate(database.categories):
        print("{}:\t{}\twords".format(difficulty, len(category)))

    print("total:\t{}\twords".format(len(database)))


main()
