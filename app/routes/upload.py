from flask import Blueprint, render_template, request, jsonify, Response
import zipfile
import os
import datetime
from app import extractqp, extractms, db
import re
import base64
from app.cv2base64 import base64_to_binary

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET'])
def upload_qp():
    return render_template('upload_qp.html', images=None, current_year=datetime.datetime.now().year)

UNCATEGORIZED_ID = -1
def add_images_to_database(database, paper_id, qp_results, ms_results):
    cursor = database.cursor()
    
    # Insert paper if it doesn't exist
    cursor.execute("""
        INSERT OR IGNORE INTO PAPERS (paper_id, year, series, paper, variant)
        VALUES (?, ?, ?, ?, ?)
    """, (paper_id["paper_id"], paper_id["year"], paper_id["series"], paper_id["paper"], paper_id["variant"]))
    
    for primary_idx, secondary_idx, image_blob in qp_results:
        image_blob = base64_to_binary(image_blob)
        cursor.execute("""
            INSERT INTO QUESTIONS (paper_id, image, primary_index, secondary_index)
            VALUES (?, ?, ?, ?)
        """, (paper_id["paper_id"], image_blob, primary_idx, secondary_idx))
        
    for primary_idx, secondary_idx, image_blob in ms_results:
        image_blob = base64_to_binary(image_blob)
        cursor.execute("""
            SELECT question_id FROM QUESTIONS
            WHERE paper_id = ? AND primary_index = ? AND secondary_index = ?
        """, (paper_id["paper_id"], primary_idx, secondary_idx))
        result = cursor.fetchone()
        
        if result:
            question_id = result[0]
            cursor.execute("""
                INSERT INTO MARKSCHEMES (question_id, image)
                VALUES (?, ?)
            """, (question_id, image_blob))
            cursor.execute("""
                INSERT INTO QUESTIONTOPICS (question_id, topic_id)
                VALUES (?, ?)
            """, (question_id, UNCATEGORIZED_ID))
        else:
            print(f"Warning: No matching question found for MS {primary_idx}.{secondary_idx}")

def extract_paper_info(filename):
    # (\d+): syllabus code (one or more digits)
    # ([swm]): series (s, w, or m)
    # (\d{2}): year (2 digits)
    # (qp|ms): type (question paper or mark scheme)
    # (\d)(\d): paper number and variant (separate digits)
    pattern = r'(\d+)_([swm])(\d{2})_(qp|ms)_(\d)(\d)\.pdf'
    match = re.match(pattern, filename)
    if match:
        syllabus, series, year, doc_type, paper, variant = match.groups()
        return {
            'syllabus': syllabus,
            'series': series,
            'year': int(year),
            'type': doc_type,
            'paper': int(paper),
            'variant': int(variant),
            'paper_id': f"{syllabus}_{series}{year}_{paper}{variant}"
        }
    return None

def get_paper_id_from_files(qp_filename, ms_filename):
    qp_info = extract_paper_info(qp_filename)
    ms_info = extract_paper_info(ms_filename)
    
    if not qp_info or not ms_info:
        print("Error: Could not parse one or both filenames")
        return None
    
    # Verify both files refer to the same paper
    if qp_info['paper_id'] != ms_info['paper_id']:
        print("Error: Question paper and mark scheme don't match")
        print(f"QP: {qp_info['paper_id']}, MS: {ms_info['paper_id']}")
        return None
    
    if qp_info['type'] != 'qp' or ms_info['type'] != 'ms':
        print("Error: Files are not correctly identified as QP and MS")
        return None
    
    return qp_info

@upload_bp.route('/upload', methods=['POST'])
def upload_pdf():
    request.files['zip'].save("upload.zip")
    with zipfile.ZipFile("upload.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
        assestlist = zip_ref.namelist()
    assestlist.append("upload.zip")
    qp = ms = ""
    for s in assestlist:
        if "qp" in s:
            qp = s
        elif "ms" in s:
            ms = s
    if qp == "" or ms == "":
        for i in assestlist:
            os.remove(i)
        return Response()

    results = extractqp.extractqp(qp)
    results2 = extractms.extractms(ms)
    web_result = []
    for i, j, image in results:
        web_result.append({"id" : f"qp{i}.{j}", "image" : image})
    for i, j, image in results2:
        web_result.append({"id" : f"ms{i}.{j}", "image" : image})
    for i in assestlist:
        os.remove(i)
    paper_id = get_paper_id_from_files(qp, ms)

    if paper_id:
        database = db.get_db()
        try:
            add_images_to_database(database, paper_id, results, results2)
            database.commit()
        except Exception as e:
            print(f"Database error: {e}")
            database.rollback()
    else:
        print("Warning: Could not extract valid paper_id from filenames")
    return jsonify({"data": web_result})