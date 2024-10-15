import os
from openai import OpenAI
import argparse
from tqdm import tqdm

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def read_file(filepath):
    with open(filepath, 'r') as file:
        return file.read()

def write_file(filepath, content):
    with open(filepath, 'w') as file:
        file.write(content.replace('\\n', '\n'))

def format_lyrics(input_text):
    prompt = f"""Given the lyrics for the song, return a python string with newline characters inserted where appropriate.\n\nExample:\n\nInput: I say, ohI don't miss you anymoreOh noWhen you walked out the doorI cried for the longest timeBut trust me, now I'm fineOh noI don't miss you anymore[Verse 1]I don't wanna think about youI don't wanna talkI don't wanna hear your name againI don't wanna picture you with someone elseBut I know that's the way this story ends (Whoa)[Pre-Chorus]Somewhere along the lineI broke your heart and you broke mineOne too many times to stay (Whoa)It took a couple tries to start believing my own liesBut when my friends ask if I'm okay[Chorus]I say, ohI don't miss you anymoreOh noWhen you walked out the doorI cried for the longest timeBut trust me, now I'm fineOh noI don't miss you anymore\n\nOutput: "I say, oh\\nI don't miss you anymore\\nOh no\\nWhen you walked out the door\\nI cried for the longest time\\nBut trust me, now I'm fine\\nOh no\\nI don't miss you anymore\\n\\n[Verse 1]\\nI don't wanna think about you\\nI don't wanna talk\\nI don't wanna hear your name again\\nI don't wanna picture you with someone else\\nBut I know that's the way this story ends (Whoa)\\n\\n[Pre-Chorus]\\nSomewhere along the line\\nI broke your heart and you broke mine\\nOne too many times to stay (Whoa)\\nIt took a couple tries to start believing my own lies\\nBut when my friends ask if I'm okay\\n\\n[Chorus]\\nI say, oh\\nI don't miss you anymore\\nOh no\\nWhen you walked out the door\\nI cried for the longest time\\nBut trust me, now I'm fine\\nOh no\\nI don't miss you anymore\n\nNow, you will be given a new song's lyrics. Please perform the same operation.\n\nInput: {input_text}\n\nOutput:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the generated text
    formatted_lyrics = response.choices[0].message.content.strip()
    
    return formatted_lyrics

def main(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in tqdm(os.listdir(input_folder)):
        if filename.endswith(".md"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # Read the content of the input file
            input_content = read_file(input_path)

            # Format the lyrics using OpenAI API
            formatted_lyrics = format_lyrics(input_content)

            # Write the formatted lyrics to the output file
            write_file(output_path, formatted_lyrics)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format song lyrics using OpenAI API.")
    parser.add_argument('input_folder', type=str, help='The folder containing input .md files.')
    parser.add_argument('output_folder', type=str, help='The folder to save the formatted .md files.')

    args = parser.parse_args()

    main(args.input_folder, args.output_folder)
