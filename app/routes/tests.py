from flask import Blueprint, request, render_template, send_file, current_app
from app.db import get_db
from app.pdf_generator import generate_pdf, generate_integrated_pdf
import zipfile
import os

tests_bp = Blueprint('tests', __name__)

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@tests_bp.route('/create', methods=['GET', 'POST'])
def create_test():
    from app.syllabus import get_syllabus
    return render_template('create.html', syllabus=get_syllabus())

@tests_bp.route('/submit_test', methods=['POST'])
def submit_test():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    question_ids = request.form.get('question_ids', '')
    ids_list = [qid for qid in question_ids.split(',') if qid]
    print(f"Title: {title}, Description: {description}, Question IDs: {ids_list}")
    db = get_db()
    cursor = db.cursor()
    
    project_root = get_project_root()
    
    questions = []
    indices = []
    for i in ids_list:
        cursor.execute("SELECT image, paper_id, primary_index, secondary_index FROM QUESTIONS WHERE question_id = ?", (i,))
        res = cursor.fetchone()
        questions.append(res[0])
        indices.append(res[1] + " Q" + str(res[2]) + "A" + str(res[3]))
    generate_pdf(questions, title, description, os.path.join(project_root, "qp.pdf"), indices)

    markschemes = []
    for i in ids_list:
        cursor.execute("SELECT image FROM MARKSCHEMES WHERE question_id = ?", (i,))
        markschemes.append(cursor.fetchone()[0])
    
    generate_pdf(markschemes, title + " Mark Scheme", description, os.path.join(project_root, "ms.pdf"), indices, False)
    generate_integrated_pdf(questions, markschemes, title, description, indices)
    
    for i in ["ms.html", "ms.pdf", "qp.html", "qp.pdf", "integrated.html"]:
        os.remove(i)

    zip_path = os.path.join(project_root, 'temp.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filename in ['qp.pdf', 'ms.pdf', 'qp.html', 'ms.html', 'integrated.html']:
            file_path = os.path.join(project_root, filename)
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=filename)

    return send_file(zip_path, mimetype='application/zip', as_attachment=True, download_name=f'test.zip')