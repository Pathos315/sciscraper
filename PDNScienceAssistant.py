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

'''the sample directory.'''
dir = 'PDF-Bulk-Assessment/Directory_Sample/'

def main(folder, file, num_of_files): #directory = dir, file = starting at, num_of_file = ending at
    """The main loop of the program. Takes the folder, file, and file number and puts out a range."""

    full_dir = [file for file in os.listdir(folder) if file.endswith('.pdf')] 
    '''Only gets the pdfs in the folder and will overlook non-pdf files.'''
    
    '''Maximum number of pdfs in a folder.'''
    if num_of_files == 0 or num_of_files > len(full_dir): 
        num_of_files = len(full_dir)
    '''If num_of_file arg is 0, or if it is larger than the number of files in the target folder, we set it to the number of files in the folder.'''
    
    files_to_check = full_dir[:num_of_files] #select the first num_of_files elements from the list
    '''This gets passed to the dataframe'''
    
    compendium = []
    
    for file_index,file in enumerate(files_to_check): #note: now the variable file is an element of files_to_check, not a numerical index
        try:
            print("\nPreparing file extraction...\n")
            filepath = str(file)
            filename = os.path.join(folder,filepath)
            '''Generates the path to each pdf file'''
            print("\nBeginning extraction... \n")
            print(f"\nProcessing file {file_index} of {num_of_files} | {filepath}\n", end = "\r")
            extract(filename, filepath)
            '''The extraction process for each file gets appended to the compendium'''
            print(f"\nPackaging {filepath}... \n")
            print("\nChecking for next file... \n")
            continue
        except:
            pass

    '''Once the entire folder has been extracted, the dataframing process begins.'''
    finalize(compendium)

def extract(filename, filepath):
    '''Using the supplied args, each file is opened using pdfplumber, which converts the pdf copy into a string.'''
    doi_results = pdf2doi(filename, verbose=True, save_identifier_metadata = True, filename_bibtex = False)

    preprints = []

    with pdfplumber.open(filename) as study:
        n = len(study.pages)

        '''Each page's string gets appended to this list.'''
        for page in range(n):
            if page <= n:
                findings = study.pages[page].extract_text(x_tolerance=3, y_tolerance=3)
                '''Each page's string gets appended to preprint []'''
                print(f" Processing Page {page} of {n}...", end = "\r")
                preprints.append(findings)
                continue

            elif page == n:
                '''After all page in the study is extracted, closes the study.'''
                break
    
    for preprint in preprints:
        manuscript = str(preprint).strip()
        '''
        Tokenization & Keyword search. Stopwords are filtered out.
        '''
        postprint = redaction(manuscript)
        all_words = tokenization(postprint)
        wordscore = word_match(all_words)

        '''
        Below is what gets passed back from the entire extraction process.
        '''
        compendium_item = {

            'Title': filepath,
            'DOI': doi_results['identifier'],
            'Pages': n,
            'Wordscore' : wordscore

            }
        
        compendium.append(compendium_item)

def redaction(manuscript):
    '''
    The resulting manuscript is put into lowercase and all non-alphanumeric characters are removed.
    '''
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

    '''
    The remaining tokenized words are compared against several lists of words, by way of the lambda overlap function.
    target_words are the words we're looking for in a study. 
    bycatch_words are words that generally indicate a false positive
    research_words are words that help us determine the underlying study design: was it a randomized control or analytical?

    The length of the target_words minus the length of the bycatch words determines the wordscore. A positive wordscore means a paper is more likely than not to be a match, and vice versa.
    '''

    #TO DO: have target words import from separate txt file
    target_words = ["prosocial", "design", "intervention", "reddit", "humane","social media","user experience","nudge","choice architecture","user interface", "misinformation", "disinformation", "Trump", "conspiracy", "dysinformation", "users"]
    bycatch_words = ["psychology", "pediatric", "pediatry", "autism", "mental", "medical", "oxytocin", "adolescence", "infant", "health", "wellness", "child", "care", "mindfulness"]

    overlap = lambda li: [w for w in li if w in all_words]
   
    target_word_overlap = overlap(target_words)
    bycatch_word_overlap = overlap(bycatch_words)
    
    wordscore = len(target_word_overlap) - len(bycatch_word_overlap)

    return wordscore

def finalize(compendium):
    '''A dataframe is generated using pandas, but TBH this #@!?>_< code has only generated headaches so far.'''
    print(f'\nFinalizing data for human review...\n')
    df = pd.DataFrame(compendium)
    aggregation_functions = {'DOI': 'first', 'Pages': 'first', 'Wordscore':'sum'}
    df = df.groupby(df['Title']).aggregate(aggregation_functions)
    print(df.head())
    finish(df)

def csv_filename():
    '''A YYMMDD timestamp is generated, and a pseudo_unique ID to prevent the deletion of prior work.'''
    csv_date = now.strftime('%y%m%d')
    export_ID = random.randint(0,100)
    export_name = f'{csv_date}_PDN_studies_{export_ID}.csv'
    return export_name

def finish(df):
    '''The dataframe is handed off to a csv file and exported. A time is measured for benchmarking.'''
    export_name = csv_filename()
    df.to_csv(export_name)
    t2 = time.perf_counter()
    print(f'\nExtraction finished in {t2-t1} seconds.\nDataframe exported to {export_name}')
        
'''This line of code initiates the entire process.'''
main(dir, 0, 2)
