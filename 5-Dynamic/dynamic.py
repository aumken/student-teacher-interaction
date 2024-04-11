import os
from openai import OpenAI
import json
from dotenv import load_dotenv
import re
from utils import get_all_content
import argparse
from typing import List, Dict

TEACHER_INSTRUCTIONS = {
    "movie_plots": "Prepare the student comprehensively for any quiz on this movie plot, by answering questions on its storyline, character arcs, themes, and significant scenes. Content: {content}\n Do not ask any questions to the student, only answer the questions!",
    "image": "Equip the student for any quiz on this image by answering questions on its elements, composition, and context. Content: {content}\n Do not ask any questions to the student, only answer the questions!",
    "academic_papers": "Enable the student to excel in any quiz on this academic paper by answering any question on its objectives, methodology, findings, and significance. Content: {content}\n Do not ask any questions to the student, only answer the questions!",
    "news_articles": "Prepare the student for any quiz on this news article by answering any question on the main events, key figures, and the article's context. Content: {content}\n Do not ask any questions to the student, only answer the questions!",
    "song_lyrics": "Equip the student for any quiz on these song lyrics by answering any questions related to the narrative, themes, and expressive techniques used. Content: {content}\n Do not ask any questions to the student, only answer the questions!",
}

STUDENT_INSTRUCTIONS = {
    "movie_plots": "To learn more about the movie plot that only teacher knows about and get prepared for any quiz on that, ask questions on its storyline, character arcs, themes, and significant scenes. Ensure questions are diverse and cover all aspects. Ask one question at a time. Also, feel free to ask detailed questions about particular points to gain deeper understanding of the topic. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time. NEVER PROMPT TEACHER TO ASK ANY QUESTION, NEVER tell teacher to feel free to ask anything, they cannot ask questions, only you can ask questions!",
    "image": "To learn more about an image that only the teacher has seen and get prepared for any quiz on that image, ask detailed questions on its elements, composition, and context. Ensure questions are diverse and cover all aspects. Ask one question at a time. Also, feel free to ask detailed questions about particular points to gain deeper understanding of the topic. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time. NEVER PROMPT TEACHER TO ASK ANY QUESTION, NEVER tell teacher to feel free to ask anything, they cannot ask questions, only you can ask questions!",
    "academic_papers": "To learn more about an academic paper that only the teacher knows about and get prepared for any quiz on that, ask questions on its objectives, methodology, findings, and significance. Ensure questions are diverse and cover all aspects. Ask one question at a time. Also, feel free to ask detailed questions about particular points to gain deeper understanding of the topic. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time. NEVER PROMPT TEACHER TO ASK ANY QUESTION, NEVER tell teacher to feel free to ask anything, they cannot ask questions, only you can ask questions!",
    "news_articles": "To learn more about a news article that only the teacher knows about and get prepared for any quiz on that, ask questions on the main events, key figures, and the article's context. Ensure questions are diverse and cover all aspects. Ask one question at a time. Also, feel free to ask detailed questions about particular points to gain deeper understanding of the topic. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time. NEVER PROMPT TEACHER TO ASK ANY QUESTION, NEVER tell teacher to feel free to ask anything, they cannot ask questions, only you can ask questions!",
    "song_lyrics": "To learn more about song lyrics that only the teacher knows about and get prepared for any quiz on that, ask questions on the narrative, themes, and expressive techniques used. Ensure questions are diverse and cover all aspects. Ask one question at a time. Also, feel free to ask detailed questions about particular points to gain deeper understanding of the topic. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time. NEVER PROMPT TEACHER TO ASK ANY QUESTION, NEVER tell teacher to feel free to ask anything, they cannot ask questions, only you can ask questions!",
}

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_answer_from_teacher(context: str, content: str, message_history: List[Dict]):
    # to obtan answer from teacher, treat teacher as assistant and student as user
    new_history = list(map(lambda x: {"role": "user" if x["role"] == "student" else "assistant", 
                                          "content": x["content"]}, message_history))
    instruction = TEACHER_INSTRUCTIONS[context].format(content=content)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "system", "content": instruction}] + new_history)
    teacher_response = response.choices[0].message.content

    return teacher_response

def get_question_from_student(context, message_history):
    # to obtan question from student, treat student as assistant and teacher as user
    new_history = list(map(lambda x: {"role": "user" if x["role"] == "teacher" else "assistant", 
                                          "content": x["content"]}, message_history))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "system", "content": STUDENT_INSTRUCTIONS[context]}] + new_history)
    student_response = response.choices[0].message.content

    return student_response

def eval_student(context, questions, message_history, out_dir, n_turn):
    new_history = list(map(lambda x: {"role": "user" if x["role"] == "teacher" else "assistant", 
                                          "content": x["content"]}, message_history))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=new_history + [{"role": "system",
                   "content": f"You will be given a set of 10 multiple-choice questions based on a {context} you previously discussed. "
                   "Answer questions based on the information you inferred from previous conversation. "
                   "Please provide your answers in a single string, with each character representing your choice for the corresponding question, "
                   f"or list them numerically. For example: 'ABCDABCDAB' or '1) A 2) B 3) C ...'.\n\n",
                   }, {"role": "user", "content": questions}])
    
    raw_answers = response.choices[0].message.content.strip()

    continuous_pattern = re.compile(r"\b[A-D]{10}\b")
    listed_pattern = re.compile(r"\b\d+[).]?\s*([A-D])")

    continuous_match = continuous_pattern.search(raw_answers)
    if continuous_match:
        return continuous_match.group()

    listed_matches = listed_pattern.findall(raw_answers)
    answer_list = "".join(listed_matches) if len(listed_matches) == 10 else None

    with open(os.path.join(out_dir, f"eval_{n_turn}"), "w") as file:
        file.write(answer_list)

def run_conversation(context, content, questions, out_dir, n_turn: int = 10):
    msg_history = []
    for i in range(n_turn):
        q = get_question_from_student(context, msg_history)
        msg_history.append({"role": "student", "content": q})
        answer = get_answer_from_teacher(context, content, msg_history)
        msg_history.append({"role": "teacher", "content": answer})
        # evaluate student perf based on current conversation
        eval_student(context, questions, msg_history, out_dir, i)

    return msg_history

def run(context, n_turn, questions_path, context_folder, root_folder, out_dir):
    with open(questions_path, "r") as file:
        questions = file.read()
    
    contents = get_all_content(context, context_folder, root_folder)
    for content in contents:
        msg_history = run_conversation(context, content, questions, out_dir, n_turn)
        # save msg_history
        with open(os.path.join(out_dir, f"chat_history.json"), "w") as f:
            json.dump(msg_history, f, indent=6)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set up dynamic conversation between student and teacher')
    parser.add_argument("--context", choices=list(TEACHER_INSTRUCTIONS.keys()), required=True)
    parser.add_argument("--num-turns", type=int, default=10, required=False)
    parser.add_argument("--questions-path", required=False)
    parser.add_argument("--context-folder", required=True)
    parser.add_argument("--root-folder", required=True)
    parser.add_argument("--output-folder", required=True)

    args = parser.parse_args()
    run(args.context, args.num_turns, args.questions_path, args.context_folder, args.root_folder, args.output_folder)
