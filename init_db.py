# This script categorizes the image based on the keywords found in the image, and insert them into the database.

import json
import sqlite3
import os

def to_binary(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

if __name__ == "__main__":
    connect = sqlite3.connect("db/9618.db")
    cursor = connect.cursor()
    with open("init.sql", "r") as f: # Initialization
        cursor.executescript(f.read())

    keywords = json.load(open("9618_keywords.json", "r"))
    cursor.execute("BEGIN")
    for i in keywords.keys():
        for j in keywords[i].keys():
            for k in keywords[i][j]:
                cursor.execute(f"INSERT INTO TOPICS (main_topic_name, sub_topic_name, AS_or_A2) VALUES(?, ?, ?)", (i, k, j == "A_Level"))
    connect.commit()

    cursor.execute("BEGIN")
    for series in ['s', 'w']:
        for year in [21, 22, 23, 24]:
            for paper in [1, 2, 3, 4]:
                for variant in [1, 2, 3]:
                    paper_id = f"9618_{series}{year}_qp_{paper}{variant}"
                    if os.path.exists(paper_id):
                        cursor.execute(f"INSERT INTO PAPERS (paper_id, year, series, paper, variant) VALUES(?, ?, ?, ?, ?)", (paper_id, year, series, paper, variant))
    connect.commit()

    cursor.execute("BEGIN")
    mapping = dict()
    cnt = 1 # The primary key of this table is set to be autoincrement, starting from 1
    for series in ['s', 'w']:
        for year in [21, 22, 23, 24]:
            for paper in [1, 2, 3, 4]:
                for variant in [1, 2, 3]:
                    paper_id = f"9618_{series}{year}_qp_{paper}{variant}"
                    if os.path.exists(paper_id):
                        for (root, dirs, files) in os.walk('./' + paper_id, topdown = True):
                            for i in files:
                                mapping[(paper_id, i.split('_')[0], i.split('_')[1][0])] = cnt
                                cursor.execute(f"INSERT INTO QUESTIONS (question_id, paper_id, image, primary_index, secondary_index) VALUES(?, ?, ?, ?, ?)", (cnt, paper_id, to_binary(os.path.join(root, i)), i.split('_')[0], i.split('_')[1][0]))
                                cnt += 1
    connect.commit()

    cursor.execute("BEGIN")
    for series in ['s', 'w']:
        for year in [21, 22, 23, 24]:
            for paper in [1, 2, 3, 4]:
                for variant in [1, 2, 3]:
                    paper_id = f"9618_{series}{year}_ms_{paper}{variant}"
                    if os.path.exists(paper_id):
                        for (root, dirs, files) in os.walk('./' + paper_id, topdown = True):
                            for i in files:
                                cursor.execute(f"INSERT INTO MARKSCHEMES (question_id, image) VALUES(?, ?)", (mapping[(paper_id.replace("ms", "qp"), i.split('_')[0], i.split('_')[1][0])], to_binary(os.path.join(root, i))))
    connect.commit()