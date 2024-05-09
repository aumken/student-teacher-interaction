import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from  matplotlib.ticker import FuncFormatter
import os
import json
import argparse
import glob
import tiktoken
import json
import PyPDF2

gpt_tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

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


def preprocess_dynamic_results(results_dir, method_name):
    all_results = []
    contexts = ['academic_papers', 'movie_plots', 'news_articles', 'song_lyrics']
    for context in contexts:
        with open(os.path.join(results_dir, context, 'results.json'), 'r') as f:
            all_results += json.load(f)
    
    all_results = list(map(lambda x: {**x, 'method': method_name}, all_results))
    return all_results

def preprocess_static_results(static_results_dir):
    def _eval_expr(expr):
        if isinstance(expr, float) and np.isnan(expr):
            return expr
        a, b = expr.strip().split('/')
        if a == '0' and b == '0':
            return np.nan
        return float(a) / float(b)
    all_static_results = []
    contexts = ['academic_papers', 'movie_plots', 'news_articles', 'song_lyrics']
    for context in contexts:
        fname = os.path.join(static_results_dir, f'{context}.xlsx')
        df = pd.read_excel(fname, index_col=0)
        scores = list(map(_eval_expr, df['S2 Score'].tolist()))
        all_static_results += [{'accuracy': s, 'method': 'static student', 'context': context, 'turn': t} for s in scores for t in range(0, 5)]

        scores = list(map(_eval_expr, df['T2 Score'].tolist()))
        all_static_results += [{'accuracy': s, 'method': 'static teacher', 'context': context, 'turn': t} for s in scores for t in range(0, 5)]
    
    return all_static_results

def preprocess_all_results(static_results_dir, plain_results_dir, lesson_results_dir, refinement_results_dir):
    dynamic_methods = ['plain', 'w/ lesson', 'w/ refinement']
    dirs = [plain_results_dir, lesson_results_dir, refinement_results_dir]
    all_results = []

    for dir_name, method in zip(dirs, dynamic_methods):
        all_results += preprocess_dynamic_results(dir_name, method)

    # ignore NA repsonse
    all_results = list(filter(lambda x: x['answers'] != 'NA', all_results))

    all_results += preprocess_static_results(static_results_dir)
    return all_results

def plot_lengths(static_lesson_dir, content_dir, plain_results_dir, lesson_results_dir, refinement_results_dir, output_dir):
    def _count_tokens(text):
        return len(gpt_tokenizer.encode(text))

    def _get_all_content(dir_name, document_type, context):
        if document_type in ['plain', 'w_lesson', 'refinement']:
            pattern = f'{dir_name}/{context}/**/chat_history_*.json'
        elif context == 'academic_papers' and document_type == 'content':
            pattern = f'{dir_name}/{context}/**/*.pdf'
        else:
            pattern = f'{dir_name}/{context}/**/*.md'

        return glob.glob(pattern, recursive=True)

    lengths = []
    contexts = ['academic_papers', 'movie_plots', 'news_articles', 'song_lyrics']
    document_types_to_dirs = {'static_lesson': static_lesson_dir, 
                              'plain': plain_results_dir,
                              'w_lesson': lesson_results_dir,
                              'refinement': refinement_results_dir,
                              'content': content_dir}
    
    for context in contexts:
        for document_type, folder in document_types_to_dirs.items():
            files = _get_all_content(folder, document_type, context)
            for file in files:
                with open(file, 'r') as f:
                    if file.endswith('.json'):
                        chat_data = json.load(f)
                        content = ' '.join(list(map(lambda x: x['content'], chat_data)))
                    elif file.endswith('.pdf'):
                        content = extract_text_from_pdf(file)
                    else:
                        content = f.read()
                content_length = _count_tokens(content)
                lengths.append({'length': content_length, 'context': context, 'document': document_type}) 

    df = pd.DataFrame(lengths)
    sns.barplot(df, x='context', y='length', hue='document')

    plt.tight_layout()
    plt.show()
    plt.savefig(os.path.join(output_dir, 'lengths.png'), dpi=300)

def plot_results(static_results_dir, plain_results_dir, lesson_results_dir, refinement_results_dir, static_lessons_dir, output_dir):
    
    results = preprocess_all_results(static_results_dir, plain_results_dir, lesson_results_dir, refinement_results_dir)
    df = pd.DataFrame(results)

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    for i, context in enumerate(df['context'].unique()):
        ax = axes[i // 2, i % 2]
        sns.lineplot(data=df[df['context'] == context], x='turn', y='accuracy', hue='method', marker='o', ax=ax, errorbar=None)
        ax.set_title(f"Context: {context}")
        plt.xticks(np.arange(0, 5, 1))

    plt.tight_layout()
    plt.show()
    plt.savefig(os.path.join(output_dir, 'results.png'), dpi=300)

def plot_information_coverage(info_results_dir, role, output_dir):
    results = []
    for file in glob.glob(f'{info_results_dir}/{role}/*.json'):
        parts = file.replace('.json','').split('/')[-1].split('_')
        context = '_'.join(parts[1:3])
        method = '_'.join(parts[3:]) if role != 'quiz' else ''

        with open(file, 'r') as f:
            res = json.load(f)
            for doc in res:
                for i, value in enumerate(res[doc]):
                    results.append({'information coverage': value, 'number of questions': i+1, 
                                    'context': context, 'method': method})

    df = pd.DataFrame(results)
    
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    for i, context in enumerate(df['context'].unique()):
        ax = axes[i // 2, i % 2]
        sns.lineplot(data=df[df['context'] == context], x='number of questions', y='information coverage', hue='method' if role != 'quiz' else None, marker='o', ax=ax, errorbar=None)
        ax.set_title(f"Context: {context}")

    plt.tight_layout()
    plt.show()
    plt.savefig(os.path.join(output_dir, f'info_results_{role}.png'), dpi=300)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot all results")
    parser.add_argument("--plot", choices=["results", "lengths", "information"], required=True)
    parser.add_argument("--static-results", help="Static results directory containing xlsx files")
    parser.add_argument("--plain-results", help="Plain results directory containing results.json file")
    parser.add_argument("--lesson-results", help="Lesson-informed results directory containing results.json file")
    parser.add_argument("--refinement-results", help="Refinement results directory containing results.json file")
    parser.add_argument("--static-lessons", help="Directory containing static lessons")
    parser.add_argument("--raw-contents", help="Directory containing raw contents")
    parser.add_argument("--information-results", help="Information coverage results directory")
    parser.add_argument("--role", help="Role for information results")
    parser.add_argument("--output", help="Output directory for the plots", required=True)

    args = parser.parse_args()
    if args.plot == 'results':
        plot_results(args.static_results, args.plain_results, args.lesson_results, args.refinement_results, args.static_lessons, args.output)
    elif args.plot == 'lengths':
        plot_lengths(args.static_lessons, args.raw_contents, args.plain_results, args.lesson_results, args.refinement_results, args.output)
    elif args.plot == 'information':
        plot_information_coverage(args.information_results, args.role, args.output)
