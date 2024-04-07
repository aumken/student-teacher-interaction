import asyncio
import os

import PyPDF2
from dotenv import load_dotenv
from openai import AsyncOpenAI

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def generate_mcq(context, plot):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"Generate 10 multiple-choice questions based on the provided {context}, each with 4 options (A, B, C, D). After each question, immediately provide the correct answer, preceded by 'Correct Answer: '. The format should be strictly followed for each question and answer pair. Here is an example of how each question and answer should be formatted:\n\nQuestion 1: [Question text]\nA) Option A\nB) Option B\nC) Option C\nD) Option D\nCorrect Answer: A\n\nPlease adhere to this format for all 10 questions and their corresponding answers.",
                },
                {"role": "user", "content": plot},
            ],
        )
        mcqs_and_answers_content = response.choices[0].message.content
        return mcqs_and_answers_content.replace("*", "")
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        return None


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
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(os.path.join(folder, filename), "w") as file:
        file.write(content)


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


async def process_file(context, filepath, mcq_folder, answer_folder):
    filename = os.path.basename(filepath)
    # Keep the original file extension for Markdown files
    questions_filename = "question_" + filename.replace(".pdf", ".md")
    answers_filename = "answer_" + filename.replace(".pdf", ".md")

    # Check if both files already exist to avoid re-processing
    if os.path.exists(os.path.join(mcq_folder, questions_filename)) and os.path.exists(
        os.path.join(answer_folder, answers_filename)
    ):
        return  # Skip processing if both files exist

    # Extract text from PDF or read from Markdown file
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
    else:
        with open(filepath, "r") as file:
            plot = file.read()

    # Generate MCQs and answers
    mcq_and_answers = await generate_mcq(context, plot)
    if mcq_and_answers:
        mcqs, answers = separate_mcqs_and_answers(mcq_and_answers)
        save_to_file(mcqs, mcq_folder, questions_filename)
        save_to_file(answers, answer_folder, answers_filename)


async def process_directory(
    context, folder, mcq_folder_base, answer_folder_base, root_folder
):
    for root, dirs, files in os.walk(folder):
        rel_path = os.path.relpath(root, root_folder)
        mcq_folder = os.path.join(mcq_folder_base, rel_path)
        answer_folder = os.path.join(answer_folder_base, rel_path)

        os.makedirs(mcq_folder, exist_ok=True)
        os.makedirs(answer_folder, exist_ok=True)

        tasks = [
            process_file(context, os.path.join(root, file), mcq_folder, answer_folder)
            for file in files
            if file.endswith(".md") or file.endswith(".pdf")
        ]

        await asyncio.gather(*tasks)


async def main():
    root_folder = "a_files"
    mcq_folder_base = "b_questions"
    answer_folder_base = "c_answers"

    for context in os.listdir(root_folder):
        context_folder = os.path.join(root_folder, context)
        if os.path.isdir(context_folder):
            await process_directory(
                context,
                context_folder,
                mcq_folder_base,
                answer_folder_base,
                root_folder,
            )


if __name__ == "__main__":
    asyncio.run(main())
