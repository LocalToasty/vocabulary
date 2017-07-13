#!/usr/bin/env python3

import random
import pickle
import sys
import json
import time
import heapq

path = ""

class Card:
    def __init__(self, entries, comment):
        self.entries = entries
        self.comment = comment
        self.proficiency = 0.
        self.due = time.time()

    def is_due(self):
        return time.time() >= self.due

    def __str__(self):
        res = str(self.entries[0])
        for e in self.entries[1:]:
            res += "\t" + e
        if self.comment:
            res += "\t# " + self.comment
        return res

    def __lt__(self, other):
        return self.due < other.due


class Database:
    def __init__(self, langs):
        self.langs = langs
        self.cards = []
        self.changes = False

    def from_dict(dct):
        db = Database(dct["langs"])
        n = 0
        for c in dct["cards"]:
            n += 1
            card = Card(c["entries"], c["comment"])
            card.proficiency = c["proficiency"]
            card.due = c["due"]
            db.cards.append(card)
        heapq.heapify(db.cards)
        print("Loaded", n, "cards")
        return db

    def add(self, card):
        self.changes = True
        heapq.heappush(self.cards, card)

    def pop(self):
        self.changes = True
        return heapq.heappop(self.cards)

    def top(self):
        return self.cards[0]

class DatabaseEncoder(json.JSONEncoder):
    def default(self, db):
        return {
            "langs": db.langs,
            "cards": [{
                "entries": card.entries,
                "comment": card.comment,
                "proficiency": card.proficiency,
                "due": card.due
            } for card in db.cards]
        }


def main():
    if len(sys.argv) != 2:
        print("Usage: {} <file>".format(sys.argv[0]))
        return

    global path
    path = sys.argv[1]

    db = None
    try:
        with open(sys.argv[1], "r") as dbfile:
            db = Database.from_dict(json.load(dbfile))
    except:
        n = int(input("How many entries per card? "))
        langs = []
        for i in range(n):
            langs.append(input("Name of entry {}: ".format(i)))
        db = Database(langs)

    if db.cards:
        if  db.top().is_due():
            print("Cards ready for repetition")
        else:
            print("Next card ready on", time.asctime(time.localtime(db.top().due)))

    while True:
        try:
            choice = input("> ")
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ["a", "A"]:
            add_card(db)
        if choice in ["r", "R"]:
            remove_card(db)
        elif choice in ["q", "q"]:
            learn(db)
        elif choice in ["l", "l"]:
            list_cards(db)
        elif choice in ["f", "F"]:
            find(db)
        elif choice in ["s", "S"]:
            save(db)

    print()
    if db.changes and ask_yes_no("Save changes?", default=True):
        save(db)

    if db.cards:
        print("Come back on",
              time.asctime(time.localtime(max(time.time(),
                                              heapq.nsmallest(min(24, len(db.cards)), db.cards)[-1].due))))

def add_card(db):
    try:
        entries = []
        for lang in db.langs:
            entry = input(lang + ": ")
            entries.append(entry)

        comment = input("Comment: ")
        db.add(Card(entries, comment))

    except (KeyboardInterrupt, EOFError):
        print()
        return None

def remove_card(db):
    content = input("Enter card to remove: ")
    for card in db.cards:
        if content in card.entries:
            print("Removed {}".format(card))
            db.cards.remove(card)
            heapq.heapify(db.cards)

def learn(db):
    if not db.cards or not db.top().is_due():
        print("No cards to learn")
        return

    duration = 0
    while True:
        try:
            duration = float(input("Duration (min): "))
            break
        except ValueError:
            pass

    end_time = time.time() + duration * 60

    while time.time() < end_time:
        if not db.top().is_due():
            print("Next cards ready on", time.asctime(time.localtime(db.top().due)))
            break

        try:
            card = db.pop()
            print(random.choice(card.entries), end=" ")
            input()
            print(card)

            if ask_yes_no("Correct?", default=False):
                card.proficiency = card.proficiency * 1.5 + 0.2 * (time.time() - card.due)
            else:
                card.proficiency = 1
            card.due = time.time() + card.proficiency
            db.add(card)
        except (KeyboardInterrupt, EOFError):
            db.add(card)
            break


def ask_yes_no(question, default):
    print(question, end=" ")
    if default:
        print("[Y/n]: ", end="")
    else:
        print("[y/N]: ", end="")
    answer = input()
    if answer in ["y", "Y"]: return True
    elif answer in ["n", "N"]: return False
    else: return default


def find(db):
    keyword = input("Seach for: ")
    for card in db.cards:
        if any(keyword in entry for entry in card.entries) or keyword in card.comment:
            print(time.asctime(time.localtime(card.due)), card)

def list_cards(db):
    cards = db.cards.copy()
    while cards:
        card = heapq.heappop(cards)
        print(time.asctime(time.localtime(card.due)), card)


def save(db):
    global path
    while True:
        try:
            if path:
                new_path = input("Save as [" + path + "]: ")
                if new_path:
                    path = new_path
            else:
                path = input("Save as: ")

            with open(path, "w") as dbfile:
                dbfile.write(json.dumps(db, cls=DatabaseEncoder, indent=2))
            break
        except FileNotFoundError:
            pass

    db.changes = False


if __name__ == "__main__":
    main()
