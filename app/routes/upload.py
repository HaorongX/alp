from flask import Blueprint, render_template, request, jsonify
import base64
import time

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET'])
def upload_qp():
    return render_template('upload_qp.html', images=None, current_year=2025)

@upload_bp.route('/upload', methods=['POST'])
def upload_pdf():
    file = request.files['pdf']
    time.sleep(5)
    sample_img = base64.b64encode(b'samplebinarydata').decode('utf-8')
    result = [
        {"id": "Q001", "image": sample_img},
        {"id": "Q002", "image": sample_img},
        {"id": "Q003", "image": sample_img},
    ]
    return jsonify({"data": result})