import base64
import pdfkit
import os

def generate_pdf(images, title, description, filename, indices, qp=True):
    options = {
        'print-media-type': None,
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'page-size': 'A4',
        'enable-local-file-access': True
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
    html_filename = 'qp.html' if qp else 'ms.html'
    html_path = os.path.join(os.path.dirname(filename), html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        pdfkit.from_file(html_path, filename, options=options)
    return filename

def generate_integrated_pdf(questions, answers, title, description, indices):
    html_content = open("templates/template_qp.html", "r").read()
    html_content += f'<div class="title">{title}</div>\n'
    if description.strip() != '':
        html_content += f'<div class="description">{description}</div>\n'
    
    for i in range(len(questions)):
        qp_base64_string = base64.b64encode(questions[i]).decode('utf-8')
        ms_base64_string = base64.b64encode(answers[i]).decode('utf-8')
        qp_data_url = f"data:image/png;base64,{qp_base64_string}"
        ms_data_url = f"data:image/png;base64,{ms_base64_string}"
        html_content += f'''
        <div class="question">
            <div class="question-number">({indices[i]}) {i + 1}.</div>
            <div class="image-container">
                <img class="question-image" src="{qp_data_url}" alt="Question {i + 1}">
            </div>
            <details>
                <summary>Mark Scheme</summary>
                <div class="image-container">
                <img class="question-image" src="{ms_data_url}" alt="Question {i + 1}">
            </div>
            </details>
        </div>
        '''
    html_content += """
    </body>
    </html>
    """

    with open(f'integrated.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    return 'integrated.html'