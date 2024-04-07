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


async def get_model_answers(questions, context):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You will be given a set of 10 multiple-choice questions regarding a {context}. "
                        "Please provide your answers in a single string, with each character representing your choice for the corresponding question, "
                        "or list them numerically. For example: 'ABCDABCDAB' or '1) A 2) B 3) C ...'."
                    ),
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

        return "None"

    except Exception as e:
        print(f"Error: {e}")
        return None


async def process_question_file(
    questions_path, answers_path, context
):

    async with aiofiles.open(questions_path, "r") as file:
        questions = await file.read()

    model_answers = await get_model_answers(questions, context)
    if model_answers and len(model_answers) == 10:
        Path(answers_path.parent).mkdir(
            parents=True, exist_ok=True
        )  # Ensure the answers directory exists
        async with aiofiles.open(answers_path, "w") as file:
            await file.write(model_answers)


async def process_directory(questions_dir, answers_dir):
    tasks = []  # Initialize an empty list to hold tasks

    for root, _, files in os.walk(questions_dir):
        for file in files:
            if file.startswith("question_") and file.endswith(".md"):
                questions_path = Path(root) / file
                relative_path = questions_path.relative_to(questions_dir)
                answers_path = answers_dir / relative_path.with_name(
                    f"s1_{relative_path.stem[9:]}.md"
                )  # Adjust for the correct answers filename

                context = relative_path.parts[
                    0
                ]  # Assuming the first part of the path is the context

                # Create a task for processing each file and add it to the tasks list
                task = process_question_file(
                    questions_path, answers_path, context
                )
                tasks.append(task)

    # Use asyncio.gather to run all tasks concurrently
    await asyncio.gather(*tasks)


async def main(questions_base_dir, answers_base_dir):
    await process_directory(questions_base_dir, answers_base_dir)


if __name__ == "__main__":
    questions_base_dir = Path(
        "b_questions"
    )  # Base directory containing question files organized by context, possibly with nested subdirectories
    answers_base_dir = Path(
        "s1_answers"
    )  # Base directory for storing answers, which will mirror the structure of b_questions
    asyncio.run(main(questions_base_dir, answers_base_dir))
