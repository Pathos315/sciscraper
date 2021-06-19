import os
import pdfplumber
import datetime
import time

from pathlib import Path
from nltk.corpus import stopwords, names
from nltk.tokenize import word_tokenize
from nltk import FreqDist

import pandas as pd

from pdf2doi.pdf2doi import pdf2doi

# assign directory

now = datetime.datetime.now()
t1 = time.perf_counter()

direct = '/Users/johnfallot/Documents/PDN/PDN_studies'

def main(our_files):
    our_files = Path(direct)
    for file in our_files.iterdir():
        filepath = file.name
        if file.suffix == '.pdf':
            try:
                print("Preparing file extraction...")
                print("\nBeginning extraction... \n")
                study = pdfplumber.open(filepath)
                n = len(study.pages)
                extract(n, study, filepath)
                print("\nChecking for next file... \n")
                continue
            except:
                pass


def extract(n, study, filepath):

    doi_results = pdf2doi(filepath, verbose=True, save_identifier_metadata = True, filename_bibtex = False)

    preprints = []

    for page in n:
        if page <= len(n):
            findings = study.pages[page].extract_text(x_tolerance = 3, y_tolerance = 3)
            print(f"Processing file {filepath} | Page {page} of {n}...")
            preprints.append(findings)
            continue

        elif page == n:
            study.close()
            break
    
    for preprint in preprints:
        manuscript = str(preprint).strip()
        #all_citations = get_citations(manuscript)

        #Tokenization & Keyword search
        postprint = redaction(manuscript)
        all_words = tokenization(postprint) #Filters out the stopwords
        fdist_top5 = frequency(all_words) #Sorts those words from most to least
        wordscore, target_word_overlap, bycatch_word_overlap, research_word_overlap = word_match(all_words)
        
        #The deliverable that gets sent to the database
        compendium_item = {

            'DOI': doi_results['identifier'],
            'Pages': n,
            '5 Most Common Words': fdist_top5,
            'Research Words': research_word_overlap,
            'Target Words': target_word_overlap,
            'Bycatch Words': bycatch_word_overlap,
            'Wordscore' : wordscore

        }

        compendium.append(compendium_item)
        print(f"\nPackaging {filepath}... \n")

def redaction(manuscript):
    second_draft = manuscript.translate({ord(i): None for i in '%$><]-−–[}{|/=+`‐`ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω~-#@!&*_'})
    postprint = second_draft.translate({ord(i): None for i in '1\'η2345"?678‘’”“90().;:,\n'})
    return postprint

def tokenization(postprint):
    stop_words = set(stopwords.words("english"))
    name_words = set(names.words())
    word_tokens = word_tokenize(postprint)
    all_words = [w for w in word_tokens if not w in stop_words and name_words] #Filters out the stopwords
    return all_words

def frequency(all_words):
    fdist = FreqDist(all_words) #Determines the frequency of the most common filtered words.
    fdist_top5 = fdist.most_common(5) #Gets the top 10 most common words
    return fdist_top5

def word_match(all_words):
    target_words = ["prosocial", "design", "intervention", "reddit", "humane","social media","user experience","nudge","choice architecture","user interface", "misinformation", "disinformation", "Trump", "conspiracy", "dysinformation", "users"]
    bycatch_words = ["psychology", "pediatric", "pediatry", "autism", "mental", "medical", "oxytocin", "adolescence", "infant", "health", "wellness", "child", "care", "mindfulness"]
    research_words = ["big data", "data", "analytics", "randomized controlled trial", "RCT", "moderation", "community", "social media", "conversational", "control", "randomized", "systemic", "analysis", "thematic", "review", "study", "case series", "case report", "double blind", "ecological", "survey"]
    
    overlap = lambda li1: [w for w in li1 if w in all_words]
   
    target_word_overlap = overlap(target_words)
    bycatch_word_overlap = overlap(bycatch_words)
    research_word_overlap = overlap(research_words)
    
    wordscore = len(target_word_overlap) - len(bycatch_word_overlap)

    return wordscore, target_word_overlap, bycatch_word_overlap, research_word_overlap

compendium = []
main(direct)

print(f'\nFinalizing data for human review...\n')
df = pd.DataFrame(compendium)
print(df.head())
csv_date = now.strftime('%y%m%d')
df.to_csv(f'{csv_date}_studies_test.csv')
t2 = time.perf_counter()
print(f'\nExtraction finished in {t2-t1} seconds.\nDataframe exported to {csv_date}_studies.csv')

#ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω
#        

#'All Citations': all_citations,