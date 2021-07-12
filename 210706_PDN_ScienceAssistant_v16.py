import os, pdfplumber, datetime, time, re
from pandas.core import groupby
from pdf2doi.finders import validate
from nltk.corpus import stopwords, names
from nltk.tokenize import word_tokenize
from nltk import FreqDist
import random
import pandas as pd
from pdf2doi.pdf2doi import pdf2doi

'''These are all the imports, which likely slow the entire thing down on launch.'''

now = datetime.datetime.now()
t1 = time.perf_counter()

'''dir is the default directory on my computer... I'd very much like to make this a little more anonymous.'''
dir = '/Users/johnfallot/Documents/PDN/PDN_studies'

def main(folder, file, num_of_files): #directory = dir, file = starting at, num_of_file = ending at
    """The main loop of the program. Takes the folder, file, and file number and puts out a range."""

    full_dir = [file for file in os.listdir(folder) if file.endswith('.pdf')] 
    '''Only gets the pdfs in the folder and will overlook non-pdf files.'''
    
    binder = len(full_dir) 
    '''Maximum number of pdfs in a folder.'''
    if num_of_files == 0:
        num_of_files = binder
    '''If num_of_file arg is 0, gets all the files.'''
    
    compendium = []
    '''This gets passed to the dataframe'''

    for file in range(num_of_files):
        if file <= num_of_files:
            try:
                print("Preparing file extraction...")
                filepath = str(full_dir[file])
                filename = os.path.join(folder,filepath)
                '''Generates the path to each pdf file'''
                print("\nBeginning extraction... \n")
                compendium_item = extract(filename, file, num_of_files, filepath)
                compendium.append(compendium_item)
                '''The extraction process for each file gets appended to the compendium'''
                print(f"\nPackaging {filepath}... \n")
                print("\nChecking for next file... \n")
                continue
            except:
                pass

        elif file == num_of_files:
            break
        '''This guarantees that the program will iterate for every pdf in the folder. I've been told to write this as an enumerate function, but that seems to throw up problems.'''

    printing(compendium)
    '''Once the entire folder has been extracted, the dataframing process begins.'''

def extract(filename, file, num_of_files, filepath):
    '''Using the supplied args, each file is opened using pdfplumber, which converts the pdf copy into a string.'''
    doi_results = pdf2doi(filename, verbose=True, save_identifier_metadata = True, filename_bibtex = False)

    study = pdfplumber.open(filename)
    n = len(study.pages)

    preprints = []
    '''Each page's string gets appended to this list.'''

    for page in range(n):
        if page <= n:
            findings = study.pages[page].extract_text()
            '''Each page's string gets appended to preprint []'''
            print(f"Processing file {file} of {num_of_files} | {filepath} | Page {page} of {n}...", end = "\r")
            preprints.append(findings) 
            continue
            '''Proceeds to next page in the study'''

        elif page == n:
            study.close()
            '''After each page in the study is extracted, closes the study.'''
            break
    
    for preprint in preprints:
        manuscript = str(preprint).strip()

        '''Tokenization & Keyword search. Stopwords are filtered out.'''
        postprint = redaction(manuscript)
        all_words = tokenization(postprint)
        wordscore, target_word_overlap, bycatch_word_overlap, research_word_overlap, fdist_top5 = word_match(all_words)
        fdist_top5 = frequency(all_words)

        compendium_item = {
        '''This is what gets passed back from the entire extraction process.'''

            'Title': filepath,
            'DOI': doi_results['identifier'],
            'Library': doi_results['validation_info'],
            'Pages': n,
            '5 Most Common Words': fdist_top5,
            'Research Words': research_word_overlap,
            'Target Words': target_word_overlap,
            'Bycatch Words': bycatch_word_overlap,
            'Wordscore' : wordscore

        }

        return compendium_item

def redaction(manuscript):
    '''The resulting manuscript is put into lowercase and all non-alphanumeric characters are removed.'''
    manuscript = manuscript.lower()
    postprint = re.sub(r'\W+', ' ', manuscript)
    return postprint

def tokenization(postprint):
    '''The postprint is tokenized and stopwords and names are removed.'''
    stop_words = set(stopwords.words("english"))
    name_words = set(names.words())
    word_tokens = word_tokenize(postprint)
    all_words = [w for w in word_tokens if not w in stop_words and name_words] #Filters out the stopwords
    return all_words

def word_match(all_words):
    '''The remaining tokenized words are compared against several lists of words, by way of the lambda overlap function 
    target_words are the words we're looking for in a study. 
    bycatch_words are words that generally indicate a false positive
    research_words are words that help us determine the underlying study design: was it a randomized control or analytical?

    The length of the target_words minus the length of the bycatch words determines the wordscore. A positive wordscore means a paper is more likely than not to be a match, and vice versa.

    '''
    #TO DO: have target words import from separate txt file
    target_words = ["prosocial", "design", "intervention", "reddit", "humane","social media","user experience","nudge","choice architecture","user interface", "misinformation", "disinformation", "Trump", "conspiracy", "dysinformation", "users"]
    bycatch_words = ["psychology", "pediatric", "pediatry", "autism", "mental", "medical", "oxytocin", "adolescence", "infant", "health", "wellness", "child", "care", "mindfulness"]
    research_words = ["big data", "data", "analytics", "randomized controlled trial", "RCT", "moderation", "community", "social media", "conversational", "control", "randomized", "systemic", "analysis", "thematic", "review", "study", "case series", "case report", "double blind", "ecological", "survey"]

    overlap = lambda li1: [w for w in li1 if w in all_words]
   
    target_word_overlap = overlap(target_words)
    bycatch_word_overlap = overlap(bycatch_words)
    research_word_overlap = overlap(research_words)
    
    wordscore = len(target_word_overlap) - len(bycatch_word_overlap)

    return wordscore, target_word_overlap, bycatch_word_overlap, research_word_overlap

def frequency(all_words):
    '''The five most common words in the paper are calculated.'''
    fdist = FreqDist(all_words) #Determines the frequency of the most common filtered words.
    fdist_top5 = fdist.most_common(5) #Gets the top 10 most common words
    return fdist_top5

def printing(compendium):
    '''After the paper is fully processed and exported to the compendium, the compendium is put through a pandas dataframe.
    Normally, what the compendium returns is page by page.
    What we aim to do is consolidate all entries that belong to one paper, which is what the aggregate_functions aims to do (with occasional success).'''
    print(f'\nFinalizing data for human review...\n')
    df = pd.DataFrame(compendium)
    aggregation_functions = {'DOI': 'first', 'author': 'first', 'Pages':'first', '5 Most Common Words': 'max', 'Wordscore':'sum'}
    df_new = df.groupby(df['Title']).aggregate(aggregation_functions)
    df_new = df_new.sort_values('5 Most Common Words', ascending=False)
    print(df_new.head())

    '''Finally, a YYMMDD timestamp is generated, and a pseudo_unique ID to prevent the deletion of prior work.'''
    csv_date = now.strftime('%y%m%d')
    export_ID = random.randint(0,100)
    export_name = f'{csv_date}_PDN_studies_{export_ID}.csv'
    df_new.to_csv(export_name)
    t2 = time.perf_counter()
    print(f'\nExtraction finished in {t2-t1} seconds.\nDataframe exported to {export_name}')

'''This line of code initiates the entire process.'''
main(dir, 0, 2)



#ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω
#        

#'All Citations': all_citations,