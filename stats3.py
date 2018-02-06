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
    

    plt.plot([(x[0]-time.time())/60/60/24 for x in db.rethist], [x[1]*100 for x in db.rethist])
    plt.xlabel("Days")
    plt.ylabel("Retention / %")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
