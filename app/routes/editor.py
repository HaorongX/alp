from flask import Blueprint, render_template, request, jsonify
from app.db import get_db
from app.syllabus import get_syllabus

editor_bp = Blueprint('editor', __name__)

@editor_bp.route('/editpb')
def edit_pb():
    return render_template("edit_pb.html", syllabus = get_syllabus())

@editor_bp.route('/edit_category', methods=['POST'])
def edit_category():
    db = get_db()
    cursor = db.cursor()

    args = request.json
    cursor.execute(f"UPDATE QUESTIONTOPICS SET topic_id = ? WHERE question_id = ?", (args["topicid"], args["qid"]))
    db.commit()
    print(f"UPDATE QUESTIONTOPICS SET topic_id = ? WHERE question_id = ?", (args["topicid"], args["qid"]))
    return jsonify({"Status" : "ok"})