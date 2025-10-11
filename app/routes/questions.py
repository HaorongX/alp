from flask import Blueprint, request, jsonify
from app.db import get_db
from app.image_handler import upload_image

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/get_questions', methods=['GET'])
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
    
    return jsonify({'questions': questions})