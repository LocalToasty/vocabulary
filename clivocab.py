#!/usr/bin/python3

from vocabulary import *
import sys
import random
import re
from math import log
from typing import Optional

class VocabularyApp:
    def __init__(self) -> None:
        if len(sys.argv) != 2:
            print("Usage: {} <file>".format(sys.argv[0]))
            return

        global path
        self.path = sys.argv[1]


    def run(self) -> None:
        self.db = None # type: Optional[Database]
        try:
            self.db = Database.load(self.path)
        except FileNotFoundError:
            n = int(input("How many entries per card? "))
            langs = []
            for i in range(n):
                langs.append(input("Name of entry {}: ".format(i)))
            self.db = Database(langs)

        if self.db.cards:
            if self.db.top().is_due():
                print("Cards ready for repetition")
            else:
                print("Next card ready on", time.asctime(time.localtime(self.db.top().due_at())))

        while True:
            try:
                choice = input("> ")
            except (KeyboardInterrupt, EOFError):
                break

            try:
                if choice in ["a", "A"]:
                    self.add_card()
                if choice in ["r", "R"]:
                    self.remove_card()
                elif choice in ["l", "l"]:
                    self.learn()
                elif choice in ["f", "F"]:
                    self.find()
                elif choice in ["t", "T"]:
                    self.stats()
                elif choice in ["s", "S"]:
                    self.save()
            except (KeyboardInterrupt, EOFError):
                pass

        print()
        if self.db.changes and ask_yes_no("Save changes?", exact=False, default=True):
            self.save()

    def add_card(self) -> None:
        try:
            entries = [] # type: List[Entry]
            for lang in self.db.langs:
                text = input(lang + ": ")
                if text == '"""':
                    text = multiline_input()
                entries.append(Entry(text))
    
            comment = input("Comment: ")
            self.db.add(Card(entries, comment))
    
        except (KeyboardInterrupt, EOFError):
            print()
            return
    
    
    def remove_card(self) -> None:
        content = input("Enter card to remove: ")
        for card in self.db.cards:
            if content in [e.text for e in card.entries]:
                print("Removed {}".format(card))
                self.db.cards.remove(card)
                heapq.heapify(self.db.cards)
                self.db.changes = True
                break
    
    def learn(self) -> None:
        if not self.db.cards or not self.db.top().is_due():
            print("No cards to learn")
            return
    
        duration = 0.
        while True:
            try:
                duration = float(input("Duration (min): "))
                break
            except ValueError:
                pass
    
        end_time = time.time() + duration * 60
        i = 0
    
        while time.time() < end_time:
            if not self.db.top().is_due():
                return
    
            try:
                card = self.db.pop()
                i += 1
                entry = card.due_entry()
    
                print(chr(27) + "[2J")
                print(entry, end=" ")
                input()
                print(chr(27) + "[2J")
                card.print()
    
                correct = ask_yes_no("Correct?")
                self.db.retention[1] += entry.proficiency
                if correct:
                    self.db.retention[0] += entry.proficiency
                    entry.proficiency = 1.75 * entry.proficiency + random.random() * 3600 * log((time.time() - entry.due)/3600 * 0.125 + 1) * 24 / log(24*0.125 + 1)
                    entry.due = time.time() + entry.proficiency
                else:
                    entry.proficiency = max(entry.proficiency / 16, 60.)
                    self.db.retention[0] += entry.proficiency
                    entry.due = time.time() + 60
                self.db.add(card)
            except (KeyboardInterrupt, EOFError):
                self.db.add(card)
                break
        print(i)
    
    def find(self) -> None:
        prog = None
        try:
            prog = re.compile(".*" + input("Seach for: "))
        except re.error as e:
            print("Error while compiling regular expression:", e.msg)
            return
    
        for card in self.db.cards:
            if any(prog.match(entry.text) for entry in card.entries) or prog.match(card.comment):
                print(time.asctime(time.localtime(card.due_at())), card)
    
    def stats(self) -> None:
        print("Total:", len(self.db.cards))
    
        print("Retention score:", 100 * self.db.retention[0]/self.db.retention[1])
    
        #cards = self.db.cards.copy()
        #n = 0
        #while cards and heapq.heappop(cards).is_due():
        #    n += 1
        #print("Cards due:", n)
    
    def save(self) -> None:
        if not self.db.changes:
            print("No changes to be saved")
            return
    
        while True:
            try:
                if self.path:
                    new_path = input("Save as [" + self.path + "]: ")
                    if new_path:
                        self.path = new_path
                else:
                    self.path = input("Save as: ")
    
                if self.db.rethist and self.db.rethist[-1][0] + 60*60 < time.time():
                    self.db.rethist += [[time.time(), self.db.retention[0]/self.db.retention[1]]]
    
                self.db.save(self.path)
                break
            except FileNotFoundError:
                pass
    
        self.db.changes = False
    
    
def multiline_input() -> str:
    inp = input()
    res = ""
    while inp != '"""':
        res += inp + "\n"
        inp = input()

    return res


def ask_yes_no(question: str, exact: bool = True, default: bool = True) -> bool:
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
    

if __name__ == "__main__":
    app = VocabularyApp()
    app.run()
