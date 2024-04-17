import os
import PyPDF2
from pathlib import Path

def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, "rb") as file:
        pdf = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf.pages)):
            text += pdf.pages[page_num].extract_text()
            if (
                len(text) >= 1500
            ):  # Check if the accumulated text has reached 1500 characters
                break  # Stop reading further if 1500 characters have been reached
    return text[:1500]  # Return only the first 1500 characters of the text

def process_file(context, filepath,):
    # Extract text from PDF or read from Markdown file
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
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

def get_all_data(context, context_folder, questions_folder, answers_folder, root_folder):
    tasks = []
    for root, dirs, files in os.walk(context_folder):
        for file in files:
            context, content = process_file(context, os.path.join(root, file))

            questions_path = os.path.join(root.replace(context_folder, questions_folder), f'question_{file}')
            _ , questions = process_file(context, questions_path)

            answers_path = os.path.join(root.replace(context_folder, answers_folder), f'answer_{file}')
            _ , answers = process_file(context, answers_path)

            tasks.append((file, context, content, questions, answers))
    
    return tasks

def get_all_content(context, context_folder, root_folder):
    return process_directory(context, context_folder, root_folder)