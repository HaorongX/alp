from flask import Flask, render_template, request, redirect, url_for, jsonify, g, Response, send_file
import sqlite3
import json
import base64
import pdfkit
import os
import zipfile

app = Flask(__name__)

syllabus = {}

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('db/9618.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

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

@app.route('/')
def index():
    return render_template('index.html')

images = {}

def upload_image(id, image):
    global images
    if id in images:
        images[id].append(image)
    else:
        images[id] = [image]
    print(f"Image {id} uploaded successfully.")

@app.route('/get_image', methods=['GET'])
def get_image():
    global images
    return Response(images[request.args.get('id')], mimetype = "image/png")

@app.route('/get_questions', methods=['GET'])
def get_questions():
    subtopic_id = request.args.get('subtopic_id')
    if not subtopic_id:
        return jsonify({'error': 'Missing subtopic ID'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT question_id
        FROM QUESTIONTOPICS
        WHERE topic_id = ?
    """, (subtopic_id,))
    rows = cursor.fetchall()
    questions = []
    for i in rows:
        cursor.execute("""
            SELECT image, paper_id, primary_index, secondary_index
            FROM QUESTIONS
            WHERE question_id = ?
        """, (i[0],))
        res = cursor.fetchone()
        if res[1][-2] == '1' or res[1][-2] == '2':
            level = 'AS'
        else:
            level = 'A2'
        upload_image("qp" + str(i[0]), res[0])
        questions.append({"id": i[0], "image_url": f"/get_image?id={'qp'+str(i[0])}", "description": res[1] + " Q" + str(res[2]) + "A" + str(res[3]), "level" : level})
    
    # For now, using your placeholder data
    return jsonify({'questions': questions})

@app.route('/create', methods=['GET', 'POST'])
def create_test():
    return render_template('create.html', syllabus=syllabus)

def generate_pdf(images, title, description, filename, indices):
    options = {
        'print-media-type': None,
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'page-size': 'A4',
        'enable-local-file-access': True  # Allow local file access
    }
    html_content = open("templates/template_qp.html", "r").read()
    html_content += f'<div class="title">{title}</div>\n'
    if description.strip() != '':
        html_content += f'<div class="description">{description}</div>\n'
    
    for i, image_data in enumerate(images, 1):
        base64_string = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_string}"
        html_content += f'''
        <div class="question">
            <div class="question-number">({indices[i - 1]}) {i}.</div>
            <div class="image-container">
                <img class="question-image" src="{data_url}" alt="Question {i}">
            </div>
        </div>
        '''
    html_content += """
    </body>
    </html>
    """
    with open('temp.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    pdfkit.from_file('temp.html', filename, options=options)
    os.remove('temp.html')
    return filename

@app.route('/submit_test', methods=['POST'])
def submit_test():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    question_ids = request.form.get('question_ids', '')  # e.g. "q1,q5,q8"
    ids_list = [qid for qid in question_ids.split(',') if qid]
    print(f"Title: {title}, Description: {description}, Question IDs: {ids_list}")
    db = get_db()
    cursor = db.cursor()
    
    questions = []
    indices = []
    for i in ids_list:
        cursor.execute("SELECT image, paper_id, primary_index, secondary_index FROM QUESTIONS WHERE question_id = ?", (i,))
        res = cursor.fetchone()
        questions.append(res[0])
        indices.append(res[1] + " Q" + str(res[2]) + "A" + str(res[3]))
    generate_pdf(questions, title, description, "qp.pdf", indices)
    markschemes = []
    for i in ids_list:
        cursor.execute("SELECT image FROM MARKSCHEMES WHERE question_id = ?", (i,))
        markschemes.append(cursor.fetchone()[0])
    generate_pdf(markschemes, title + " Mark Scheme", description, "ms.pdf", indices)
    with zipfile.ZipFile(os.path.join(os.getcwd(), 'temp.zip'), 'w') as zipf:
        for filename in ['qp.pdf', 'ms.pdf']:
            file_path = os.path.join(os.getcwd(), filename)
            zipf.write(file_path, arcname=filename)

    return send_file("temp.zip", mimetype='application/zip', as_attachment=True, download_name=f'test.zip')

@app.route('/editpb')
def edit_pb():
    global syllabus
    return render_template("edit_pb.html", syllabus = syllabus)

@app.route('/edit_category', methods = ['POST'])
def edit_category():
    db = get_db()
    cursor = db.cursor()

    args = json.loads(request.data.decode('utf-8'))
    cursor.execute(f"UPDATE QUESTIONTOPICS SET topic_id = ? WHERE question_id = ?", (args["topicid"], args["qid"]))
    db.commit()
    print(f"UPDATE QUESTIONTOPICS SET topic_id = ? WHERE question_id = ?", (args["topicid"], args["qid"]))
    return jsonify({"Status" : "ok"})

if __name__ == '__main__':
    # Initialize syllabus data before starting the server
    init_syllabus()
    app.run(debug = True)