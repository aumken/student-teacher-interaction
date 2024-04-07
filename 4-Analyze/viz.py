import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


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

    return pd.DataFrame(analytics_rows)


def calculate_analytics(df, columns, label):
    analytics_data = []
    for column in columns:
        scores = df[column].apply(lambda x: int(x.split("/")[0]) if "/" in x else 0)
        analytics_row = {"Subcategory": f"{label} {column} Analytics"}
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
base_dir = os.path.join(script_dir, "..", "a_files")
static_dir = os.path.join(script_dir, "..", "d_static")
questions_dir = os.path.join(script_dir, "..", "b_questions")
answers_dir = os.path.join(script_dir, "..", "c_answers")
s1_answers_dir = os.path.join(script_dir, "..", "s1_answers")
s2_answers_dir = os.path.join(script_dir, "..", "s2_answers")
t1_answers_dir = os.path.join(script_dir, "..", "t1_answers")
t2_answers_dir = os.path.join(script_dir, "..", "t2_answers")

columns = [
    "Subcategory",
    "Name/Title",
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
                if file.endswith(".md") or file.endswith(".pdf"):
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

    # After processing all files in the folder and creating 'df'
    df = pd.DataFrame(df_rows, columns=columns)

    # Add subcategory and overall analytics
    score_columns = ["S1 Score", "S2 Score", "T1 Score", "T2 Score"]
    analytics_df = add_analytics(df, score_columns)

    # Concatenate original data with analytics
    df_with_analytics = pd.concat(
        [df, pd.DataFrame([{}]), analytics_df], ignore_index=True
    )

    final_dir = os.path.join(script_dir, "..", "viz")
    if not os.path.exists(final_dir):
        os.makedirs(final_dir)
        
    # Save the Excel file
    excel_path = os.path.join(final_dir, f"{folder}.xlsx")
    df_with_analytics.to_excel(excel_path, index=False)
    print(f"Spreadsheet created for {folder}")
