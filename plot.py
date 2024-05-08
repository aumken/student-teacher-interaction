import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from  matplotlib.ticker import FuncFormatter
import os
import json
import argparse
import glob

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
        all_static_results += [{'accuracy': s, 'method': 'static', 'context': context, 'turn': t} for s in scores for t in range(0, 5)]
    
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

def plot_static_lesson_lengths(static_lesson_dir, output_name):
    lengths = []
    contexts = ['academic_papers', 'movie_plots', 'news_articles', 'song_lyrics']
    for context in contexts:
        for fname in glob.glob(f'{static_lesson_dir}/{context}/**/*.md', recursive=True):
            with open(fname, 'r') as f:
                file_length = len(f.read())
            lengths.append({'length': file_length, 'context': context})

    df = pd.DataFrame(lengths)
    sns.barplot(df, x='context', y='length')

    plt.tight_layout()
    plt.show()
    plt.savefig(output_name, dpi=300)

def plot_results(static_results_dir, plain_results_dir, lesson_results_dir, refinement_results_dir, static_lessons_dir, output_dir):
    plot_static_lesson_lengths(static_lessons_dir, os.path.join(output_dir, 'lengths.png'))
    
    results = preprocess_all_results(static_results_dir, plain_results_dir, lesson_results_dir, refinement_results_dir)
    df = pd.DataFrame(results)

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    for i, context in enumerate(df['context'].unique()):
        ax = axes[i // 2, i % 2]
        sns.lineplot(data=df[df['context'] == context], x='turn', y='accuracy', hue='method', marker='o', ax=ax)
        ax.set_title(f"Context: {context}")
        plt.xticks(np.arange(0, 5, 1))

    plt.tight_layout()
    plt.show()
    plt.savefig(os.path.join(output_dir, 'results.png'), dpi=300)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot all results")
    parser.add_argument("--static-results", help="Static results directory containing xlsx files")
    parser.add_argument("--plain-results", help="Plain results directory containing results.json file")
    parser.add_argument("--lesson-results", help="Lesson-informed results directory containing results.json file")
    parser.add_argument("--refinement-results", help="Refinement results directory containing results.json file")
    parser.add_argument("--static-lessons", help="Directory containing static lessons")
    parser.add_argument("--output", help="Output directory for the plots")

    args = parser.parse_args()

    # Call the run() function with the provided arguments
    plot_results(args.static_results, args.plain_results, args.lesson_results, args.refinement_results, args.static_lessons, args.output)
