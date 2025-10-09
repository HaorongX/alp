import re
import cv2
from pytesseract import image_to_string
import json
import sys
import os
import sqlite3
from denoise import denoise

keywords = json.load(open('9618_keywords.json'))
TOPICS = {}
for i in keywords.keys():
    TOPICS[i] = []
    for j in keywords[i].keys():
        for k in keywords[i][j]:
            TOPICS[i].append(k)

def get_ocr_text(image):
    return denoise(image)

def choose_topic():
    print("\nAvailable Topics:")
    topic_list = list(TOPICS.keys())
    for i, topic in enumerate(topic_list):
        print(f"{i+1}. {topic}")
    
    topic_idx = int(input("Choose a topic (number): ")) - 1
    topic = topic_list[topic_idx]

    print(f"\nAvailable Subtopics for {topic}:")
    subtopics = TOPICS[topic]
    for j, sub in enumerate(subtopics):
        print(f"{j+1}. {sub}")
    
    subtopic_idx = int(input("Choose a subtopic (number) (type -1 to choose another topic): ")) - 1
    if subtopic_idx == -2:
        return choose_topic()
    subtopic = subtopics[subtopic_idx]

    return topic, subtopic

def label_dataset(image_dir, connect, cursor):
    qp_name = re.search(r"9618_[sw]\d{2}_qp_\d{2}", sys.argv[1]).group(0)
    if qp_name[-2] == '1' or qp_name[-2] == '2':
        AS = True
    else:
        AS = False
    for root, _, files in os.walk(image_dir):
        for file in files:
            filepath = os.path.join(root, file)

            image = cv2.imread(filepath)
            question = get_ocr_text(image)

            found = False
            for i in keywords.keys():
                for j in keywords[i].keys():
                    if (j == 'AS_Level' and AS == False) or (j != 'AS_Level' and AS == True):
                        continue
                    for k in keywords[i][j]:
                        for keyword in keywords[i][j][k]:
                            if question.find(keyword.lower()) != -1:
                                topic = i
                                subtopic = k
                                found = True
                                break
            if not found:
                print(f"\nLabeling: {filepath}")
                cv2.imwrite("current.png", image)
                topic, subtopic = choose_topic()
            # topic_id = cursor.execute("SELECT topic_id FROM TOPICS WHERE main_topic_name = ? AND sub_topic_name = ?", (topic, subtopic)).fetchone()[0]
            # question_id = cursor.execute("SELECT question_id FROM QUESTIONS WHERE paper_id = ? AND primary_index = ? AND secondary_index = ?", (qp_name, file[:-4].split('_')[0], file[:-4].split('_')[1])).fetchone()[0]
            # cursor.execute("INSERT INTO QUESTIONTOPICS (question_id, topic_id) VALUES (?, ?)", (question_id, topic_id))

if __name__ == "__main__":
    connect = sqlite3.connect("db/9618.db")
    cursor = connect.cursor()
    image_dir = sys.argv[1]
    label_dataset(image_dir, connect, cursor)
    connect.commit()