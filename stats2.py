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
    
    added = [(card.added - time.time())/60/60/24 for card in db.cards]
    added.sort()
    minx, miny = 0, 0
    for i in range(len(added) - 1):
        if added[i+1] > added[i] + 1/24/60/60:
            minx, miny = added[i], i + 1
            print("rate:", (len(added)-miny)/(-minx))
            plt.ylim(ymin=i-1, ymax=len(added)+1)
            break

    #plt.plot([minx, 0], [miny, len(added)])
    plt.plot(added + [0], list(range(1, len(added)+1)) + [len(added)])
    plt.xlabel("Days")
    plt.ylabel("Cards")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
