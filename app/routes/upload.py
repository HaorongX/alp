from flask import Blueprint, render_template, request, jsonify, Response
from pypdf import PdfReader, PdfWriter
import zipfile
import os
import datetime
from app import extractqp, extractms

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET'])
def upload_qp():
    return render_template('upload_qp.html', images=None, current_year=datetime.datetime.now().year)

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
    return jsonify({"data": web_result})