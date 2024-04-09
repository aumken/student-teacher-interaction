import os
import PyPDF2

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

def process_file(context, filepath, root_folder):
    # Extract text from PDF or read from Markdown file
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
    else:
        with open(filepath, "r") as file:
            plot = file.read()

    return context, plot


def process_directory(context, folder, root_folder):
    for root, dirs, files in os.walk(folder):
        tasks = [
            process_file(context, os.path.join(root, file), root_folder)
            for file in files
            if file.endswith(".md")
            or file.endswith(".pdf")  # Include PDF files as well
        ]
    
    return tasks


def get_all_content(context, context_folder, root_folder):
    return process_directory(context, context_folder, root_folder)