#!/usr/bin/python3

from vocabulary import *
import sys
import random
import re
import readline
from math import log
from typing import Optional


class VocabularyApp:
    def run(self) -> None:
        if len(sys.argv) < 2:
            print("Usage: {} <file> [command]".format(sys.argv[0]))
            print("")
            print("[command] is one of the following:")
            usage()
            return

        self.path = sys.argv[1]
        self.db = None  # type: Optional[Database]
        # Load database from file, or create new one if file does not exist
        try:
            self.db = Database.load(self.path)
        except FileNotFoundError:
            n = int(input("How many entries per card? "))
            langs = []
            for i in range(n):
                langs.append(input("Name of entry {}: ".format(i)))
            self.db = Database(langs)

        if len(sys.argv) >= 3:
            # execute command line arguments
            command = ' '.join(sys.argv[2:])
            try:
                self.parse_execute_command(command)
            except (KeyboardInterrupt, EOFError):
                pass
            if self.db.changes:
                self.save()
            return

        # check if any cards are ready
        if self.db.cards:
            if self.db.top().is_due():
                print("Cards ready for repetition")
            else:
                print("Next card ready on",
                      time.asctime(time.localtime(self.db.top().due_at())))

        # main menu loop
        while True:
            try:
                command = input("> ")
            except (KeyboardInterrupt, EOFError):
                # quit loop on ^C, ^D
                break

            try:
                self.parse_execute_command(command)
            except (KeyboardInterrupt, EOFError):
                pass

        print()
        if self.db.changes and ask_yes_no("Save changes?",
                                          exact=False, default=True):
            self.save()

    def parse_execute_command(self, command: str) -> None:
        tokens = command.lstrip().split(' ', 1)
        command = tokens[0]
        operands = tokens[1] if len(tokens) == 2 else ""

        if command in ["add", "a"]:
            self.add_card()
        elif command in ["remove", "r"]:
            self.remove_card(operands)
        elif command in ["learn", "l"]:
            duration = 0.
            try:
                duration = float(operands)
            except ValueError:
                pass
            self.learn(duration)
        elif command in ["find", "f"]:
            self.find(operands)
        elif command in ["stats", "t"]:
            self.stats()
        elif command in ["save", "s"]:
            self.save(operands)
        elif command in ["version", "v"]:
            print('.'.join(map(str, version)))
        elif command in ["help", "h", "?"]:
            usage(operands)
        else:
            print("Unrecognized command: {}. Type ? for help.".format(command))

    def add_card(self) -> None:
        try:
            entries = []  # type: List[Entry]
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

    def remove_card(self, content: str) -> None:
        if not content:
            content = input("Enter card to remove: ")

        for card in self.db.cards:
            if content in [e.text for e in card.entries]:
                print("Removed {}".format(card))
                self.db.cards.remove(card)
                heapq.heapify(self.db.cards)
                self.db.changes = True
                break

    def learn(self, duration: float = 0) -> None:
        if not self.db.cards or not self.db.top().is_due():
            print("No cards to learn")
            return

        if duration <= 0:
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

            card = self.db.top()
            i += 1
            entry = card.due_entry()

            # print due side first, all sides after press of enter
            print(chr(27) + "[2J")
            print(entry, end=" ")
            input()
            print(chr(27) + "[2J")
            card.print()

            correct = ask_yes_no("Correct?")

            try:
                card = self.db.pop()
                self.db.retention[1] += entry.proficiency
                if correct:
                    self.db.retention[0] += entry.proficiency
                    entry.proficiency = self.db.profscale * entry.proficiency + \
                                        self.db.timescale * random.random() * 3600 * log((time.time() - entry.due)/3600 * 0.125 + 1) * 24 / log(24*0.125 + 1)
                    entry.due = time.time() + entry.proficiency
                else:
                    entry.proficiency = max(entry.proficiency / self.db.faildiv, 60.)
                    self.db.retention[0] += entry.proficiency
                    entry.due = time.time() + 60
                self.db.add(card)
            except (KeyboardInterrupt, EOFError):
                self.db.add(card)
                break
        print(i)

    def find(self, regex: str) -> None:
        if not regex:
            regex = input("Seach for: ")

        prog = None
        try:
            prog = re.compile(".*" + regex)
        except re.error as e:
            print("Error while compiling regular expression:", e.msg)
            return

        for card in self.db.cards:
            if any(prog.match(entry.text) for entry in card.entries) or prog.match(card.comment):
                print(time.asctime(time.localtime(card.due_at())), card)

    def stats(self) -> None:
        print("Total:", len(self.db.cards))

        print("Retention score:", 100 * self.db.retention[0]/self.db.retention[1])

    def save(self, filename: str = "") -> None:
        if not filename and not self.db.changes:
            print("No changes to be saved")
            return

        while True:
            try:
                if filename:
                    self.path = filename
                elif self.path:
                    new_path = input("Save as [" + self.path + "]: ")
                    if new_path:
                        self.path = new_path
                else:
                    self.path = input("Save as: ")

                if self.db.rethist and self.db.rethist[-1][0] + 60*60 < time.time():
                    self.db.rethist.append([time.time(),
                                            self.db.retention[0]/self.db.retention[1]])

                self.db.save(self.path)
                break
            except FileNotFoundError:
                pass

        self.db.changes = False


def usage(command: str = "") -> None:
    if command in ["add", "a"]:
        print("(add|a) Add new card.")
    elif command in ["remove", "r"]:
        print("(remove|r) [entry] Remove card.")
        print("[entry] content of one side of the card to be deleted.")
    elif command in ["learn", "l"]:
        print("(learn|l) [minutes] Start a learning session.")
        print("[minutes] specifies the duration of the session.")
    elif command in ["find", "f"]:
        print("(find|f) [expr] Search for cards.")
        print("[expr] a regular expression which the card should match.")
    elif command in ["stats", "t"]:
        print("(stats|t) Get database statistics.")
    elif command in ["save", "s"]:
        print("(save|s) [file] Save database.")
        print("[file] file the database should be saved to.")
    elif command in ["version", "v"]:
        print("(version|v) Show version information.")
    elif command in ["help", "h", "?"]:
        self.usage(operands)
    else:
        print("(add|a)               Add new card.")
        print("(remove|r) [entry]    Remove card.")
        print("(learn|l) [minutes]   Start a learning session.")
        print("(find|f) [expr]       Search for cards.")
        print("(stats|t)             Get database statistics.")
        print("(save|s) [file]       Save database.")
        print("(version|v)           Show version information.")
        print("(help|h|?) [command]  Get usage information.")
        print()
        print("For further information on a command, use help [command].")


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
