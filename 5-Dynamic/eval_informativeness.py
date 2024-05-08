import glob
from tqdm import tqdm
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
import torch
import nltk
import argparse
import os

def _get_entailment_scores(model, tokenizer, sentences, question):
    inputs = tokenizer([f"premise: {s} hypothesis: {question}" for s in sentences], 
                        padding=True, truncation=True, return_tensors='pt')['input_ids'].to('cuda:0')
    model.eval()
    entailment_idx = tokenizer.convert_tokens_to_ids(['1'])[0]
    non_entailment_idx = tokenizer.convert_tokens_to_ids(['0'])[0]
    indices = [entailment_idx, non_entailment_idx]
    
    with torch.no_grad():
        scores = nli_model.generate(inputs, max_new_tokens=10, return_dict_in_generate=True, output_scores=True).scores[0]
        scores = torch.nn.functional.softmax(scores[:, indices], dim=0).cpu()

    return scores

def get_informativeness_per_doc(model, tokenizer, content, questions):
    doc_sentences =  nltk.sent_tokenize(content)
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
        scores = torch.max(torch.vstack(sent_scores), dim=0).values
        all_scores.append(scores)
        max_of_qs = torch.max(torch.vstack(all_scores), dim=0).values
        informativeness_per_doc.append(max_of_qs.mean().item())

    return informativeness_per_doc

def get_informativeness(out_file, chat_directory, content_directory, role, model, tokenizer):
    scores = {}
    for file in tqdm(glob.glob(f"{chat_directory}/**/chat_*.json", recursive=True)):
        doc_name = file.replace(f'{chat_directory}', '').replace('chat_history_', '').replace('.json', '')
        with open(os.path.join(content_directory, doc_name), 'rb') as f:
            content = f.read().decode('utf-8')
            print(content)
        with open(file, 'r') as f:
            chat_history = json.load(f)

        questions = [msg['content'] for msg in chat_history if msg['role'] == role]
        informativeness_per_doc = get_informativeness_per_doc(model, tokenizer, content, questions)
        scores[doc_name] = informativeness_per_doc

    with open(out_file, 'w') as f:
        json.dump(scores, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate informativeness")
    parser.add_argument("--role", choices=['teacher', 'student'], required=True, help="Role to evaluate")
    parser.add_argument("--content-folder", required=True, help="Directory containing contents")
    parser.add_argument("--chat-folder", required=True, help="Directory containing chats")
    parser.add_argument("--output-file", required=True, help="Output file name")

    args = parser.parse_args()
    nli_model = AutoModelForSeq2SeqLM.from_pretrained('google/t5_xxl_true_nli_mixture', device_map='cuda', torch_dtype=torch.bfloat16)
    nli_tokenizer = AutoTokenizer.from_pretrained('google/t5_xxl_true_nli_mixture')

    get_informativeness(args.output_file, args.chat_folder, args.content_folder, args.role, nli_model, nli_tokenizer)