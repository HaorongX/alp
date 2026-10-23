import sqlite3
import csv

# Database and output file paths
db_path = '../db/9618.db'
output_csv = 'training_data.csv'

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query to get all questions with their topics
query = """
SELECT 
    q.content,
    qt.topic_id
FROM QUESTIONS q
INNER JOIN QUESTIONTOPICS qt ON q.question_id = qt.question_id
WHERE q.content IS NOT NULL AND q.content != ''
ORDER BY q.question_id
"""

cursor.execute(query)
results = cursor.fetchall()

# Write to CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['content', 'topic_id'])  # Header
    writer.writerows(results)  # Data

conn.close()

print(f"Exported {len(results)} rows to {output_csv}")