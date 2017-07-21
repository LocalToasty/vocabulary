#!/usr/bin/env python3

import random
import pickle
import sys
import json
import time
import heapq
import re

path = ""

class Card:
    def __init__(self, entries, comment):
        self.entries = entries
        self.comment = comment

    def due_entry(self):
        return min(self.entries)

    def due_at(self):
        return min([entry.due for entry in self.entries])

    def is_due(self):
        return time.time() >= self.due_at()

    def __str__(self):
        res = str(self.entries[0])
        for e in self.entries[1:]:
            res += " \t" + str(e)
        if self.comment:
            res += " \t# " + self.comment
        return res

    def __lt__(self, other):
        return self.due_at() < other.due_at()

class Entry:
    def __init__(self, text, proficiency=1, due=None):
        self.text = text
        self.proficiency = proficiency
        if due:
            self.due = due
        else:
            self.due = time.time() + 5 * 60 * random.random()

    def __str__(self):
        return self.text

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
            card = Card([Entry(e["text"], e["proficiency"], e["due"])
                         for e in c["entries"]],
                        c["comment"])
            db.cards.append(card)
        heapq.heapify(db.cards)
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
                "entries": [{
                    "text": entry.text,
                    "proficiency": entry.proficiency,
                    "due": entry.due
                } for entry in card.entries],
                "comment": card.comment,
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
    except FileNotFoundError:
        n = int(input("How many entries per card? "))
        langs = []
        for i in range(n):
            langs.append(input("Name of entry {}: ".format(i)))
        db = Database(langs)

    if db.cards:
        if  db.top().is_due():
            print("Cards ready for repetition")
        else:
            print("Next card ready on", time.asctime(time.localtime(db.top().due_at())))

    while True:
        try:
            choice = input("> ")
        except (KeyboardInterrupt, EOFError):
            break

        try:
            if choice in ["a", "A"]:
                add_card(db)
            if choice in ["r", "R"]:
                remove_card(db)
            elif choice in ["l", "l"]:
                learn(db)
            elif choice in ["f", "F"]:
                find(db)
            elif choice in ["t", "T"]:
                stats(db)
            elif choice in ["s", "S"]:
                save(db)
        except (KeyboardInterrupt, EOFError):
            pass

    print()
    if db.changes and ask_yes_no("Save changes?", default=True):
        save(db)

    if db.cards:
        print("Come back on",
              time.asctime(time.localtime(max(time.time(),
                                              heapq.nsmallest(min(16, len(db.cards)), db.cards)[-1].due_at()))))

def add_card(db):
    try:
        entries = []
        for lang in db.langs:
            entry = Entry(input(lang + ": "))
            entries.append(entry)

        comment = input("Comment: ")
        db.add(Card(entries, comment))

    except (KeyboardInterrupt, EOFError):
        print()
        return None

def remove_card(db):
    content = input("Enter card to remove: ")
    for card in db.cards:
        if content in [e.text for e in card.entries]:
            print("Removed {}".format(card))
            db.cards.remove(card)
            heapq.heapify(db.cards)
            break

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

    # clear screen
    print(chr(27) + "[2J")

    while time.time() < end_time:
        if not db.top().is_due():
            print("Next cards ready on", time.asctime(time.localtime(db.top().due_at())))
            break

        try:
            card = db.pop()
            entry = card.due_entry()
            print(entry, end=" ")
            input()
            print(card)

            if ask_yes_no("Correct?", default=False):
                entry.proficiency = entry.proficiency * 2 + 0.2 * random.random() * (time.time() - entry.due)
            else:
                entry.proficiency = max(entry.proficiency / 128, 1)
            entry.due = time.time() + entry.proficiency
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
    prog = None
    try:
        prog = re.compile(".*" + input("Seach for: "))
    except re.error as e:
        print("Error while compiling regular expression:", e.msg)
        return

    for card in db.cards:
        if any(prog.match(entry.text) for entry in card.entries) or prog.match(card.comment):
            print(time.asctime(time.localtime(card.due_at())), card)


def stats(db):
    print("Total:", len(db.cards))
    cards = db.cards.copy()

    print("Cards Due:")
    n = 0
    while cards and heapq.heappop(cards).is_due():
        n += 1
    print("  Now:          ", n)
    while cards and heapq.heappop(cards).due_at() <= time.time() + 6*60*60:
        n += 1
    print("  In six hours: ", n)
    while cards and heapq.heappop(cards).due_at() <= time.time() + 24*60*60:
        n += 1
    print("  Tomorrow:     ", n)
    while cards and heapq.heappop(cards).due_at() <= time.time() + 2*24*60*60:
        n += 1
    print("  In two days:  ", n)
    while cards and heapq.heappop(cards).due_at() <= time.time() + 3*24*60*60:
        n += 1
    print("  In three days:", n)


def save(db):
    if not db.changes:
        print("No changes to be saved")
        return

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
                json.dump(db, dbfile, cls=DatabaseEncoder, indent=2, ensure_ascii=False)
            break
        except FileNotFoundError:
            pass

    db.changes = False


if __name__ == "__main__":
    main()
