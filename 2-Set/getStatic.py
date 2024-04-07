import asyncio
import os

import PyPDF2
from dotenv import load_dotenv
from openai import AsyncOpenAI

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

instructions = {
    "movie_plots": "Prepare the student comprehensively for any quiz on this movie plot, by explaining its storyline, character arcs, themes, and significant scenes. Your explanation should cover all essential aspects, enabling the student to confidently answer questions on any part of the movie.",
    "image": "Equip the student for any quiz on this image by providing a detailed analysis of its elements, composition, and context. Highlight the key features and underlying messages, ensuring the student can address questions related to any aspect of the image.",
    "academic_papers": "Enable the student to excel in any quiz on this academic paper by summarizing its objectives, methodology, findings, and significance. Your summary should comprehensively cover the paper's content, preparing the student to tackle questions on any part of the study.",
    "news_articles": "Prepare the student for any quiz on this news article by outlining the main events, key figures, and the article's context. Ensure your summary is thorough, allowing the student to respond to questions on any detail of the article.",
    "song_lyrics": "Equip the student for any quiz on these song lyrics by dissecting the narrative, themes, and expressive techniques used. Provide a complete understanding, enabling the student to engage with questions on any aspect of the lyrics.",
}


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


async def generate_static(context, plot):
    inst = instructions[context]

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": inst},
                {"role": "user", "content": plot},
            ],
        )
        static_content = response.choices[0].message.content
        return static_content.replace("*", "")
    
    except Exception as e:
        print(
            f"Error generating static content for {context}: {e}"
        )
        return None


def save_to_file(content, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(os.path.join(folder, filename), "w") as file:
        file.write(content)


async def process_file(context, filepath, root_folder):
    # Extract text from PDF or read from Markdown file
    if filepath.endswith(".pdf"):
        plot = extract_text_from_pdf(filepath)
    else:
        with open(filepath, "r") as file:
            plot = file.read()

    rel_path = os.path.relpath(filepath, start=root_folder)
    base_name = os.path.basename(filepath)
    static_folder = os.path.join(f"d_static", os.path.dirname(rel_path))

    # Ensure the output filename uses .md extension
    static_filename = f"static_{os.path.splitext(base_name)[0]}.md"

    static_content = await generate_static(context, plot)
    if static_content:
        save_to_file(static_content, static_folder, static_filename)


async def process_directory(context, folder, root_folder):
    for root, dirs, files in os.walk(folder):
        tasks = [
            process_file(context, os.path.join(root, file), root_folder)
            for file in files
            if file.endswith(".md")
            or file.endswith(".pdf")  # Include PDF files as well
        ]
        await asyncio.gather(*tasks)


async def main():
    root_folder = "a_files"

    for context in os.listdir(root_folder):
        context_folder = os.path.join(root_folder, context)
        if os.path.isdir(context_folder) and context in instructions:
            await process_directory(context, context_folder, root_folder)


if __name__ == "__main__":
    asyncio.run(main())
