#!/usr/bin/env python3

import random
import pickle
import sys
import json
import time
import heapq
import re
from math import log

path = ""

class Card:
    def __init__(self, entries, comment):
        self.entries = entries
        self.comment = comment
        self.added = time.time()

    def due_entry(self):
        return min(self.entries)

    def due_at(self):
        return min([entry.due for entry in self.entries])

    def is_due(self):
        return time.time() >= self.due_at()

    def print(self):
        for e in self.entries:
            print(e)
        if self.comment:
            print(self.comment)

    def __str__(self):
        res = str(self.entries[0])
        for e in self.entries[1:]:
            res += " \t" + str(e)
        if self.comment:
            res += " \t# " + self.comment
        return res

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return self.due_at() < other.due_at()

class Entry:
    def __init__(self, text, proficiency=60, due=None):
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
        self.changes = True

        self.retention = [1., 1.]
        self.rethist = []

    def load(filename):
        with open(filename, "r") as dbfile:
            return Database.from_dict(json.load(dbfile))

    def save(self, filename):
        with open(filename, "w") as dbfile:
            json.dump(self, dbfile, cls=DatabaseEncoder, indent=2, ensure_ascii=False)

    def from_dict(dct):
        db = Database(dct["langs"])
        db.changes = False
        db.retention = dct["retention"]
        if "rethist" in dct: db.rethist = dct["rethist"]
        for c in dct["cards"]:
            card = Card([Entry(e["text"], e["proficiency"], e["due"])
                         for e in c["entries"]],
                        c["comment"])
            if "added" in c:
                card.added = c["added"]
            db.cards.append(card)
        heapq.heapify(db.cards)

        if len(db.cards) > 64:
            cards = heapq.nsmallest(64, db.cards)
            if cards[-1].is_due():
                off = time.time() - cards[-1].due_at()
                for card in db.cards:
                    for entry in card.entries:
                        if entry.due > cards[-1].due_at():
                            entry.due += off
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
            "retention": db.retention,
            "rethist": db.rethist,
            "cards": sorted([{
                "entries": [{
                    "text": entry.text,
                    "proficiency": entry.proficiency,
                    "due": entry.due
                } for entry in card.entries],
                "added": card.added,
                "comment": card.comment,
            } for card in db.cards],
                            key=lambda x: x['added'])
        }


def main():
    if len(sys.argv) != 2:
        print("Usage: {} <file>".format(sys.argv[0]))
        return

    global path
    path = sys.argv[1]

    db = None
    try:
        db = Database.load(path)
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
    if db.changes and ask_yes_no("Save changes?", exact=False, default=True):
        save(db)


def add_card(db):
    try:
        entries = []
        for lang in db.langs:
            text = input(lang + ": ")
            if text == '"""':
                text = multiline_input()
            entries.append(Entry(text))

        comment = input("Comment: ")
        db.add(Card(entries, comment))

    except (KeyboardInterrupt, EOFError):
        print()
        return None


def multiline_input():
    inp = input()
    res = ""
    while inp != '"""':
        res += inp + "\n"
        inp = input()

    return res


def remove_card(db):
    content = input("Enter card to remove: ")
    for card in db.cards:
        if content in [e.text for e in card.entries]:
            print("Removed {}".format(card))
            db.cards.remove(card)
            heapq.heapify(db.cards)
            db.changes = True
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

    while time.time() < end_time:
        if not db.top().is_due():
            return

        try:
            card = db.pop()
            entry = card.due_entry()

            print(chr(27) + "[2J")
            print(entry, end=" ")
            input()
            print(chr(27) + "[2J")
            card.print()

            correct = ask_yes_no("Correct?")
            db.retention[1] += entry.proficiency
            if correct:
                db.retention[0] += entry.proficiency
                entry.proficiency = entry.proficiency * 2 + random.random() * 3600 * log((time.time() - entry.due)/3600 * 0.125 + 1) * 24 / log(24*0.125 + 1)
            else:
                entry.proficiency = max(entry.proficiency / 16, 60.)
                db.retention[0] += entry.proficiency
            entry.due = time.time() + entry.proficiency
            db.add(card)
        except (KeyboardInterrupt, EOFError):
            db.add(card)
            break


def ask_yes_no(question, exact=True, default=True):
    while True:
        print(question, end=" ")
        if exact:
            print("[y/n]: ", end="")
        elif default:
            print("[Y/n]: ", end="")
        else:
            print("[y/N]: ", end="")

        answer = input()
        if answer in ["y", "Y"]: return True
        elif answer in ["n", "N"]: return False
        elif not exact and answer is "": return default


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

    print("Retention score:", 100 * db.retention[0]/db.retention[1])

    #cards = db.cards.copy()
    #n = 0
    #while cards and heapq.heappop(cards).is_due():
    #    n += 1
    #print("Cards due:", n)


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

            if db.rethist and db.rethist[-1][0] + 60*60 < time.time():
                db.rethist += [[time.time(), db.retention[0]/db.retention[1]]]

            db.save(path)
            break
        except FileNotFoundError:
            pass

    db.changes = False


if __name__ == "__main__":
    main()
