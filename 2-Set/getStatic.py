# getStatic.py
import asyncio
import base64
import os

import httpx
import pdfplumber
import PyPDF2
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pdfminer.psparser import PSEOF

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

instructions = {
    "movie_plots": "Prepare the student comprehensively for any quiz on this movie plot, by explaining its storyline, character arcs, themes, and significant scenes. Your explanation should cover all essential aspects, enabling the student to confidently answer questions on any part of the movie.",
    "images": "Equip the student for any quiz on this image by providing a detailed analysis of its elements, composition, and context. Highlight the key features and underlying messages, ensuring the student can address questions related to any aspect of the image.",
    "academic_papers": "Enable the student to excel in any quiz on this academic paper by summarizing its objectives, methodology, findings, and significance. Your summary should comprehensively cover the paper's content, preparing the student to tackle questions on any part of the study.",
    "news_articles": "Prepare the student for any quiz on this news article by outlining the main events, key figures, and the article's context. Ensure your summary is thorough, allowing the student to respond to questions on any detail of the article.",
    "song_lyrics": "Equip the student for any quiz on these song lyrics by dissecting the narrative, themes, and expressive techniques used. Provide a complete understanding, enabling the student to engage with questions on any aspect of the lyrics.",
}


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


async def generate_static(context, plot):
    inst = instructions[context]

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            seed=123,
            messages=[
                {"role": "system", "content": inst},
                {"role": "user", "content": plot},
            ],
        )
        static_content = response.choices[0].message.content
        return static_content
    except Exception as e:
        print(f"Error generating static content for {context}: {e}")
        return None


def save_to_file(content, folder, filename):
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def generate_description_from_image(context, image_path):
    inst = instructions[context]
    base64_image = encode_image(image_path)

    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            seed=123,
            messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": inst},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ],
        )
        static_content = response.choices[0].message.content
        return static_content
    except Exception as e:
        print(f"Error generating static content for {context}: {e}")
        return None


async def process_file(context, filepath, static_folder):
    filename = os.path.basename(filepath)
    base_filename = filename.rsplit(".", 1)[0]
    static_filename = f"static_{base_filename}.md"

    # Check if the file already exists to avoid re-processing
    if os.path.exists(os.path.join(static_folder, static_filename)):
        return

    # Process based on file type
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
    elif filepath.endswith((".jpg", ".jpeg")):  # Handle both .jpg and .jpeg
        static_content = await generate_description_from_image(context, filepath)
        if static_content:
            save_to_file(static_content, static_folder, static_filename)
        else:
            print(f"Failed to generate static content for {filepath}")
    elif filepath.endswith(".md"):  # Handle .md files
        with open(filepath, "r") as file:
            plot = file.read()
    else:
        print(f"Unsupported file type for {filepath}")  # Debugging print
        return

    if not filepath.endswith((".jpg", ".jpeg")):
        static_content = await generate_static(context, plot)
        if static_content:
            save_to_file(static_content, static_folder, static_filename)
        else:
            print(f"No static content generated for {filepath}")  # Debugging print


async def process_directory(context, folder, static_folder_base):
    print(f"Starting directory processing for {folder}")
    tasks = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith((".md", ".pdf", ".jpg", ".jpeg")):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, folder)
                static_folder = os.path.join(static_folder_base, context, relative_path)
                tasks.append(process_file(context, file_path, static_folder))
    await asyncio.gather(*tasks)


async def main():
    root_folder = "a_files"
    static_folder_base = "d_static"
    for context in os.listdir(root_folder):
        context_folder = os.path.join(root_folder, context)
        if os.path.isdir(context_folder):
            await process_directory(context, context_folder, static_folder_base)


if __name__ == "__main__":
    asyncio.run(main())
