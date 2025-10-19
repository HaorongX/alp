from flask import Blueprint, render_template, request, jsonify, Response
import base64
from pypdf import PdfReader, PdfWriter
import zipfile
import os
import datetime
from app import extractqp

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['GET'])
def upload_qp():
    return render_template('upload_qp.html', images=None, current_year=datetime.date.year)

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

    reader = PdfReader(qp)
    output = PdfWriter()

    for i in range(1, len(reader.pages)): # Skip information page
        page = reader.pages[i]
        text = page.extract_text()
        if text.find("BLANK PAGE") == -1:
            p = reader.pages[i]
            output.add_page(p)
    reader.close()
    output.write(qp)
    output.close()

    results = extractqp.extractqp(qp)
    web_result = []
    for i, j, image in results:
        web_result.append({"id" : f"{i}.{j}", "image" : image})
    for i in assestlist:
        os.remove(i)
    return jsonify({"data": web_result})