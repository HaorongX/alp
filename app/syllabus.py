import json
import sqlite3

syllabus = {}

def init_syllabus():
    global syllabus
    keywords = json.loads(open('9618_keywords.json').read())
    
    conn = sqlite3.connect('db/9618.db')
    cursor = conn.cursor()
    
    for i in keywords.keys():
        syllabus[i] = []
        for j in keywords[i].keys():
            for k in keywords[i][j]:
                topic_id = cursor.execute("SELECT topic_id FROM TOPICS WHERE main_topic_name = ? AND sub_topic_name = ?", (i, k)).fetchone()[0]
                if j.find('AS_Level') != -1:
                    temp = {"id": topic_id, "name": k, "level": 'AS'}
                else:
                    temp = {"id": topic_id, "name": k, "level": 'A2'}
                syllabus[i].append(temp)
    
    conn.close()

def get_syllabus():
    return syllabus