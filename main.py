import os, pdfplumber, datetime, time, re, random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, names
import pandas as pd
from pdf2doi.pdf2doi import pdf2doi
from nltk import FreqDist
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import as_text

now = datetime.datetime.now()
t1 = time.perf_counter()

#the sample directory
default_directory = 'pdfcurate/Directory_Sample/'

def run(folder: str, file: int, num_of_files: int): #directory = dir, file = starting at, num_of_file = ending at
    '''
    Parameters:
        folder (str): The pathname to the folder that contains the files to be extracted.
        file (int): The index of the file within the folder.
        num_of_files (int): The total number of files to be extracted.

    Variables:
        full_dir (list): Short for 'full directory', it is a list comprehension of each pdf file in the folder directory.
        files_to_check: the full_dir (list), compared against the num_of_files parameter. This gets enumerated.

    Returns:
        list: a list (compendium) of dictionaries (cpdx) for the finalize method
    '''

    full_dir = [file for file in os.listdir(folder) if file.endswith('.pdf')]
        
    if num_of_files == 0 or num_of_files > len(full_dir): 
        num_of_files = len(full_dir) #if the num_of_files is less than 0 or greater than the number of files in the folder, then it will get every pdf file in the folder
        
    files_to_check = full_dir[:num_of_files] #select the first num_of_files elements from the list

    for file_index,file in enumerate(files_to_check): #note: now the variable file is an element of files_to_check, not a numerical index
        try:
            print("\nPreparing file extraction...\n")
            filepath, filename = filenaming(folder, file)
            #Generates the path to each pdf file
            print("\nBeginning extraction... \n")
            print(f"\nProcessing file {file_index} of {num_of_files} | {filepath}\n", end = "\r")
            extract(filename)
            #The extraction process for each file gets appended to the compendium
            print(f"\nPackaging {filepath}... \n")
            continue
        except:
            pass
       
def filenaming(folder: str, file: int):
    '''
    Parameters:
        folder (str): The pathname to the folder that contains the files to be extracted.
        file (int): The index of the file within the folder.

    Returns:
        filepath: the name assigned to the file being extracted.
        filename: the full pathname to the file being extracted.

    '''
    filepath = str(file)
    filename = os.path.join(folder,filepath)
    return filepath,filename
    
def extract(filename, filepath):
    '''
    Parameters:
        filename: the full pathname to the file being extracted.

    Variables:
        doi_results: Using the filename, the pdf2doi module returns a bibtex entry for the file.
        study: The file opened to be read using pdfplumber, a robust pdf file reader.
        n (int): the total numerical length of all the pages in the study.
        book(list): a list comprehension of each page to be examined in the opened file
        pages_to_check: the book (list), compared against the book's total length
        findings: the raw extraction from each study's pages
        preprints (list): a list of all the findings appended together
        manuscript (str): for each preprint in the preprints list, it is made into a lowercase string, and stripped of extraneous characters

    Returns: 
        cpdi (dict): A dictionary of key information about the paper in question.
    '''
    doi_results = pdf2doi(filename, verbose=True, save_identifier_metadata = True, filename_bibtex = False)

    preprints = []

    with pdfplumber.open(filename) as study:
        n = len(study.pages)
        book = [page for page in study.pages]
        pages_to_check = book[:n]
        for page_number, page in enumerate(pages_to_check):
            findings = study.pages[page_number].extract_text(x_tolerance=3, y_tolerance=3)
            #Each page's string gets appended to preprint []
            print(f" Processing Page {page_number} of {n}...", end = "\r")
            preprints.append(findings)
            continue
    
    for preprint in preprints:
        manuscript = str(preprint).strip().lower()
        postprint = redaction(manuscript)
        all_words = tokenization(postprint)
        wordscore, research_word_overlap = word_match(all_words)
        doi_url, publisher, journal, volume, number, title, author, year = bibtex_writing(doi_results)
        fdist_top5 = frequency(all_words)
        sdist_top3 = study_design(research_word_overlap)

        # Below is what gets passed back from the entire extraction process.
        
        cpdi = {

            'Title': title,
            'Author(s)': author,
            'Year': year,
            'DOI': doi_results['identifier'],
            'DOI URL': doi_url,
            'Publisher': publisher,
            'Journal': journal,
            'Volume': volume,
            'No.': number,
            'Pages': n,
            'Wordscore': wordscore,
            '5 Most Common Words': fdist_top5,
            'Study Design': sdist_top3
            
        }
        compendium.append(cpdi)
    return

def bibtex_writing(doi_results, keys=('url', 'publisher', 'journal', 'volume', 'number', 'title', 'author', 'year')):
    ''' 
    Parameters: 
        doi_results (bibtex): pdf2doi validation info
        keys: the keys in the bibtex entry to be extracted

    Returns: 
        bibtex data extracted from pdf2doi validation info.
    '''
    bibtex = doi_results['validation_info']
    parser = BibTexParser(interpolate_strings=False)
    database = parser.parse(bibtex)
    return (as_text(database.entries[0][key]) for key in keys)

def redaction(manuscript):
    '''
    Parameters:
        manuscript (str): A lowercase string from the initial extraction process, stripped of extraneous characters
        
    Returns:
        postprint (str): All non-alphanumeric characters are removed from the manuscript.
    '''
    postprint = re.sub(r'\W+', ' ', manuscript)
    return postprint

def tokenization(postprint):
    '''
    Parameters:
        postprint (str): A lowercase string now removed of its non-alphanumeric characters.
        
    Returns:
        all words (list comprehension): A parsed and tokenized instance of the postprint string.
    '''
    stop_words = set(stopwords.words("english"))
    name_words = set(names.words())
    word_tokens = word_tokenize(postprint)
    all_words = [w for w in word_tokens if not w in stop_words and name_words] #Filters out the stopwords
    return all_words

def word_match(all_words):
    '''
    Parameters:
        all words (list comprehension): A parsed and tokenized instance of the postprint string.
    
    Description:
        The remaining tokenized words are compared against several lists of words, by way of the lambda overlap function.

        target_words are the words we're looking for in a study. 
        bycatch_words are words that generally indicate a false positive
        research_words are words that help us determine the underlying study design: was it a randomized control or analytical?
    
        A positive wordscore means a paper is more likely than not to be a match, and vice versa.
        
    Returns:
        wordscore (int): A value derived from the length of matching target_words minus the length of matching bycatch words.
        research_words (list): A list of matching research words in the paper.
    '''

    target_words = ["prosocial", "design", "intervention", "reddit", "humane","social media",\
                    "user experience","nudge","choice architecture","user interface", "misinformation", \
                    "disinformation", "Trump", "conspiracy", "dysinformation", "users"]
    bycatch_words = ["psychology", "pediatric", "pediatry", "autism", "mental", "medical", \
                    "oxytocin", "adolescence", "infant", "health", "wellness", "child", "care", "mindfulness"]
    research_words = ["big data", "data", "analytics", "randomized controlled trial", "RCT", "moderation", \
                    "community", "social media", "conversational", "control", "randomized", "systemic", \
                    "analysis", "thematic", "review", "study", "case series", "case report", "double blind", \
                    "ecological", "survey"]
    
    overlap = lambda li: [w for w in li if w in all_words]
    
    target_word_overlap = overlap(target_words)
    bycatch_word_overlap = overlap(bycatch_words)
    research_word_overlap = overlap(research_words)

    wordscore = len(target_word_overlap) - len(bycatch_word_overlap)
    return wordscore, research_word_overlap

def study_design(research_word_overlap):
    '''
    Parameters:
        research_words (list): A list of matching research words in the paper.
        
    Returns:
        sdist_top3 (list): A list of the top three most common research words in the paper.
    '''
    sdist = FreqDist(research_word_overlap)
    sdist_top3 = sdist.most_common(3)
    return sdist_top3

def frequency(all_words):
    '''
    Parameters:
        all words (list comprehension): A parsed and tokenized instance of the postprint string.
        
    Returns:
        fdist_top5 (list): A list of the five most common words in the paper.
    '''
    fdist = FreqDist(all_words) #Determines the frequency of the most common filtered words.
    fdist_top5 = fdist.most_common(5) #Gets the top 10 most common words
    return fdist_top5

def finalize(compendium):
    '''
    Parameters:
        compendium(list): A list of all dictionaries from the extract method
        
    Returns:
        A csv file, creating using the pandas module, which contains all information about the papers in question.
    '''
    
    print(f'\nFinalizing data for human review...\n')

    df = pd.DataFrame(compendium)

    aggregation_functions = {
            'author': 'first',
            'year': 'first',
            'doi': 'first',
            'doi_url': 'first',
            'publisher': 'first',
            'journal': 'first',
            'volume': 'first',
            'number': 'first',
            'pages': 'first',
            '5 Most Common Words': 'max',
            'Study Design': 'max',
            'Wordscore': 'sum'
        }

    df_new = df\
        .groupby(df['title'])\
        .agg(aggregation_functions)
    print(df_new.head())
    finish(df_new)

def csv_filename():
    '''
    Parameters:
        None

    Description:
        A YYMMDD timestamp is generated, and a pseudo_unique ID to prevent the deletion of prior work.

    Returns:
        export_name (str): A name for the imminent file to be.
    '''
    csv_date = now.strftime('%y%m%d')
    export_ID = random.randint(0,100)
    export_name = f'{csv_date}_PDN_studies_{export_ID}.csv'
    return export_name

def finish(df):
    '''
    Parameters:
        df (dataframe): the pandas dataframe

    Description:
        The dataframe is handed off to a csv file and exported. A time is measured for benchmarking.

    Returns:
        pErFeCtIoN
    '''
    export_name = csv_filename()
    df.to_csv(export_name)
    t2 = time.perf_counter()
    print(f'\nExtraction finished in {t2-t1} seconds.\nDataframe exported to {export_name}')
        
#========================
#    MAIN LOOP TIME
#========================

compendium = []

if __name__ == '__main__':
    
    run(default_directory, 0, 2)
    finalize(compendium)
