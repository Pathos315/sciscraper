import os, pdfplumber, datetime, time
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import FreqDist
import pandas as pd


# assign directory

now = datetime.datetime.now()
t1 = time.perf_counter()

dir = '/Users/johnfallot/Desktop/PDN_studies'

def main(folder, file, num_of_files): #directory = dir, file = starting at, num_of_file = ending at

    full_dir = [file for file in os.listdir(folder) if file.endswith('.pdf')]
    binder = len(full_dir)
    if num_of_files == 0:
        num_of_files = binder
    
    for file in range(num_of_files):
        if file <= num_of_files:
            print("Preparing file extraction...")
            filepath = str(full_dir[file])
            filename = os.path.join(folder,filepath)
            study = pdfplumber.open(filename)
            n = len(study.pages)
            print("\nBeginning extraction... \n")
            extract(n, study, file, num_of_files, filepath)
            print("\nChecking for next file... \n")
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
        manuscript = str(preprint).strip()
        #all_citations = get_citations(manuscript)

        #Tokenization & Keyword search
        postprint = redaction(manuscript)
        all_words = tokenization(postprint) #Filters out the stopwords
        fdist_top5 = frequency(all_words) #Sorts those words from most to least
        target_word_overlap, bycatch_word_overlap, research_word_overlap = word_match(all_words)
        
        #The deliverable that gets sent to the database
        compendium_item = {

            'Title': filepath,
            'Pages': n,
            '5 Most Common Words': fdist_top5,
            'Research Words': research_word_overlap,
            'Target Words': target_word_overlap,
            'Bycatch Words': bycatch_word_overlap

        }

        compendium.append(compendium_item)
    print(f"\nPackaging {filepath}... \n")

"""
TODO: Currently catches too many stray characters
def get_citations(manuscript):
    citations = manuscript[manuscript.find("(")+1:manuscript.find(")")]
    all_citations = []
    all_citations.append(citations)
    return all_citations
"""

def redaction(manuscript):
    second_draft = manuscript.translate({ord(i): None for i in '%$><]-–[}{|/=+`‐`ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω~-#@!&*_'})
    postprint = second_draft.translate({ord(i): None for i in '1\'η2345"?678‘’”“90().;:,\n'})
    return postprint

def frequency(all_words):
    fdist = FreqDist(all_words) #Determines the frequency of the most common filtered words.
    fdist_top5 = fdist.most_common(5) #Gets the top 10 most common words
    return fdist_top5

def tokenization(postprint):
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(postprint)
    all_words = [w for w in word_tokens if not w in stop_words] #Filters out the stopwords
    return all_words

def overlap(li1,li2):
    li3 = [w for w in li1 if w in li2]
    return li3

def word_match(postprint):
    target_words = ["prosocial","design","intervention","humane","social media","user experience","nudge","choice architecture","user interface", "misinformation", "disinformation", "Trump", "conspiracy", "dysinformation", "users"]
    bycatch_words = ["psychology", "pediatric", "pediatry", "autism", "mental", "medical", "oxytocin", "health", "wellness", "child", "care", "mindfulness"]
    research_words = ["big data", "data", "analytics", "randomized controlled trial", "RCT", "moderation", "community", "social media", "conversational", "control", "randomized", "systemic", "analysis", "thematic", "review", "study", "case series", "case report", "double blind", "ecological", "survey"]
    target_word_overlap = overlap(target_words, postprint)
    bycatch_word_overlap = overlap(bycatch_words, postprint)
    research_word_overlap = overlap(research_words, postprint)

    return target_word_overlap, bycatch_word_overlap, research_word_overlap

compendium = []
main(dir, 0, 0)

print(f'\nFinalizing data for human review...\n')
df = pd.DataFrame(compendium)
df.sort_values('5 Most Common Words', ascending=False)
print(df.head())
csv_date = now.strftime('%Y_%m_%d')
df.to_csv(f'{csv_date}_studies_1.csv')
t2 = time.perf_counter()
print(f'\nExtraction finished in {t2-t1} seconds.\n ')
