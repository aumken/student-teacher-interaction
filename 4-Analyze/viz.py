import base64
import os
import re

import matplotlib.pyplot as plt
import pandas as pd
import pdfplumber
import PyPDF2
from pdfminer.psparser import PSEOF  # Import the PSEOF exception
from PIL import Image


def remove_illegal_chars(text):
    # Removes non-printable characters from a string
    return re.sub(r"[^\x20-\x7E]", "", text)


def clean_content(content):
    if isinstance(content, str):
        return remove_illegal_chars(content)
    else:
        return content  # Assuming non-string content is already clean


def parse_score(score_str):
    correct, total = map(int, score_str.split("/"))
    if total == 0:
        return 0, 0
    return correct, correct / total


def add_analytics(df, score_columns):
    # Initialize a list to hold all analytics rows
    analytics_rows = []

    # Group by 'Subcategory' and calculate analytics for each group
    for subcategory, group in df.groupby("Subcategory"):
        if subcategory == "": break
        subcategory_analytics = calculate_analytics(group, score_columns, subcategory)
        analytics_rows.extend(subcategory_analytics)

    # Calculate overall analytics (ignoring subcategory)
    overall_analytics = calculate_analytics(df, score_columns, "Overall")
    analytics_rows.extend(overall_analytics)

    overall_analytics_df = pd.DataFrame(overall_analytics)


    plt.figure()  # Create a new figure for the plot
    plt.plot(
        overall_analytics_df["Subcategory"],
        overall_analytics_df["Mean Score"],
        label="Mean",
    )
    plt.plot(
        overall_analytics_df["Subcategory"],
        overall_analytics_df["Median Score"],
        label="Median",
    )
    plt.plot(
        overall_analytics_df["Subcategory"],
        overall_analytics_df["Mode Score"],
        label="Mode",
    )
    plt.plot(
        overall_analytics_df["Subcategory"],
        overall_analytics_df["Std Dev Score"],
        label="Std Dev",
    )

    plt.xlabel("Assessment")
    plt.ylabel("Score (0-10)")
    plt.title("Overall Score Analytics")
    plt.legend()
    plt.tight_layout()  # Adjust layout to prevent overlapping labels
    plt.savefig(
        os.path.join(final_dir, f"{folder}_overall_analytics.png")
    )  # Save the plot

    return pd.DataFrame(analytics_rows)


def calculate_analytics(df, columns, label):
    analytics_data = []
    for column in columns:
        scores = df[column].apply(lambda x: int(x.split("/")[0]) if "/" in x else 0)
        analytics_row = {"Subcategory": f"{label} {column}"}
        analytics_row.update(
            {
                "Mean Score": scores.mean(),
                "Median Score": scores.median(),
                "Mode Score": (
                    scores.mode().iloc[0] if not scores.mode().empty else "N/A"
                ),
                "Std Dev Score": scores.std(),
                "25th Percentile Score": scores.quantile(0.25),
                "50th Percentile Score": scores.quantile(0.5),
                "75th Percentile Score": scores.quantile(0.75),
            }
        )
        analytics_data.append(analytics_row)
    return analytics_data


def read_first_line(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.readline().strip()
    except FileNotFoundError:
        return ""


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""


def calculate_score(original, student):
    original_answers = original.replace("\n", "")
    student_answers = student.replace("\n", "")
    correct = sum(1 for o, s in zip(original_answers, student_answers) if o == s)
    total = len(original_answers)
    return f"{correct}/{total}" if total > 0 else "0/0"


script_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, "..", "a_files"))
static_dir = os.path.join(script_dir, "..", "d_static")
questions_dir = os.path.join(script_dir, "..", "b_questions")
answers_dir = os.path.join(script_dir, "..", "c_answers")
s1_answers_dir = os.path.join(script_dir, "..", "s1_answers")
s2_answers_dir = os.path.join(script_dir, "..", "s2_answers")
t1_answers_dir = os.path.join(script_dir, "..", "t1_answers")
t2_answers_dir = os.path.join(script_dir, "..", "t2_answers")
final_dir = os.path.join(script_dir,'..', "viz")
if not os.path.exists(final_dir):
    os.makedirs(final_dir)

columns = [
    "Subcategory",
    "Name/Title",
    "Content",
    "Static",
    "Questions",
    "Answers",
    "S1 Answers",
    "S1 Score",
    "S2 Answers",
    "S2 Score",
    "T1 Answers",
    "T1 Score",
    "T2 Answers",
    "T2 Score",
]

for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue

    df_rows = []  # Initialize df_rows for each folder

    subfolders = [
        f
        for f in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, f))
    ]
    process_folders = (
        [(folder_path, subfolders)] if subfolders else [(folder_path, [""])]
    )

    for current_folder, folders in process_folders:
        for subfolder in folders:
            subfolder_path = (
                os.path.join(current_folder, subfolder) if subfolder else current_folder
            )
            for file in os.listdir(subfolder_path):
                if (
                    file.endswith(".md")
                    or file.endswith(".pdf")
                    or file.endswith(".jpg")
                ):
                    file_base_name = os.path.splitext(file)[0]
                    subcategory = subfolder if subfolder else ""
                    md_extension = ".md"

                    # Include the subfolder in the path for static, question, and answer files
                    static_file = os.path.join(
                        static_dir,
                        folder,
                        subcategory,
                        f"static_{file_base_name}{md_extension}",
                    )
                    question_file = os.path.join(
                        questions_dir,
                        folder,
                        subcategory,
                        f"question_{file_base_name}{md_extension}",
                    )
                    answer_file = os.path.join(
                        answers_dir,
                        folder,
                        subcategory,
                        f"answer_{file_base_name}{md_extension}",
                    )

                    static_content = read_first_line(static_file)
                    question_content = read_first_line(question_file)
                    original_answers = read_file_content(answer_file)

                    answer_scores = {}
                    for prefix, answer_dir in zip(
                        ["s1", "s2", "t1", "t2"],
                        [
                            s1_answers_dir,
                            s2_answers_dir,
                            t1_answers_dir,
                            t2_answers_dir,
                        ],
                    ):
                        student_answer_file = os.path.join(
                            answer_dir,
                            folder,
                            subcategory,
                            f"{prefix}_{file_base_name}{md_extension}",
                        )
                        student_answers = read_file_content(student_answer_file)
                        score = calculate_score(original_answers, student_answers)
                        answer_scores[f"{prefix.upper()} Answers"] = student_answers
                        answer_scores[f"{prefix.upper()} Score"] = score

                    row_data = {
                        "Subcategory": subcategory,
                        "Name/Title": file_base_name,
                        "Static": static_content,
                        "Questions": question_content,
                        "Answers": original_answers,
                        **answer_scores,
                    }
                    df_rows.append(row_data)  # Add row data for the current file

    def read_pdf_content(file_path, char_limit=1500):
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
                    if len(text) >= char_limit:
                        break
        except PSEOF:  # Catch the PSEOF exception
            pass  # Continue to the next line
        return text[:char_limit]

    def read_image_dimensions(file_path):
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                return f"{width}x{height}"
        except Exception as e:
            print(f"Error reading image file {file_path}: {e}")
            return ""

    def read_image_as_base64(file_path):
        try:
            with open(file_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                return f"data:image/jpg;base64,{encoded_string}"
        except Exception as e:
            print(f"Error reading image file {file_path}: {e}")
            return ""

    def read_content(file_path, char_limit=1500):
        if file_path.endswith('.pdf'):
            return read_pdf_content(file_path, char_limit)
        elif file_path.endswith('.md'):
            return read_file_content(file_path)
        # Add a condition for JPG files
        elif file_path.endswith('.jpg'):
            # Option 1: Return base64 encoded image
            return read_image_as_base64(file_path)

            # Option 2: Return image dimensions (previous behavior)
            # return read_image_dimensions(file_path)
        else:
            return "Unsupported file type"

    def add_file_content(df, base_dir):
        for index, row in df.iterrows():
            # Check for both '.md' and '.pdf' file extensions
            for ext in ['.md', '.pdf', '.jpg']:
                # Adjusted to include both folder (main category) and subfolder (subcategory)
                file_content_path = os.path.join(base_dir, folder, row['Subcategory'], f"{row['Name/Title']}{ext}")
                if os.path.exists(file_content_path):
                    file_content = read_content(file_content_path)
                    df.at[index, 'Content'] = file_content
                    break  # Found the file, no need to check the next extension
        return df

    # After creating the initial dataframe 'df'
    df = pd.DataFrame(df_rows, columns=columns)

    # Call add_file_content to populate the 'Content' column
    df = add_file_content(df, base_dir)

    # Add subcategory and overall analytics
    score_columns = ["S1 Score", "S2 Score", "T1 Score", "T2 Score"]
    analytics_df = add_analytics(df, score_columns)

    # Use this function to clean content in your dataframe before saving it to Excel
    df["Content"] = df["Content"].apply(clean_content)
    df["Static"] = df["Static"].apply(clean_content)
    df["Questions"] = df["Questions"].apply(clean_content)
    df["Answers"] = df["Answers"].apply(clean_content)
    df["S1 Answers"] = df["S1 Answers"].apply(clean_content)
    df["S2 Answers"] = df["S2 Answers"].apply(clean_content)
    df["T1 Answers"] = df["T1 Answers"].apply(clean_content)
    df["T2 Answers"] = df["T2 Answers"].apply(clean_content)
    # Apply this cleaning process to any other text columns you intend to write to Excel

    # Then continue with concatenating dataframes and saving to Excel
    df_with_analytics = pd.concat([df, pd.DataFrame([{}]), analytics_df], ignore_index=True)

    final_dir = os.path.join(script_dir,'..', "viz")
    if not os.path.exists(final_dir):
        os.makedirs(final_dir)

    # Save the Excel file
    excel_path = os.path.join(final_dir, f"{folder}.xlsx")
    df_with_analytics.to_excel(excel_path, index=False)
    print(f"Spreadsheet created for {folder}")
