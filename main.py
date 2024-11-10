from flask import Flask, request, jsonify, render_template
import os
import fitz
import spacy
import json

app = Flask(__name__)
nlp = spacy.load("ru_core_news_sm")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET'])
def upload_form():
    return render_template('index.html')


@app.route('/get_ratings', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part'}), 400

    files = request.files.getlist('files')
    skills = request.form.getlist('skills[]')

    if len(files) == 0:
        return jsonify({'error': 'No files selected'}), 400

    file_contents = []
    extracted_data = []
    print(files)

    for file in files:
        if file.filename == '':
            continue

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        if file.filename.lower().endswith('.pdf'):
            try:
                doc = fitz.open(filepath)
                pdf_text = ""
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    pdf_text += page.get_text()
                print(file.filename)
                extracted_data.append(analyze_resume(file.filename, pdf_text, skills))
                file_contents.append({
                    'filename': file.filename,
                    'filetype': 'pdf',
                    'content': pdf_text
                })
                doc.close()
            except Exception as e:

                return jsonify({'error': f'Error reading PDF file {file.filename}: {str(e)}'}), 500
        else:
            file_contents.append({
                'filename': file.filename,
                'filetype': 'unknown',
                'content': 'Non-PDF file uploaded'
            })
    print(extracted_data, file_contents)
    return render_template('results.html', data=extracted_data)


def analyze_resume(filename, text, required_skills):
    # Приведение текста и навыков к нижнему регистру
    text = text.lower()
    required_skills = [skill.lower() for skill in required_skills]

    # Поиск навыков в тексте (с учетом частичных совпадений)
    skills_found = [skill for skill in required_skills if skill in text]
    matched_skills = list(set(skills_found))  # Уникальные совпадения навыков

    # Расчет процента совпадений
    matched_percent = (len(matched_skills) / len(required_skills)) * 100 if required_skills else 0.0

    return {
        "filename": filename,
        "skills_found": matched_skills,
        "matched_percent": matched_percent
    }


if __name__ == '__main__':
    app.run()
