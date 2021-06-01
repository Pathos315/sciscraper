import os, pdfplumber
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import FreqDist
import pandas as pd

# assign directory

compendium = []
dir = '/Users/johnfallot/Desktop/PDN_studies'

def direct(folder, file, num_of_files): #directory = dir, file = starting at, num_of_file = ending at

    full_dir = [file for file in os.listdir(folder) if file.endswith('.pdf')]
    #binder = len(full_dir)
    
    for file in range(num_of_files):
        if file <= num_of_files:
            print("Preparing file extraction...")
            filepath = str(full_dir[file])
            filename = os.path.join(folder,filepath)
            study = pdfplumber.open(filename)
            n = len(study.pages)
            print("Beginning extraction...")
            extract(n, study, file, num_of_files, filepath)
            print("Checking for next file...")
            continue

        elif file == num_of_files:
            break

def extract(n, study, file, num_of_files, filepath):
    
    preprints = []

    for page in range(n):
        if page <= n:
            findings = study.pages[page].extract_text()
            print(f"Processing file {file} of {num_of_files} | {filepath} | Page {page} of {n}...")
            preprints.append(findings) 
            continue

        elif page == n:
            study.close()
            break
    
    for preprint in preprints:
        print(f"Packaging {filepath}...")
        manuscript = str(preprint)
        citations = manuscript[manuscript.find("(")+1:manuscript.find(")")]
        all_citations = []
        all_citations.append(citations)

        #Tokenization & Keyword search
        second_draft = manuscript.translate({ord(i): None for i in '%$><][}{|/``~-#@!&*_'})
        third_draft = second_draft.translate({ord(i): None for i in '1\'2345"67890().;:,\n'})
        stop_words = set(stopwords.words("english"))
        word_tokens = word_tokenize(third_draft)

        all_words = [w for w in word_tokens if not w in stop_words] #Filters out the stopwords

        fdist = FreqDist(all_words) #Determines the frequency of the most common filtered words.
        fdist_top15 = fdist.most_common(15) #Gets the top 10 most common words
        results = sorted(fdist_top15, reverse=1) #Sorts those words from most to least
        
        #The deliverable that gets sent to the database
        compendium_item = {

            'Title': filepath,
            'Contents': second_draft,
            'Current Page': page,
            'Total Pages': n,
            '15 Most Common Words': results,
            'All Citations': all_citations,

        }

        compendium.append(compendium_item)

compendium = []
direct(dir,0,2)

print(f'Finalizing the compendium for human review...')
df = pd.DataFrame(compendium)
print(df.head())
df.to_csv('210601_studies_12.csv')
print('Extraction finished.')
