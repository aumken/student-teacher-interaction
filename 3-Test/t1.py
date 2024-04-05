import asyncio
import os
import re
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

# Initialize the OpenAI client with your API key
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def get_model_answers(questions, content, static_info, context):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You will be given a {context}, its analysis, and a set of 10 multiple-choice questions based on it. "
                        "Please provide your answers in a single string, with each character representing your choice for the corresponding question, "
                        "or list them numerically. For example: 'ABCDABCDAB' or '1) A 2) B 3) C ...'."
                        f"\n\n{context}: {content}\n"
                        f"\n{context} Analysis: {static_info}\n"
                    ),
                },
                {
                    "role": "user",
                    "content": f"{questions}",
                },
            ],
        )
        raw_answers = response.choices[0].message.content.strip()
        answers = "".join(filter(str.isalpha, raw_answers))[:10].upper()
        return answers if len(answers) == 10 else "None"
    except Exception as e:
        print(f"Error: {e}")
        return None

async def process_question_file(questions_path, static_info_path, original_info_path, answers_path, context):
    if not os.path.exists(static_info_path) or not os.path.exists(original_info_path):
        print(f"Skipping {questions_path.name} due to missing information file.")
        return

    async with aiofiles.open(static_info_path, "r") as file:
        static_info = await file.read()

    async with aiofiles.open(original_info_path, "r") as file:
        content = await file.read()

    async with aiofiles.open(questions_path, "r") as file:
        questions = await file.read()

    model_answers = await get_model_answers(questions, content, static_info, context)
    if model_answers and len(model_answers) == 10:
        Path(answers_path.parent).mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(answers_path, "w") as file:
            await file.write(model_answers)

async def process_directory(questions_dir, static_dir, original_info_dir, answers_dir, context):
    tasks = []

    for root, _, files in os.walk(questions_dir):
        for file in files:
            if file.startswith("question_") and file.endswith(".md"):
                questions_path = Path(root) / file
                relative_path = questions_path.relative_to(questions_dir)
                static_info_path = static_dir / relative_path.with_name(f"static_{relative_path.stem[9:]}.md")
                original_info_path = original_info_dir / relative_path.with_name(f"{relative_path.stem[9:]}.md")
                answers_path = answers_dir / relative_path.with_name(f"t2_{relative_path.stem[9:]}.md")

                task = process_question_file(questions_path, static_info_path, original_info_path, answers_path, context)
                tasks.append(task)

    await asyncio.gather(*tasks)

async def main(questions_base_dir, static_base_dir, original_info_base_dir, answers_base_dir, context):
    await process_directory(questions_base_dir, static_base_dir, original_info_base_dir, answers_base_dir, context)

if __name__ == "__main__":
    context = input("Name of context? ")
    questions_base_dir = Path(f"{context}_questions")
    static_base_dir = Path(f"{context}_static")
    original_info_base_dir = Path(context)
    answers_base_dir = Path(f"{context}_t2_answers")

    asyncio.run(main(questions_base_dir, static_base_dir, original_info_base_dir, answers_base_dir, context))
