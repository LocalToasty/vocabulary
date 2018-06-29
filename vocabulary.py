#!/usr/bin/env python3

import random
import sys
import json
import time
import heapq
from typing import List


# current version [major, minor, patch, others]
version = [2, 2, 0, "develop"]


class Entry:
    def __init__(self, text: str, proficiency: float = 60, due: float = None) -> None:
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


class Card:
    def __init__(self, entries: List[Entry], comment: str) -> None:
        self.entries = entries
        self.comment = comment
        self.added = time.time()

    def due_entry(self) -> Entry:
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


class Database:
    def __init__(self, langs: List[str]) -> None:
        """Creates a new database.

        Keyword arguments:
        langs -- titles of the card sides.
        """
        self.langs = langs
        self.cards = []  # type: List[Card]
        self.changes = True

        self.retention = [1., 1.]
        self.rethist = []  # type: List[List[float]]

        # maximum number of cards active a every time
        self.maxcards = 32

    def load(filename: str):
        with open(filename, "r", encoding="utf-8") as dbfile:
            return Database.from_dict(json.load(dbfile))

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as dbfile:
            json.dump(self, dbfile, cls=DatabaseEncoder, indent=2,
                      ensure_ascii=False)

    def from_dict(dct):
        global version
        # check for potential version incompatabilities
        if "version" in dct and dct["version"][:2] > version[:2]:
            print("Warning: The loaded file was created with a newer version "
                  "({} > {}). Saving might lead to data loss."
                  .format(".".join(map(str, dct["version"])),
                          ".".join(map(str, version))))

        db = Database(dct["langs"])
        db.changes = False
        db.retention = dct["retention"]

        if "rethist" in dct:
            db.rethist = dct["rethist"]

        if "maxcards" in dct:
            db.maxcards = dct["maxcards"]

        for c in dct["cards"]:
            card = Card([Entry(e["text"], e["proficiency"], e["due"])
                         for e in c["entries"]],
                        c["comment"])
            if "added" in c:
                card.added = c["added"]
            db.cards.append(card)
        heapq.heapify(db.cards)

        if len(db.cards) > db.maxcards:
            cards = heapq.nsmallest(db.maxcards, db.cards)
            if cards[-1].is_due():
                off = time.time() - cards[-1].due_at()
                for card in db.cards:
                    for entry in card.entries:
                        if entry.due > cards[-1].due_at():
                            entry.due += off
        return db

    def add(self, card: Card):
        self.changes = True
        heapq.heappush(self.cards, card)

    def pop(self):
        self.changes = True
        return heapq.heappop(self.cards)

    def top(self):
        return self.cards[0]


class DatabaseEncoder(json.JSONEncoder):
    def default(self, db):
        global version
        return {
            "langs": db.langs,
            "version": version,
            "retention": db.retention,
            "rethist": db.rethist,
            "maxcards": db.maxcards,
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
