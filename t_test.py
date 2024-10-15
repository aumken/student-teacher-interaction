import os
import json
import numpy as np
from scipy import stats
import pandas as pd


def load_accuracies(base_path, seeds, context, static_type = None, method_type_info = None):
    accuracies = {}
    for seed in seeds:
        if 'static' in base_path:
            result_file = os.path.join(base_path, f'seed_{seed}', f'{context}.xlsx')
            data = pd.read_excel(result_file)
            data = data[['Name/Title', static_type]].dropna().values.tolist()
            for title, score in data:
                title = str(title)
                score = eval(score)
                if title not in accuracies:
                    accuracies[title] = []
                accuracies[title].append(score)
        elif 'informativeness' in base_path:
            result_file = os.path.join(base_path, f'informativeness_{context}_{method_type_info}_{seed}.json')
            with open(result_file, 'r') as file:
                data = json.load(file)
            
            for title in data:
                new_title = title.replace('.md', '').replace('.pdf', '').replace('.jpg', '').strip()
                if new_title not in accuracies:
                    accuracies[new_title] = []
                accuracies[new_title].append(data[title][-1])
        else:
            # Construct the path to the results.json file
            result_file = os.path.join(base_path, f'seed_{seed}', context, 'results.json')

            with open(result_file, 'r') as file:
                data = json.load(file)

                for item in data:
                    if item['turn'] == 5:
                        title = item['title'].replace('.md', '').replace('.pdf', '').replace('.jpg', '').strip()
                        if title not in accuracies:
                            accuracies[title] = []
                        accuracies[title].append(item['accuracy'])
    print(f"accuracies: {accuracies}")
    return accuracies


def average_accuracies(accuracies):
    avg_accuracies = {}
    for title, acc_list in accuracies.items():
        avg_accuracies[title] = np.mean(acc_list)
    print(f"avg_accs: {avg_accuracies}")
    return avg_accuracies


def perform_paired_ttest(method1_avg, method2_avg):
    method1_values = []
    method2_values = []
    for title in method1_avg.keys():
        if title in method2_avg:
            method1_values.append(method1_avg[title])
            method2_values.append(method2_avg[title])

    t_statistic, p_value = stats.ttest_rel(method1_values, method2_values)

    return t_statistic, p_value


def main(context):
    #context = "academic_papers"  # Replace with your specific context
    seeds = [123, 765, 915]  # Replace with your actual seed values

    # Paths to the directories for the two methods
    path_dynamic_plain = "results/results_dynamic_plain"
    path_dynamic_w_lesson = "results/results_dynamic_w_lesson"
    path_static_student_wo_lesson = "results/static_results"
    path_static_student_w_lesson = "results/static_results"
    path_static_teacher_wo_lesson = "results/static_results"
    path_student_info_wo_lesson = "results/informativeness_results/student"
    path_student_info_w_lesson = "results/informativeness_results/student"
    path_teacher_info_wo_lesson = "results/informativeness_results/teacher"
    path_teacher_info_w_lesson = "results/informativeness_results/teacher"

    # Load accuracies for each method
    dynamic_plain_accuracies = load_accuracies(path_dynamic_plain, seeds, context)
    dynamic_w_lesson_accuracies = load_accuracies(path_dynamic_w_lesson, seeds, context)
    static_student_wo_lesson_accuracies = load_accuracies(path_static_student_wo_lesson, seeds, context, static_type='S1 Score')
    static_student_w_lesson_accuracies = load_accuracies(path_static_student_w_lesson, seeds, context, static_type='S2 Score')
    static_teacher_wo_lesson_accuracies = load_accuracies(path_static_teacher_wo_lesson, seeds, context, static_type='T1 Score')
    student_info_wo_lesson = load_accuracies(path_student_info_wo_lesson, seeds, context, method_type_info='plain')
    student_info_w_lesson = load_accuracies(path_student_info_w_lesson, seeds, context, method_type_info='w_lesson')
    teacher_info_wo_lesson = load_accuracies(path_teacher_info_wo_lesson, seeds, context, method_type_info='plain')
    teacher_info_w_lesson = load_accuracies(path_teacher_info_w_lesson, seeds, context, method_type_info='w_lesson')

    # Average accuracies across seeds for each method
    dynamic_plain_avg = average_accuracies(dynamic_plain_accuracies)
    dynamic_w_lesson_avg = average_accuracies(dynamic_w_lesson_accuracies)
    static_student_wo_lesson_avg = average_accuracies(static_student_wo_lesson_accuracies)
    static_student_w_lesson_avg = average_accuracies(static_student_w_lesson_accuracies)
    static_teacher_wo_lesson_avg = average_accuracies(static_teacher_wo_lesson_accuracies)
    student_info_wo_lesson_avg = average_accuracies(student_info_wo_lesson)
    student_info_w_lesson_avg = average_accuracies(student_info_w_lesson)
    teacher_info_wo_lesson_avg = average_accuracies(teacher_info_wo_lesson)
    teacher_info_w_lesson_avg = average_accuracies(teacher_info_w_lesson)

    #print(f"static teacher avg: {static_teacher_wo_lesson_avg.keys()}")
    #print(f"dynamic w lesson avg: {dynamic_w_lesson_avg.keys()}")
    #print("----")

    pairs = [(dynamic_w_lesson_avg, dynamic_plain_avg), (static_student_w_lesson_avg, static_student_wo_lesson_avg), 
             (static_teacher_wo_lesson_avg, dynamic_w_lesson_avg), (static_teacher_wo_lesson_avg, static_student_w_lesson_avg),
             (student_info_w_lesson_avg, student_info_wo_lesson_avg), (teacher_info_w_lesson_avg, teacher_info_wo_lesson_avg)]
    pair_names = [['dynamic w lesson', 'dynamic wo lesson'], ['static student w lesson', 'static wo lesson'], 
                    ['static teacher', 'dynamic w lesson'], ['static teacher', 'static student w lesson'],
                    ['informativeness student w lesson', 'informativeness student wo lesson'], ['informativeness teacher w lesson', 'informativeness teacher wo lesson']]
    # Perform paired t-test
    exit()
    print(context.upper())
    print("significance level: 0.05")
    for idx, (m1, m2) in enumerate(pairs):
        t_statistic, p_value = perform_paired_ttest(m1, m2)

        # Output the results
        print(f"T-statistic: {t_statistic}")
        print(f"P-value: {p_value}")
        if p_value < 0.05:
            if t_statistic > 0:
                print(f"{pair_names[idx][0]} is significantly better than {pair_names[idx][1]} ")
            else:
                print(f"{pair_names[idx][1]} is significantly better than {pair_names[idx][0]}")
        else:
            print("No significant difference between the two methods")
        print()
    print("---------------------")
    print()

if __name__ == "__main__":
    for context in ['academic_papers', 'movie_plots', 'song_lyrics', 'news_articles']:
        main(context)
