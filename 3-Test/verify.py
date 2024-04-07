import os


def check_answer_file(file_path):
    """Check that an answer file contains exactly 10 answers."""
    with open(file_path, "r", encoding="utf-8") as file:
        answers = file.read().strip()
        if len(answers) != 10 or not all(answer in "ABCD" for answer in answers):
            print(f"Verification failed for answer file: {file_path}")


def verify_files(base_directory, base_mcq_folder, base_answer_folder):
    prefix=""
    if base_answer_folder == "c_answers": prefix = "answer"
    elif base_answer_folder == "s1_answers": prefix = "s1"
    elif base_answer_folder == "s2_answers": prefix = "s2"
    elif base_answer_folder == "t1_answers": prefix = "t1"
    elif base_answer_folder == "t2_answers": prefix = "t2"

    for context in os.listdir(base_directory):
        context_path = os.path.join(base_directory, context)
        if os.path.isdir(context_path):
            for root, dirs, files in os.walk(context_path):
                relative_path = os.path.relpath(root, start=base_directory)
                mcq_folder = os.path.join(base_mcq_folder, relative_path)
                answer_folder = os.path.join(base_answer_folder, relative_path)

                for file in files:
                    if file.endswith(".md"):
                        mcq_file_path = os.path.join(mcq_folder, f"question_{file}")
                        answer_file_path = os.path.join(answer_folder, f"{prefix}_{file}")

                        if not os.path.exists(mcq_file_path):
                            print(f"Missing MCQ file: {mcq_file_path}")
                        if not os.path.exists(answer_file_path):
                            print(f"Missing Answer file: {answer_file_path}")
                        else:
                            check_answer_file(answer_file_path)


if __name__ == "__main__":
    base_directory = "a_files"  # Directory containing all contexts
    base_mcq_folder = "b_questions"  # Directory where questions are stored
    dirs = ["s1", "s2", "t1", "t2"]
    for directory in dirs:
        base_answer_folder = f"{directory}_answers"  # Directory where answers are stored
        verify_files(base_directory, base_mcq_folder, base_answer_folder)
