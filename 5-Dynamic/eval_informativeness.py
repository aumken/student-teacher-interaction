import glob
from tqdm import tqdm
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
import torch
import nltk
import argparse
import os
import pdfplumber
from pdfminer.psparser import PSEOF
import re

nltk.data.path.append('.')

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
                if len(text) >= 1500:
                    break
    except PSEOF:  # Catch the PSEOF exception
        pass  # Continue to the next line
    return text[:1500]

def _get_entailment_scores(model, tokenizer, sentences, question, batch_size=16):
    inputs = tokenizer([f"premise: {s} hypothesis: {question}" for s in sentences], 
                        padding=True, truncation=True, return_tensors='pt')['input_ids'].to('cuda:0')
    model.eval()
    entailment_idx = tokenizer.convert_tokens_to_ids(['1'])[0]
    non_entailment_idx = tokenizer.convert_tokens_to_ids(['0'])[0]
    indices = [entailment_idx, non_entailment_idx]
    
    scores = []
    with torch.no_grad():
        for i in range(0, inputs.shape[0], 16):
            batch = inputs[i:i+16, :]
            batch_scores = nli_model.generate(batch, max_new_tokens=10, return_dict_in_generate=True, output_scores=True).scores[0]
            batch_scores = torch.nn.functional.softmax(batch_scores[:, indices], dim=0).cpu()
            scores.append(batch_scores)
    
    scores = torch.vstack(scores)
    diff = (scores[:, 0] - scores[:, 1]).unsqueeze(-1)
    
    return diff

def get_informativeness_per_doc(model, tokenizer, content, questions, split_by_newlines=False):
    doc_sentences =  content.split('\n') if split_by_newlines else nltk.sent_tokenize(content)
    all_scores = []
    informativeness_per_doc = []
    # aggregated informativenss: max_i(q_i, doc)
    for q in questions:
        sents = nltk.sent_tokenize(q)
        sent_scores = []
        # q_i vs doc: max_j entailment(q_ij, doc_sents)
        for sent in sents:
            scores = _get_entailment_scores(model, tokenizer, doc_sentences, sent)
            sent_scores.append(scores)
        scores = torch.max(torch.vstack(sent_scores), dim=-1).values
        all_scores.append(scores)
        max_of_qs = torch.max(torch.vstack(all_scores), dim=0).values
        informativeness_per_doc.append(max_of_qs.mean().item())
    #informativeness_per_doc = all_scores #torch.vstack(all_scores)
    return informativeness_per_doc

def get_informativeness(out_file, chat_directory, content_directory, questions_folder, role, model, tokenizer):
    scores = {}
    pattern = f"{questions_folder}/**/question_*.md" if role == 'quiz' else f"{chat_directory}/**/chat_*.json" 
    
    for file in tqdm(glob.glob(pattern, recursive=True)):
        if role == 'quiz':
            doc_name = file.replace(f'{questions_folder}', '').replace('question_', '')
        else:
            doc_name = file.replace(f'{chat_directory}', '').replace('chat_history_', '').replace('.json', '')
        
        content_fname = os.path.join(content_directory, doc_name)
        if 'academic_papers' in content_fname:
            content_fname = content_fname.replace('.md', '.pdf')
            content = extract_text_from_pdf(content_fname)
        else:
            with open(content_fname, 'rb') as f:
                content = f.read().decode('utf-8')
        
        if role == 'quiz':
            with open(file, 'r') as f:
                txt = f.read()
            questions = re.findall(r"Question [0-9]+: (.+)", txt, re.MULTILINE)
        else:
            with open(file, 'r') as f:
                chat_history = json.load(f)
            questions = [msg['content'] for msg in chat_history if msg['role'] == role]

        split_by_lines = True if 'song_lyrics' in content_fname else False
        informativeness_per_doc = get_informativeness_per_doc(model, tokenizer, content, questions, split_by_lines)
        scores[doc_name] = informativeness_per_doc

    with open(out_file, 'w') as f:
        json.dump(scores, f, indent=4)
    #torch.save(scores, out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate informativeness")
    parser.add_argument("--role", choices=['teacher', 'student', 'quiz'], required=True, help="Role to evaluate")
    parser.add_argument("--content-folder", required=True, help="Directory containing contents")
    parser.add_argument("--questions-folder", required=False, help="Directory containing contents")
    parser.add_argument("--chat-folder", required=False, help="Directory containing chats")
    parser.add_argument("--output-file", required=True, help="Output file name")

    args = parser.parse_args()
    nli_model = AutoModelForSeq2SeqLM.from_pretrained('google/t5_xxl_true_nli_mixture', device_map='cuda', torch_dtype=torch.bfloat16)
    nli_tokenizer = AutoTokenizer.from_pretrained('google/t5_xxl_true_nli_mixture')

    get_informativeness(args.output_file, args.chat_folder, args.content_folder, args.questions_folder, args.role, nli_model, nli_tokenizer)