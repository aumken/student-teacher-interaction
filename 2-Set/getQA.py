import asyncio
import os

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
            answer = line.split("Correct Answer:")[1].strip()
            if answer in ["A", "B", "C", "D"]:
                answers.append(answer)
        else:
            mcqs.append(line)


    return "\n".join(mcqs), "".join(answers)


def save_to_file(content, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(os.path.join(folder, filename), "w") as file:
        file.write(content)


async def process_file(context, filepath, mcq_folder, answer_folder):
    filename = os.path.basename(filepath)
    questions_filename = "question_" + filename
    answers_filename = "answer_" + filename

    if os.path.exists(os.path.join(mcq_folder, questions_filename)) and os.path.exists(
        os.path.join(answer_folder, answers_filename)
    ):
        return  # Skip if both files already exist

    with open(filepath, "r") as file:
        plot = file.read()

    attempts = 0
    max_attempts = 5  # Set a limit to prevent infinite loops
    while attempts < max_attempts:
        mcq_and_answers = await generate_mcq(context, plot)
        if mcq_and_answers:
            mcqs, answers = separate_mcqs_and_answers(mcq_and_answers)
            if len(answers) == 10:
                save_to_file(mcqs, mcq_folder, questions_filename)
                save_to_file(
                    answers, answer_folder, answers_filename
                )  # Save just the answers if there are exactly 10
                if attempts >= 1:
                    print(f"Attempt {attempts + 1}: Worked for {filename}.")
                break  # Exit the loop if 10 answers are found
            else:
                print(
                    f"Attempt {attempts + 1}: Not exactly 10 answers for {filename}."
                )
        attempts += 1

    if attempts == max_attempts:
        print(
            f"Warning: Unable to get exactly 10 answers for {filename} after {max_attempts} attempts. Saving the last attempt."
        )
        save_to_file(
            mcq_and_answers, answer_folder, answers_filename
        )  # Save the last attempt regardless of answer count


async def process_directory(
    context, folder, mcq_folder_base, answer_folder_base, root_folder
):
    for root, dirs, files in os.walk(folder):
        # Get the relative path from the root folder to the current directory
        rel_path = os.path.relpath(root, root_folder)

        # Construct the mcq and answer folders by joining the base folder with the relative path
        mcq_folder = os.path.join(mcq_folder_base, rel_path)
        answer_folder = os.path.join(answer_folder_base, rel_path)

        os.makedirs(mcq_folder, exist_ok=True)
        os.makedirs(answer_folder, exist_ok=True)

        tasks = [
            process_file(context, os.path.join(root, file), mcq_folder, answer_folder)
            for file in files
            if file.endswith(".md")
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
