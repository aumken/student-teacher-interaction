# s1.py
import asyncio
import os
import re
from pathlib import Path

import aiofiles
import random
import ujson
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

# Initialize the OpenAI client with your API key
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Precompiled regex patterns
continuous_pattern = re.compile(r"^[A-D]+$", re.MULTILINE)
listed_pattern = re.compile(r"^\d+\)\s*([A-D])\s*$", re.MULTILINE)
dot_pattern = re.compile(r"^\d+\.\s*([A-D])\s*$", re.MULTILINE)


async def get_model_answers(questions, context, max_retries=3, seed=123):
    model = "gpt-4o" if context == "images" else "gpt-3.5-turbo"
    expected_answers = 5 if context == "images" else 10
    retries = 0
    random.seed(seed)
    seeds = [random.randint(0, 1000) for i in range(10)]
    while retries < max_retries:
        try:
            response = await client.chat.completions.create(
                model=model,
                seed=seeds.pop(),
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You will be given a set of {expected_answers} multiple-choice questions regarding a {context}. "
                            f"Please provide your answers in the following format:\n\n"
                            f"1. A single string of {expected_answers} capital letters (A, B, C, or D) representing your choices for each question. For example: ABCDABCDAB\n\n"
                            f"OR\n\n"
                            f"2. A numbered list with the question number followed by a closing parenthesis or a dot, a space, and then the capital letter (A, B, C, or D) representing your choice. For example:\n"
                            f"1) A\n2) B\n3) C\n...\n\n"
                            f"Even if you feel you lack context, make an educated guess for each answer. You must provide exactly {expected_answers} answers, one for each question, and use only the specified formats."
                        ),
                    },
                    {"role": "user", "content": questions},
                ],
            )
            raw_answers = response.choices[0].message.content.strip()
            continuous_match = continuous_pattern.search(raw_answers)
            if continuous_match:
                return continuous_match.group()
            # Combine listed and dot patterns
            listed_matches = listed_pattern.findall(raw_answers) + dot_pattern.findall(
                raw_answers
            )
            if len(listed_matches) == expected_answers:
                return "".join(match.strip() for match in listed_matches)
            retries += 1
        except Exception as e:
            print(f"Error: {e}")
            retries += 1
    print(
        f"Failed to generate answers after {max_retries} retries for context: {questions[:50]}"
    )
    print(f"Invalid answers format: {raw_answers}")
    return None


async def process_question_file(questions_path, answers_path, context, seed = 123):
    expected_answers = 5 if context == "images" else 10

    # Check if the answers file already exists and has the expected number of answers
    if answers_path.exists():
        async with aiofiles.open(answers_path, "r") as file:
            existing_answers = await file.read()
        if len(existing_answers) == expected_answers and all(
            answer in "ABCD" for answer in existing_answers
        ):
            return

    async with aiofiles.open(questions_path, "r") as file:
        questions = await file.read()
    model_answers = await get_model_answers(questions, context, seed)
    if model_answers and len(model_answers) == expected_answers:
        Path(answers_path.parent).mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(answers_path, "w") as file:
            await file.write(model_answers)


async def process_directory(context, questions_dir, answers_dir, seed = 123):
    print(f"Starting directory processing for {questions_dir}")
    tasks = []
    for root, _, files in os.walk(questions_dir):
        for file in files:
            if file.startswith("question_") and file.endswith(".md"):
                questions_path = Path(root) / file
                relative_path = questions_path.relative_to(questions_dir)
                answers_path = answers_dir / relative_path.with_name(
                    f"s1_{relative_path.stem[9:]}.md"
                )
                task = asyncio.create_task(
                    process_question_file(questions_path, answers_path, context, seed)
                )
                tasks.append(task)
    await asyncio.gather(*tasks)


async def main(questions_base_dir, answers_base_dir, seed = 123):
    for context in os.listdir(questions_base_dir):
        context_questions_dir = questions_base_dir / context
        if context_questions_dir.is_dir():
            context_answers_dir = answers_base_dir / context
            await process_directory(context, context_questions_dir, context_answers_dir, seed)


if __name__ == "__main__":
    seed = 915
    questions_base_dir = Path("data/b_questions")
    answers_base_dir = Path("s1_answers")
    asyncio.run(main(questions_base_dir, answers_base_dir, seed))
