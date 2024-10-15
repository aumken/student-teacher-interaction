import stanza
from nltk.translate.bleu_score import modified_precision
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import FunctionTransformer, PolynomialFeatures
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import r_regression, SelectKBest, f_regression
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.base import BaseEstimator, TransformerMixin
from transformers import set_seed
from scipy.stats import pearsonr
import numpy as np
import glob
import os
from tqdm import tqdm
import json
import random
import joblib
import argparse
from itertools import chain
import pdfplumber
from pdfminer.psparser import PSEOF
import pandas as pd
from itertools import groupby
from operator import itemgetter

class SyntaxTreeDepthExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.nlp_pipeline = stanza.Pipeline(lang='en', processors='tokenize,pos,constituency', dir='stanza-resources')

    def _get_height(self, node):
        if node.is_leaf():
            return 0
        heights = []
        for child in node.children:
            heights.append(self._get_height(child))
        return 1 + max(heights)
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        max_depths = []
        for txt in tqdm(X):
            doc = self.nlp_pipeline(txt)
            max_depth = 0
            for sentence in doc.sentences:
                tree = sentence.constituency
                max_depth = max(self._get_height(tree), max_depth)
            max_depths.append([max_depth])
        return max_depths

    def get_feature_names_out(self, input_features=None):
        return ['max_syntax_depth']

class LengthExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        # Calculate the length of each document
        lengths = X.apply(len).values.reshape(-1, 1)
        return lengths  # Return as a sparse matrix
    
    def get_feature_names_out(self, input_features=None):
        return ['length']

class NamedEntityStatsExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.ner_pipeline = stanza.Pipeline("en", processors="tokenize,ner", dir='stanza-resources')
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        entity_counts_list = []
        for txt in tqdm(X):
            entity_counts = {'PER': 0, 'LOC': 0, 'ORG': 0, 'MISC': 0}
            doc = self.ner_pipeline(txt)
            for sentence in doc.sentences:
                for entity in sentence.ents:
                    if entity.type in entity_counts:
                        entity_counts[entity.type] += 1
    
            total_count = sum(entity_counts.values())
            entity_counts_list.append([total_count])
        return entity_counts_list

    def get_feature_names_out(self, input_features=None):
        return ['named_entity_count']


class RRegressionScorer(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.scores_ = None

    def fit(self, X, y):
        #self.scores_ = r_regression(X, y)
        correlations = []
        p_values = []

        for i in range(X.shape[1]):  # Loop over each feature (column in X)
            corr, p_val = pearsonr(X[:, i], y)  # Calculate the correlation and p-value for the i-th feature
            correlations.append(corr)
            p_values.append(p_val)

        self.scores_ = correlations, p_values
        return self

    def transform(self, X):
        return X  # No transformation, just passing through the data

    def score(self, X, y):
        return self.scores_

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

def prepare_data(content_directories, chat_directories, seed: int = 42):
    dataset = []

    for content_directory, chat_directory in zip(content_directories, chat_directories):
        with open(os.path.join(chat_directory, 'results.json')) as f:
            all_results = json.load(f)
        
        all_results = [next(group) for _, group in groupby(sorted(all_results, key=itemgetter('title', 'turn')), key=itemgetter('title', 'turn'))]

        pattern = f"{chat_directory}/**/chat_*.json" 
        for file in tqdm(glob.glob(pattern, recursive=True)):
            doc_name = file.replace(f'{chat_directory}', '').replace('chat_history_', '').replace('.json', '')
            content_fname = os.path.join(content_directory, doc_name)
            #if 'academic_papers' in content_fname:
            #    content_fname = content_fname.replace('.md', '.pdf')
            #    content = extract_text_from_pdf(content_fname)
            #else:
            #    with open(content_fname, 'rb') as f:
            #        content = f.read().decode('utf-8')
            
            with open(file, 'r') as f:
                chat_history = json.load(f)
            
            questions = [msg['content'] for msg in chat_history if msg['role'] == 'student']
            #questions = [msg['content'] for msg in chat_history if msg['role'] == 'teacher'][1:]
            title = content_fname.split('/')[-1].replace('.pdf', '.md')
            
            # TO DO: fix for repeating documents
            doc_results = sorted(list(filter(lambda x: x['title'] == title, all_results)), key=lambda x: x['turn'])
            question_accuracies = list(map(lambda x: x['accuracy'], doc_results))
            info_gains = list(map(lambda x: x - question_accuracies[0], question_accuracies[1:]))
            assert len(info_gains) == len(questions), f"{info_gains} and {doc_results}"
            
            for idx, (q, info_gain) in enumerate(zip(questions, info_gains)):
                dataset.append({
                    'question': q, 'turn': idx+1, 'info_gain': info_gain
                })
    
    random.shuffle(dataset)
    df = pd.DataFrame.from_dict(dataset)

    return df

def train_regression(content_folders, chat_folders, output_file, seed: int = 42):
    dataset = prepare_data(content_folders, chat_folders)
    get_text = FunctionTransformer(lambda x: x['question'], validate=False)
    #get_turn = FunctionTransformer(lambda x: np.array(x['turn'])[..., np.newaxis], validate=False)
    get_turn = FunctionTransformer(lambda x: np.eye(np.max(x['turn']))[np.array(x['turn']) - 1], validate=False)
    X = dataset
    y = dataset['info_gain']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=seed)

    # Creating a pipeline with combined features
    pipeline = Pipeline([
        ('features', FeatureUnion([
            #('tfidf', Pipeline([
            #    ('selector', get_text),
            #    ('tfidf', TfidfVectorizer(ngram_range=(1, 5), max_features=100)),
                #('feature_reduction', SelectKBest(k=20, score_func=r_regression))
            #])),
            ('length', Pipeline([
                ('selector', get_text),
                ('length_extractor', LengthExtractor())
                ])),
            ('max_depth', Pipeline([
                ('selector', get_text),
                ('depth_extractor', SyntaxTreeDepthExtractor())
                ])),
            ('named_entity_count', Pipeline([
                ('selector', get_text),
                ('ne_extractor', NamedEntityStatsExtractor())
                ])),
            ('turn', get_turn)
        ])),
        #('polynomial', PolynomialFeatures(degree=2, include_bias=True)),
        ('scaler', MaxAbsScaler()),
        #('regressor', LinearRegression())
        ('r_regression', RRegressionScorer())
    ])

    # Training the model
    #pipeline.fit(X_train, y_train)
    #joblib.dump(pipeline, model_path)
    
    #tfidf_feature_names_all = pipeline.named_steps['features'].transformer_list[0][1].named_steps['tfidf'].get_feature_names_out()
    #selected_features_idx = pipeline.named_steps['features'].transformer_list[0][1].named_steps['feature_reduction'].get_support(indices=True)
    #print(selected_features_idx)
    #tfidf_feature_names = tfidf_feature_names_all[selected_features_idx]
    #tfidf_feature_names = tfidf_feature_names_all
    #print(tfidf_feature_names)

    feature_names = ['feat:length', 'feat:max_depth', 'feat:named_entity_count', 'feat:turn_1', 'feat:turn_2', 'feat:turn_3', 'feat:turn_4', 'feat:turn_5']
    
    #train_score = pipeline.score(X_train, y_train) 
    #test_score = pipeline.score(X_test, y_test) 
    #print(f"R2 score on train set: {train_score}")
    #print(f"R2 score on test set: {test_score}")
    #model = pipeline.named_steps['regressor']
    #coefficients = model.coef_
    #print(f"len coeff: {len(coefficients)} len feat names: {len(feature_names)} len tfidf names: {len(list(tfidf_feature_names))}")
    
    #coef_df = pd.DataFrame({'Term': feature_names, 'Coefficient': coefficients})
    #coef_df = coef_df.sort_values(by='Coefficient', ascending=False)
    #pd.set_option('display.max_rows', None)
    #print(coef_df)

    #pipeline.steps.pop()
    #pipeline.steps.append(('r_regression', RRegressionScorer()))
    pipeline.fit(X_train, y_train)
    train_correlations, train_pvalues = pipeline.score(X_train)
    corr_df = pd.DataFrame({'Term': feature_names, 'Correlation': train_correlations, 'p-value': train_pvalues})
    corr_df = corr_df.sort_values(by='Correlation', ascending=False)
    pd.set_option('display.max_rows', None)
    print(corr_df)
    corr_df.to_json(output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Regression analysis")
    parser.add_argument("--content-folders", nargs='+', required=True, help="Directory containing contents")
    parser.add_argument("--chat-folders", nargs='+', required=True, help="Directory containing chats")
    parser.add_argument("--output-file", required=True, help="Output folder name to save the model")
    parser.add_argument("--seed", required=False, type=int, default=42)

    args = parser.parse_args()
    set_seed(args.seed)
    train_regression(args.content_folders, args.chat_folders, args.output_file)
