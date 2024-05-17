import os
from openai import OpenAI
import json
from dotenv import load_dotenv
import re
from utils import get_all_content, get_all_data
import argparse
from typing import List, Dict
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
import torch
import nltk

nltk.data.path.append('.')

TEACHER_INSTRUCTIONS = {
    "movie_plots": "Prepare the student comprehensively for any quiz on this movie plot, by answering questions on its storyline, character arcs, themes, and significant scenes. Content: {content}\n Do not ask any questions to the student, only answer the questions! Generate long and detailed answers! Include specific event and character-related details in your answers like what happened, who performed specific actions, and who was involved.",
    "image": "Prepare the student comprehensively for any quiz on this image, by answering questions on its elements, composition, and context. Content: {content}\n Do not ask any questions to the student, only answer the questions! Generate long and detailed answers!",
    "academic_papers": "Prepare the student comprehensively for any quiz on this academic paper, by answering questions on its objectives, methodology, findings, and significance. Content: {content}\n Do not ask any questions to the student, only answer the questions! Generate long and detailed answers!",
    "news_articles": "Prepare the student comprehensively for any quiz on this news article, by answering questions on the main events, key figures, and the article's context. Content: {content}\n Do not ask any questions to the student, only answer the questions! Generate long and detailed answers! Include specific event-related details in your answers like what happened, who performed specific actions, and who was involved.",
    "song_lyrics": "Prepare the student comprehensively for any quiz on this movie plot, by answering questions on the narrative, themes, and expressive techniques used. Content: {content}\n Do not ask any questions to the student, only answer the questions! Generate long and detailed answers!",
}

STUDENT_INSTRUCTIONS = {
    "movie_plots": "To learn more about the movie plot known only to the teacher and get prepared for any quiz on that, ask questions on its storyline, character arcs, themes, and significant scenes. Ask diverse questions encompassing plot progression, character actions, involvement, thematic exploration, and character motivations. Include questions seeking specific details such as character names, objects, settings, and dates. Include questions that prompt thorough analysis of the plot and a deeper comprehension of its unfolding events. Ensure questions are diverse and comprehensive, covering all facets of the movie. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time! NEVER PROMPT TEACHER TO ASK ANY QUESTION!",
    "image": "To learn more about the image known only to the teacher and get prepared for any quiz on that, ask questions on its elements, composition, and context. Ask diverse questions encompassing symbolism, meaning, theme and actions depicted in the image. Include questions seeking specific details such as presence and placement of objects. Include questions that prompt thorough analysis of the image. Ensure questions are diverse and comprehensive, covering all facets of the image. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time! NEVER PROMPT TEACHER TO ASK ANY QUESTION!",
    "academic_papers": "To learn more about the academic paper known only to the teacher and get prepared for any quiz on that, ask questions on its objectives, methodology, findings, and significance. Ask diverse questions encompassing experiments, its relation to prior studies, limitations, motivation and key takeaways. Include questions seeking specific details such as experimental setup. Include questions that prompt thorough analysis of the paper and a deeper understanding of its broader contributions. Ensure questions are diverse and comprehensive, covering all aspects of the paper. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time! NEVER PROMPT TEACHER TO ASK ANY QUESTION!",
    "news_articles": "To learn more about the news article known only to the teacher and get prepared for any quiz on that, ask questions on the main events, key figures, and the article's context. Ask diverse questions encompassing background stories and broader implications. Include questions seeking specific details such as names of individuals, events, actions, and dates. Include questions that prompt thorough analysis of the article and a deeper comprehension of unfolding events. Ensure questions are diverse and comprehensive, covering all aspects of the article. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time! NEVER PROMPT TEACHER TO ASK ANY QUESTION!",
    "song_lyrics": "To learn more about song lyrics known only to the teacher knows about and get prepared for any quiz on that, ask questions on its narrative, themes, and expressive techniques used. Ask diverse questions encompassing emotions, individuals, events, involvement, themes and references to other content. Include questions that prompt thorough analysis of the lyrics and a deeper comprehension of its meaning. Ensure questions are diverse and comprehensive, covering all facets of the lyrics. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! Ask one question at a time! NEVER PROMPT TEACHER TO ASK ANY QUESTION!",
}

STUDENT_INSTRUCTIONS_MQ = {
    "movie_plots": "To learn more about the movie plot known only to the teacher and get prepared for any quiz on that, ask questions on its storyline, character arcs, themes, and significant scenes. Each time pose an array of diverse questions encompassing plot progression, character actions, involvement, thematic exploration, and character motivations. Include questions seeking specific details such as character names, objects, settings, and dates. Include questions that prompt thorough analysis of the plot and a deeper comprehension of its unfolding events. Ensure questions are diverse and comprehensive, covering all facets of the movie. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! NEVER PROMPT TEACHER TO ASK ANY QUESTION! Pose multiple questions simultaneously, EACH ON A NEW LINE. Do not output anything than questions!",
    "image": "To learn more about the image known only to the teacher and get prepared for any quiz on that, ask questions on its elements, composition, and context. Each time pose an array of diverse questions encompassing symbolism, meaning, theme and actions depicted in the image. Include questions seeking specific details such as presence and placement of objects. Include questions that prompt thorough analysis of the image. Ensure questions are diverse and comprehensive, covering all facets of the image. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! NEVER PROMPT TEACHER TO ASK ANY QUESTION! Pose multiple questions simultaneously, EACH ON A NEW LINE. Do not output anything than questions!",
    "academic_papers": "To learn more about the academic paper known only to the teacher and get prepared for any quiz on that, ask questions on its objectives, methodology, findings, and significance. Each time pose an array of diverse questions encompassing experiments, its relation to prior studies, limitations, motivation and key takeaways. Include questions seeking specific details such as experimental setup. Include questions that prompt thorough analysis of the paper and a deeper understanding of its broader contributions. Ensure questions are diverse and comprehensive, covering all aspects of the paper. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! NEVER PROMPT TEACHER TO ASK ANY QUESTION! Pose multiple questions simultaneously, EACH ON A NEW LINE. Do not output anything than questions!",
    "news_articles": "To learn more about the news article known only to the teacher and get prepared for any quiz on that, ask questions on the main events, key figures, and the article's context. Each time pose an array of diverse questions encompassing background stories and broader implications. Include questions seeking specific details such as names of individuals, events, actions, and dates. Include questions that prompt thorough analysis of the article and a deeper comprehension of unfolding events. Ensure questions are diverse and comprehensive, covering all aspects of the article. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! NEVER PROMPT TEACHER TO ASK ANY QUESTION! Pose multiple questions simultaneously, EACH ON A NEW LINE. Do not output anything than questions!",
    "song_lyrics": "To learn more about song lyrics known only to the teacher knows about and get prepared for any quiz on that, ask questions on its narrative, themes, and expressive techniques used. Each time pose an array of diverse questions encompassing emotions, individuals, events, involvement, themes and references to other content. Include questions that prompt thorough analysis of the lyrics and a deeper comprehension of its meaning. Ensure questions are diverse and comprehensive, covering all facets of the lyrics. Also, feel free to ask detailed questions whenever necessary. If you run out of questions, always think of and come up with more creative and detailed questions! NEVER PROMPT TEACHER TO ASK ANY QUESTION! Pose multiple questions simultaneously, EACH ON A NEW LINE. Do not output anything than questions!",
}

QUESTION_SENTENCE = " Do you have any other questions?"

#env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_answer_from_teacher(context: str, content: str, message_history: List[Dict], seed: int = 123):
    # to obtan answer from teacher, treat teacher as assistant and student as user
    new_history = list(map(lambda x: {"role": "user" if x["role"] == "student" else "assistant", 
                                          "content": x["content"]}, message_history))
    instruction = TEACHER_INSTRUCTIONS[context].format(content=content)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "system", "content": instruction}] + new_history,
        seed=seed)
    teacher_response = response.choices[0].message.content

    return teacher_response

def get_question_from_student(context, message_history, seed: int = 123):
    # to obtan question from student, treat student as assistant and teacher as user
    new_history = list(map(lambda x: {"role": "user" if x["role"] == "teacher" else "assistant", 
                                          "content": x["content"]}, message_history))

    instruction = STUDENT_INSTRUCTIONS[context]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "system", "content": instruction}] + new_history,
        seed=seed)
    student_response = response.choices[0].message.content

    return student_response


def get_refined_question_from_student(context, message_history, lesson, seed: int = 123):
    def _get_entailment_score(model, tokenizer, sentences, question):
        #inputs = tokenizer([(s, question) for s in sentences], padding=True, truncation=True, return_tensors='pt').to('cuda:0')
        #label_mapping = ['contradiction', 'entailment', 'neutral']
        #entailment_idx = label_mapping.index('entailment')
        inputs = tokenizer([f"premise: {s} hypothesis: {question}" for s in sentences], 
                           padding=True, truncation=True, return_tensors='pt')['input_ids'].to('cuda:0')
        model.eval()
        entailment_idx = tokenizer.convert_tokens_to_ids(['1'])[0]
        
        with torch.no_grad():
            scores = nli_model.generate(inputs, max_new_tokens=10, return_dict_in_generate=True, output_scores=True).scores
            #scores = model(**inputs).logits
            total_score = torch.sum(scores[0][:, entailment_idx], dim=0).cpu().item()

        return total_score
    # to obtan question from student, treat student as assistant and teacher as user
    new_history = list(map(lambda x: {"role": "user" if x["role"] == "teacher" else "assistant", 
                                          "content": x["content"]}, message_history))

    instruction = STUDENT_INSTRUCTIONS_MQ[context]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=new_history + [{"role": "user", "content": instruction}],
        seed=seed)
    student_response = response.choices[0].message.content

    questions = nltk.sent_tokenize(student_response) # split into questions
    
    lesson_sentences = nltk.sent_tokenize(lesson)
    q_scores = [_get_entailment_score(nli_model, nli_tokenizer, lesson_sentences, q) for q in questions]
    print(questions)
    print(q_scores)
    print("------")
    
    min_idx = torch.argmin(torch.tensor(q_scores)).item()
    return questions[min_idx]

def eval_student(context, questions, message_history, true_answers, n_turn, seed: int = 123):
    answer_list = None
    num_trials = 0
    while answer_list is None:
        if num_trials > 2:
            break
        new_history = list(map(lambda x: {"role": "user" if x["role"] == "teacher" else "assistant", 
                                        "content": x["content"]}, message_history))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo" if context != "images" else "gpt-4o",
            seed=seed,
            temperature=0.0,
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
            answer_list = continuous_match.group()
        else:
            listed_matches = listed_pattern.findall(raw_answers)
            answer_list = "".join(listed_matches) if len(listed_matches) == 10 else None
        
        num_trials += 1

    if answer_list is None:
        return "NA", 0.0
    
    acc = sum(map(lambda x: x[0] == x[1], zip(answer_list, true_answers))) / len(true_answers)
    return answer_list, acc

def run_conversation(context, content, questions, true_answers, static, out_dir, n_turn: int = 10, refine_questions=False, provide_lesson=False, seed:int = 123):    
    msg_history = [{"role": "teacher", 
                    "content": f"Here is the extensive summary of the {context.replace('_', ' ')}: {static}\n" if provide_lesson else "" +
                    f"You can ask me any question about the {context.replace('_', ' ')}."}]
    
    outputs = []
    student_quiz_answers, acc = eval_student(context, questions, msg_history, true_answers, 0, seed)
    outputs.append((student_quiz_answers, acc))
    
    for i in range(1, n_turn + 1):
        #chat_summary = ' '.join([msg['content'] for msg in msg_history if msg['role'] == 'teacher'])
        q =  get_refined_question_from_student(context, msg_history, static, seed) if refine_questions else get_question_from_student(context, msg_history, seed)
        msg_history.append({"role": "student", "content": q})
        answer = get_answer_from_teacher(context, content, msg_history, seed)
        msg_history.append({"role": "teacher", "content": answer + QUESTION_SENTENCE})
        student_quiz_answers, acc = eval_student(context, questions, msg_history, true_answers, i, seed)
        outputs.append((student_quiz_answers, acc))

    return msg_history, outputs

def run(context, n_turn, refine_questions, provide_lesson, questions_folder, answers_folder, 
        context_folder, root_folder, static_folder, out_dir, seed: int = 123, results_folder: str = None):
    data = get_all_data(context, context_folder, questions_folder, answers_folder, static_folder, root_folder)
    results = []

    for title, context, content, questions, answers, static_lesson in tqdm(data):
        if results_folder:
            if os.path.exists(os.path.join(results_folder, f'chat_history_{title}.json')):
                continue
        if len(answers) == 0:
            continue
        print(title)
        msg_history, outputs = run_conversation(context, content, questions, answers, static_lesson, out_dir, 
                                                n_turn, refine_questions, provide_lesson, seed)
        for i, output in enumerate(outputs):
            student_answers, acc = output
            results.append({'title': title, 'context': context, 'true_answer': answers, 'answers': student_answers, 
                            'accuracy': acc, 'turn': i})
        with open(os.path.join(out_dir, f'chat_history_{title}.json'), 'w') as f:
            json.dump(msg_history, f, indent=4)
    
    res_file = os.path.join(out_dir, f'results.json')
    if results_folder:
        if os.path.exists(res_file):
            with open(res_file, 'r') as f:
                prev_results = json.load(res_file)
                results.extend(prev_results)
    
    with open(res_file, 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set up dynamic conversation between student and teacher')
    parser.add_argument("--context", choices=list(TEACHER_INSTRUCTIONS.keys()), required=True)
    parser.add_argument("--num-turns", type=int, default=10, required=False)
    parser.add_argument("--refine-questions", action='store_true', required=False)
    parser.add_argument("--provide-lesson", action='store_true', required=False)
    parser.add_argument("--answers-folder", required=False)
    parser.add_argument("--questions-folder", required=False)
    parser.add_argument("--context-folder", required=True)
    parser.add_argument("--static-folder", required=True)
    parser.add_argument("--root-folder", required=True)
    parser.add_argument("--output-folder", required=True)
    parser.add_argument("--results-folder", required=False)
    parser.add_argument("--seed", type=int, default=123)

    args = parser.parse_args()
    print(args.static_folder)
    if args.refine_questions:
        nli_model = AutoModelForSeq2SeqLM.from_pretrained('google/t5_xxl_true_nli_mixture', device_map='cuda', torch_dtype=torch.bfloat16)
        nli_tokenizer = AutoTokenizer.from_pretrained('google/t5_xxl_true_nli_mixture')
    run(args.context, args.num_turns, args.refine_questions, args.provide_lesson, args.questions_folder, args.answers_folder, args.context_folder, args.root_folder, args.static_folder, args.output_folder, args.seed, args.results_folder)
