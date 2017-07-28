#!/usr/bin/env python3

import random
import pickle
import sys
import json
import time

class Card:
    pass

class Database:
    pass


class DatabaseEncoder(json.JSONEncoder):
    def default(self, db):
        words = []
        for i, cat in enumerate(db.categories):
            for word in cat:
                proficiency = 24*60*60*i*i
                words.append({
                    "entries": [{"text": word,
                                 "proficiency": proficiency,
                                 "due": time.time() + proficiency + random.random() * 0.2 * proficiency
                                 } for word in words.words],
                    "comment": word.comment,
                })
        
        return {
            "langs": db.langs,
            "retention": [1.0, 1.0],
            "cards": words
        }
    

def main():
    if len(sys.argv) != 2:
        print("Usage: {} <file>".format(sys.argv[0]))
        return

    db = None
    with open(sys.argv[1], "rb") as dbfile:
        db = pickle.load(dbfile)

    with open(sys.argv[1] + ".new", "w") as dbfile:
        dbfile.write(json.dumps(db, cls=DatabaseEncoder, indent=2))


if __name__ == "__main__":
    main()
