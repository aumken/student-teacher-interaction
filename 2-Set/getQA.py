#getQA.py
import asyncio
import base64
import os

import pdfplumber
import requests
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pdfminer.psparser import PSEOF  # Import the PSEOF exception

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def generate_description_from_image(image_path, max_retries=5, expected_count=5):
    base64_image = encode_image(image_path)
    retries = 0
    while retries < max_retries:
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Generate {expected_count} multiple-choice questions based on the provided image, each with 4 options (A, B, C, D). After each question, immediately provide the correct answer, preceded by 'Correct Answer: '. The format should be strictly followed for each question and answer pair. Here is an example of how each question and answer should be formatted:\n\nQuestion 1: [Question text]\nA) Option A\nB) Option B\nC) Option C\nD) Option D\nCorrect Answer: A\n\nPlease adhere to this format for all {expected_count} questions and their corresponding answers.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
            )
            mcqs_and_answers_content = response.choices[0].message.content
            mcqs, answers = separate_mcqs_and_answers(mcqs_and_answers_content)
            if len(answers) == expected_count and all(
                answer in "ABCD" for answer in answers
            ):
                return mcqs, answers
            else:
                retries += 1
        except Exception as e:
            print(f"Error generating MCQs: {e}")
            retries += 1
    print(f"Failed to generate valid MCQs after {max_retries} retries for {image_path}.")
    return "", ""


async def generate_mcq(context, plot, max_retries=5, expected_count=10):
    retries = 0
    while retries < max_retries:
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate {expected_count} multiple-choice questions based on the provided {context}, each with 4 options (A, B, C, D). After each question, immediately provide the correct answer, preceded by 'Correct Answer: '. The format should be strictly followed for each question and answer pair. Here is an example of how each question and answer should be formatted:\n\nQuestion 1: [Question text]\nA) Option A\nB) Option B\nC) Option C\nD) Option D\nCorrect Answer: A\n\nPlease adhere to this format for all {expected_count} questions and their corresponding answers.",
                    },
                    {"role": "user", "content": plot},
                ],
            )
            mcqs_and_answers_content = response.choices[0].message.content
            mcqs, answers = separate_mcqs_and_answers(mcqs_and_answers_content)
            if len(answers) == expected_count and all(
                answer in "ABCD" for answer in answers
            ):
                return mcqs, answers
            else:
                retries += 1
        except Exception as e:
            print(f"Error generating MCQs: {e}")
            retries += 1
    print(f"Failed to generate valid MCQs after {max_retries} retries for {plot}.")
    return "", ""


def separate_mcqs_and_answers(mcqs_and_answers):
    mcqs, answers = [], []
    lines = mcqs_and_answers.split("\n")
    for line in lines:
        if line.startswith("Correct Answer:"):
            answers.append(line.split("Correct Answer:")[1].strip())
        else:
            mcqs.append(line)
    return "\n".join(mcqs), "".join(answers)


def save_to_file(content, folder, filename):
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
                if len(text) >= 1500:
                    break
    except PSEOF:  # Catch the PSEOF exception
        print(
            f"Encountered Unexpected EOF error for {filepath}, extracting available text"
        )
        pass  # Continue to the next line
    return text[:1500]


async def process_file(context, filepath, mcq_folder, answer_folder):
    filename = os.path.basename(filepath)
    base_filename = filename.rsplit(".", 1)[0]
    questions_filename = f"question_{base_filename}.md"
    answers_filename = f"answer_{base_filename}.md"

    # Check if both files already exist to avoid re-processing
    if os.path.exists(os.path.join(mcq_folder, questions_filename)) and os.path.exists(
        os.path.join(answer_folder, answers_filename)
    ):
        return

    # Check if the answer file already exists and has the expected number of answers
    expected_count = 10 if not filepath.endswith((".jpg", ".jpeg")) else 5
    answer_file_path = os.path.join(answer_folder, answers_filename)
    if os.path.exists(answer_file_path):
        with open(answer_file_path, "r") as file:
            existing_answers = file.read()
        if len(existing_answers) == expected_count and all(
            answer in "ABCD" for answer in existing_answers
        ):
            return

    # Process based on file type
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
        expected_count = 10
    elif filepath.endswith((".jpg", ".jpeg")):  # Handle both .jpg and .jpeg
        mcqs, answers = await generate_description_from_image(
            filepath, max_retries=5, expected_count=5
        )
        if mcqs and answers:
            print(f"{mcqs}\n{answers}\n{filepath}")
            save_to_file(mcqs, mcq_folder, questions_filename)
            save_to_file(answers, answer_folder, answers_filename)
        else:
            print(f"Failed to generate valid MCQs for {filepath}")
    elif filepath.endswith(".md"):  # Handle .md files
        with open(filepath, "r") as file:
            plot = file.read()
        expected_count = 10
    else:
        print(f"Unsupported file type for {filepath}")  # Debugging print
        return

    if not filepath.endswith((".jpg", ".jpeg")):
        mcqs, answers = await generate_mcq(context, plot, expected_count=expected_count)
        if mcqs and answers:
            save_to_file(mcqs, mcq_folder, questions_filename)
            save_to_file(answers, answer_folder, answers_filename)
        else:
            print(f"No MCQs generated for {filepath}")  # Debugging print


async def process_directory(context, folder, mcq_folder_base, answer_folder_base):
    print(f"Starting directory processing for {folder}")
    tasks = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith((".md", ".pdf", ".jpg", ".jpeg")):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, folder)
                mcq_folder = os.path.join(mcq_folder_base, context, relative_path)
                answer_folder = os.path.join(answer_folder_base, context, relative_path)
                tasks.append(
                    process_file(context, file_path, mcq_folder, answer_folder)
                )
    await asyncio.gather(*tasks)


async def main():
    root_folder = "a_files"
    mcq_folder_base = "b_questions"
    answer_folder_base = "c_answers"
    for context in os.listdir(root_folder):
        context_folder = os.path.join(root_folder, context)
        if os.path.isdir(context_folder):
            await process_directory(
                context, context_folder, mcq_folder_base, answer_folder_base
            )


if __name__ == "__main__":
    asyncio.run(main())
