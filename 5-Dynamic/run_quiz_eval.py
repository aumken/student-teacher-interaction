import argparse
from tqdm import tqdm
import glob
import json
import os
from dynamic import eval_student, TEACHER_INSTRUCTIONS

def run(context, chat_folder, question_folder, answer_folder, seed):
    def _read_file(fname):
        with open(fname, "r") as f:
            return f.read()

    results = []
    
    for chat_file in tqdm(glob.glob(f"{chat_folder}/**/chat_*.json", recursive=True)):
        question_file = chat_file.replace(chat_folder, question_folder).replace('.json', '').replace('chat_history_', 'question_').strip()
        answer_file = chat_file.replace(chat_folder, answer_folder).replace('.json', '').replace('chat_history_', 'answer_').strip()
        title = chat_file.split('/')[-1].replace('chat_history_', '').replace('.json', '').strip()
        
        questions = _read_file(question_file)
        true_answers = _read_file(answer_file)

        with open(chat_file, 'r') as f:
            chat_history = json.load(f)
        
        for i in range(1, len(chat_history) + 1, 2):
            student_answers, acc = eval_student(context, questions, chat_history[:i], true_answers, i, seed)
            results.append({'title': title, 'context': context, 'true_answer': true_answers, 'answers': student_answers, 
                            'accuracy': acc, 'turn': (i-1)//2})

    res_file = os.path.join(chat_folder, 'results.json')
    with open(res_file, 'w') as f:
        json.dump(results, f, indent=4)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set up dynamic conversation between student and teacher')
    parser.add_argument("--context", choices=list(TEACHER_INSTRUCTIONS.keys()), required=True)
    parser.add_argument("--answers-folder", required=True)
    parser.add_argument("--questions-folder", required=True)
    parser.add_argument("--results-folder", required=True)
    parser.add_argument("--seed", type=int, default=123)

    args = parser.parse_args()
    run(args.context, args.results_folder, args.questions_folder, args.answers_folder, args.aggregate_answers, args.seed)
