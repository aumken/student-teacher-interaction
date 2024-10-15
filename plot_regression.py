import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from scipy.stats import chi2, combine_pvalues


QUANTITY = 'correlation' # 'pvalue'
COEFF = 3

# Add custom font
font_path = 'Inter.ttf'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Inter'

# Configuration
concepts = ['academic_papers', 'movie_plots', 'news_articles', 'song_lyrics', 'images']
seeds = [123, 765, 915]
methods = ['plain', 'w_lesson']
colors = {'plain': '#EF6F6C', 'w_lesson': '#465775'}
hatches = {'plain': '//', 'w_lesson': 'xx'}
method_labels = {'plain': 'Student w/o Lesson', 'w_lesson': 'Student w/ Lesson'}
concept_labels = {
    'academic_papers': 'Academic Papers',
    'movie_plots': 'Movie Plots',
    'news_articles': 'News Articles',
    'song_lyrics': 'Song Lyrics',
    'images': 'Images'
}
feature_labels = {
    'feat:length': 'Length',
    'feat:max_depth': 'Depth',
    'feat:named_entity_count': 'NE Count',
    'feat:turn_1': 'P #1',
    'feat:turn_2': 'P #2',
    'feat:turn_3': 'P #3',
    'feat:turn_4': 'P #4',
    'feat:turn_5': 'P #5'
}

# Aggregate data
data = {concept: {method: {} for method in methods} for concept in concepts}

for concept in concepts:
    for method in methods:
        for seed in seeds:
            filename = f'results/regression_analysis/correlation_{concept}_{method}_{seed}.json'
            if os.path.exists(filename):
                df = pd.read_json(filename)
                for index, row in df.iterrows():
                    term = row['Term']
                    correlation = row['Correlation'] if QUANTITY == 'correlation' else row['p-value']
                    if term not in data[concept][method]:
                        data[concept][method][term] = []
                    data[concept][method][term].append(correlation)

# Calculate average correlations and standard deviations
avg_data = {concept: {method: {} for method in methods} for concept in concepts}
std_data = {concept: {method: {} for method in methods} for concept in concepts}

for concept in concepts:
    for method in methods:
        for term, correlations in data[concept][method].items():
            avg_data[concept][method][term] = np.mean(correlations) if QUANTITY == 'correlation' else combine_pvalues(correlations, method='fisher')[1]
            std_data[concept][method][term] = np.std(correlations)

# Calculate overall average and standard deviations
overall_avg_data = {method: {} for method in methods}
overall_std_data = {method: {} for method in methods}

for method in methods:
    all_correlations = {}
    for concept in concepts:
        for term, avg_corr in avg_data[concept][method].items():
            if term not in all_correlations:
                all_correlations[term] = []
            all_correlations[term].append(avg_corr)
    for term, correlations in all_correlations.items():
        overall_avg_data[method][term] = np.mean(correlations) if QUANTITY == 'correlation' else combine_pvalues(correlations, method='fisher')[1]
        overall_std_data[method][term] = np.std(correlations)

# Determine common y-axis range
all_avg_values = []
for concept in concepts:
    for method in methods:
        all_avg_values.extend(avg_data[concept][method].values())

for method in methods:
    all_avg_values.extend(overall_avg_data[method].values())

y_min = min(all_avg_values)
y_max = max(all_avg_values)

# Plotting
#fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig, axes = plt.subplots(1, 5, figsize=(30, 6))

# Plot overall average
"""ax = axes[0, 0]
terms = sorted(overall_avg_data[methods[0]].keys(), key=lambda x: feature_labels[x])
indices = range(len(terms))
width = 0.4

for j, method in enumerate(methods):
    avg_correlations = [overall_avg_data[method].get(term, 0) for term in terms]
    print(avg_correlations)
    print(terms)
    print(method)
    print(method_labels[method])
    std_correlations = [overall_std_data[method].get(term, 0) for term in terms]
    ax.bar(
        [index + j * width for index in indices],
        avg_correlations,
        yerr=std_correlations,
        width=width,
        color=colors[method],
        label=method_labels[method],
        hatch=hatches[method],
        capsize=5
    )

ax.set_title('Overall', fontsize=12*COEFF)
ax.set_xticks([index + width / 2 for index in indices])
ax.set_xticklabels([feature_labels[term] for term in terms], rotation=45, ha='right', fontsize=10*COEFF)
ax.set_ylabel('Average Correlation', fontsize=12*COEFF)
ax.grid(axis='y', linestyle='-', linewidth=0.7)
ax.tick_params(axis='both', which='major', labelsize=10*COEFF)
ax.set_ylim(y_min, y_max)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)"""

# Plot individual concepts
#plot_positions = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
plot_positions = [(0,0), (0, 1), (0, 2), (0, 3), (0, 4)]
for i, concept in enumerate(concepts):
    #ax = axes[plot_positions[i][0], plot_positions[i][1]]
    ax = axes[i]
    terms = sorted(avg_data[concept][methods[0]].keys(), key=lambda x: feature_labels[x])
    indices = range(len(terms))
    width = 0.5

    for j, method in enumerate(methods):
        avg_correlations = [avg_data[concept][method].get(term, 0) for term in terms]
        std_correlations = [std_data[concept][method].get(term, 0) for term in terms]
        ax.bar(
            [index + j * width for index in indices],
            avg_correlations,
            yerr=std_correlations,
            width=width,
            color=colors[method],
            label=method_labels[method],
            hatch=hatches[method],
            capsize=5
        )

    ax.set_title(concept_labels[concept], fontsize=12*COEFF)
    ax.set_xticks([index + width / 2 for index in indices])
    ax.set_xticklabels([feature_labels[term] for term in terms], rotation=45, ha='right', fontsize=10*COEFF)
    ax.grid(axis='y', linestyle='-', linewidth=0.7)
    ax.tick_params(axis='both', which='major', labelsize=10*COEFF)
    ax.set_ylim(y_min, y_max)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    if QUANTITY == 'pvalue':
        ax.axhline(y=0.05, linewidth=4, color='r')
    #ax.spines['left'].set_visible(False)
    #ax.spines['bottom'].set_visible(False)

# Remove y-axis labels for subplots
for pos in plot_positions[1:]:
    #axes[pos[0], pos[1]].set_ylabel('')
    axes[pos[1]].set_ylabel('')

# Add single legend to the lower center
#handles, labels = axes[0, 0].get_legend_handles_labels()
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', fontsize=7*COEFF, ncol=2)

plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust layout to make space for legend
if QUANTITY == 'correlation':
    plt.savefig('average_correlations.pdf', dpi=300, bbox_inches='tight')
else:
    plt.savefig('average_pvalue.pdf', dpi=300, bbox_inches='tight')
plt.show()
