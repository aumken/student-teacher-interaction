import asyncio
import os
import re
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from openai import AsyncOpenAI

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  # Replace with your actual API key


async def get_model_answers(questions, info, context):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You will be given a brief lesson of a {context} and a set of 10 multiple-choice questions based on it. "
                    "Please provide your answers in a single string, with each character representing your choice for the corresponding question, "
                    f"or list them numerically. For example: 'ABCDABCDAB' or '1) A 2) B 3) C ...'.\n\n Lesson: {info}\n",
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


async def process_question_file(questions_path, static_info_path, output_path, context):
    if not os.path.exists(static_info_path):
        print(
            f"Skipping {Path(questions_path).name} due to missing static information file."
        )
        return

    async with aiofiles.open(static_info_path, "r") as file:
        info = await file.read()

    async with aiofiles.open(questions_path, "r") as file:
        questions = await file.read()

    model_answers = await get_model_answers(questions, info, context)
    if model_answers and len(model_answers) == 10:
        async with aiofiles.open(output_path, "w") as file:
            await file.write(model_answers)


async def process_directory(questions_dir, static_dir, answers_dir):
    tasks = []  # Initialize an empty list to hold tasks

    for root, _, files in os.walk(questions_dir):
        for file in files:
            if file.startswith("question_") and file.endswith(".md"):
                question_path = Path(root) / file
                relative_path = question_path.relative_to(questions_dir)
                static_info_path = static_dir / relative_path.with_name(
                    f"static_{relative_path.stem[9:]}.md"
                )  # Adjust for the correct static info filename
                output_path = (
                    answers_dir
                    / relative_path.parent
                    / f"s2_{relative_path.stem[9:]}.md"
                )  # Adjust for the correct answers filename

                # Ensure the parent directory for the output file exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                context = relative_path.parts[
                    0
                ]  # Assuming the first part of the path is the context

                # Create a task for processing each file and add it to the tasks list
                task = process_question_file(
                    question_path, static_info_path, output_path, context
                )
                tasks.append(task)

    # Use asyncio.gather to run all tasks concurrently
    await asyncio.gather(*tasks)


async def main():
    questions_base_dir = "b_questions"  # Base directory for questions
    static_base_dir = "d_static"  # Base directory for static information
    answers_base_dir = "s2_answers"  # Base directory for answers

    await process_directory(questions_base_dir, static_base_dir, answers_base_dir)


if __name__ == "__main__":
    asyncio.run(main())
