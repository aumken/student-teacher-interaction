import asyncio
import os
import re
from pathlib import Path

import aiofiles
import PyPDF2
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
env_path = Path(__file__).parent.joinpath("..", ".env")
load_dotenv(env_path)

# Initialize the OpenAI client with your API key
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# Function to extract text from PDF, limited to the first 1500 characters
def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, "rb") as file:
        pdf = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf.pages)):
            text += pdf.pages[page_num].extract_text()
            if len(text) >= 1500:  # Stop if text length exceeds 1500 characters
                break
    return text[:1500]


async def get_model_answers(questions, content, static_info, context):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You will be given a {context}, its analysis, and a set of 10 multiple-choice questions based on it. "
                    "Please provide your answers in a single string, with each character representing your choice for the corresponding question, "
                    f"or list them numerically. For example: 'ABCDABCDAB' or '1) A 2) B 3) C ...'. Do not write out the entire answer, just the letter.\n\n Info: {content}\n\n Analysis: {static_info}\n",
                },
                {"role": "user", "content": questions},
            ],
        )
        raw_answers = response.choices[0].message.content.strip()

        continuous_pattern = re.compile(r"\b[A-D]{10}\b")
        listed_pattern = re.compile(r"\b\d+[).]?\s*([A-D])")

        continuous_match = continuous_pattern.search(raw_answers)
        if continuous_match:
            return continuous_match.group()

        listed_matches = listed_pattern.findall(raw_answers)
        if len(listed_matches) == 10:
            return "".join(listed_matches)

        return "None"  # Return "None" if the correct format isn't found
    except Exception as e:
        print(f"Error: {e}")
        return None


async def process_question_file(
    questions_path, static_info_path, original_info_path, answers_path, context
):
    # Check if the question file exists, else skip processing
    if not questions_path.exists():
        print(f"Skipping {questions_path.name} due to missing question file.")
        return

    # Function to asynchronously read file content
    async def read_file_content(file_path):
        async with aiofiles.open(file_path, "r") as file:
            return await file.read()

    # Check and read the static info file (PDF or MD)
    if not static_info_path.exists():
        static_info_path = static_info_path.with_suffix(
            ".pdf"
        )  # Attempt to find a PDF alternative
        if not static_info_path.exists():
            print(f"Skipping {questions_path.name} due to missing static info file.")
            return

    static_info = (
        extract_text_from_pdf(static_info_path)
        if static_info_path.suffix == ".pdf"
        else await read_file_content(static_info_path)
    )

    # Check and read the original info file (PDF or MD)
    if not original_info_path.exists():
        original_info_path = original_info_path.with_suffix(
            ".pdf"
        )  # Attempt to find a PDF alternative
        if not original_info_path.exists():
            print(f"Skipping {questions_path.name} due to missing original info file.")
            return

    content = (
        extract_text_from_pdf(original_info_path)
        if original_info_path.suffix == ".pdf"
        else await read_file_content(original_info_path)
    )

    # Read the questions file
    questions = await read_file_content(questions_path)

    # Generate model answers based on the content and static info
    model_answers = await get_model_answers(questions, content, static_info, context)
    if model_answers and len(model_answers) == 10:
        answers_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(answers_path, "w") as file:
            await file.write(model_answers)


async def process_directory(questions_dir, static_dir, original_info_dir, answers_dir):
    tasks = []

    for root, _, files in os.walk(questions_dir):
        for file in files:
            if file.startswith("question_") and file.endswith(".md"):
                questions_path = Path(root) / file
                relative_path = questions_path.relative_to(questions_dir)
                static_info_path = static_dir / relative_path.with_name(
                    f"static_{relative_path.stem[9:]}.md"
                )
                original_info_path = original_info_dir / relative_path.with_name(
                    f"{relative_path.stem[9:]}.md"
                )
                answers_path = answers_dir / relative_path.with_name(
                    f"t2_{relative_path.stem[9:]}.md"
                )

                # Extract context from the directory structure
                context = relative_path.parts[0]

                task = process_question_file(
                    questions_path,
                    static_info_path,
                    original_info_path,
                    answers_path,
                    context,
                )
                tasks.append(task)

    await asyncio.gather(*tasks)


async def main(
    questions_base_dir, static_base_dir, original_info_base_dir, answers_base_dir
):
    await process_directory(
        questions_base_dir, static_base_dir, original_info_base_dir, answers_base_dir
    )


if __name__ == "__main__":
    questions_base_dir = Path("b_questions")
    static_base_dir = Path("d_static")
    original_info_base_dir = Path("a_files")
    answers_base_dir = Path("t2_answers")

    asyncio.run(
        main(
            questions_base_dir,
            static_base_dir,
            original_info_base_dir,
            answers_base_dir,
        )
    )
