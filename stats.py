#!/usr/bin/env python3

import sys
import json
import time
import vocabulary
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) != 2:
        print("Usage: {} <file>".format(sys.argv[0]))
        return

    db = None
    with open(sys.argv[1], "r") as dbfile:
        db = vocabulary.Database.from_dict(json.load(dbfile))
    
    dues = [entry.due for card in db.cards for entry in card.entries]
    dues.sort(reverse=True)

    dues_per_day = []

    step = 60*60*24
    for t in range(int(time.time()), int(dues[0]) + step, step):
        dues_per_day += [0]
        while dues and dues[-1] <= t:
            dues.pop()
            dues_per_day[-1] += 1

    proficiencies = [entry.proficiency for card in db.cards for entry in card.entries]
    proficiencies.sort(reverse=True)

    entries_per_day = []

    step = 60*60*24//2
    for t in range(0, int(proficiencies[0]) + step, step):
        entries_per_day += [0]
        while proficiencies and proficiencies[-1] <= t:
            proficiencies.pop()
            entries_per_day[-1] += 1

    plt.plot(range(len(dues_per_day)), dues_per_day)
    plt.plot(range(len(entries_per_day)), entries_per_day)
    #plt.xlim(xmin=0, xmax=len(dues_per_day) - 1)
    #plt.ylim(ymin=0)
    plt.xlabel("Days")
    plt.ylabel("Entries")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
