import os
import pdfplumber
from pdfminer.psparser import PSEOF
from pathlib import Path
import base64

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
                if len(text) >= 1500:
                    break
    except PSEOF:  # Catch the PSEOF exception
        pass  # Continue to the next line
    return text[:1500]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def process_file(context, filepath,):
    # Extract text from PDF or read from Markdown file
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
    elif filepath.endswith(".jpg"):
        plot = encode_image(filepath)
    else:
        with open(filepath, "r") as file:
            plot = file.read()

    return context, plot


def process_directory(context, folder, root_folder):
    tasks = []
    for root, dirs, files in os.walk(folder):
        tasks.extend([
            process_file(context, os.path.join(root, file))
            for file in files
            if file.endswith(".md")
            or file.endswith(".pdf")  # Include PDF files as well
        ])
    
    return tasks

def get_all_data(context, context_folder, questions_folder, answers_folder, static_folder, root_folder):
    tasks = []
    for root, dirs, files in os.walk(context_folder):
        for file in files:
            context, content = process_file(context, os.path.join(root, file))

            if context == 'academic_papers':
                file = file.replace('.pdf', '.md')
            elif context == 'images':
                file = file.replace('.jpg', '.md')
            
            static_path = os.path.join(root.replace(context_folder, static_folder), f'static_{file}')
            _, static_lesson = process_file(context, static_path)

            questions_path = os.path.join(root.replace(context_folder, questions_folder), f'question_{file}')
            _ , questions = process_file(context, questions_path)

            answers_path = os.path.join(root.replace(context_folder, answers_folder), f'answer_{file}')
            _ , answers = process_file(context, answers_path)

            tasks.append((file, context, content, questions, answers, static_lesson))
    
    return tasks

def get_all_content(context, context_folder, root_folder):
    return process_directory(context, context_folder, root_folder)