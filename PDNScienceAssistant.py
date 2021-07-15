import os, pdfplumber, datetime, time, re, random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, names
import pandas as pd
from pdf2doi.pdf2doi import pdf2doi
from nltk import FreqDist
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import as_text

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
    
    for file_index,file in enumerate(files_to_check): #note: now the variable file is an element of files_to_check, not a numerical index
        try:
            print("\nPreparing file extraction...\n")
            filepath, filename = filenaming(folder, file)
            '''Generates the path to each pdf file'''
            print("\nBeginning extraction... \n")
            print(f"\nProcessing file {file_index} of {num_of_files} | {filepath}\n", end = "\r")
            extract(filename)
            '''The extraction process for each file gets appended to the compendium'''
            print(f"\nPackaging {filepath}... \n")
            continue
        except:
            pass

    '''Once the entire folder has been extracted, the dataframing process begins.'''
    finalize(compendium)

def filenaming(folder, file):
    '''Generates filename and locates file in directory'''
    filepath = str(file)
    filename = os.path.join(folder,filepath)
    return filepath,filename 
    
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
        
        manuscript = str(preprint).strip().lower()
        postprint = redaction(manuscript)
        all_words = tokenization(postprint)
        wordscore, research_word_overlap = word_match(all_words)
        doi_url, publisher, journal, volume, number, title, author, year = bibtexwriting(doi_results)
        fdist_top5 = frequency(all_words)
        sdist_top3 = study_design(research_word_overlap)

        '''
        Below is what gets passed back from the entire extraction process.
        '''
        
        cpdi = {

            'title': title,
            'author': author,
            'year': year,
            'doi': doi_results['identifier'],
            'doi_url': doi_url,
            'publisher': publisher,
            'journal': journal,
            'volume': volume,
            'number': number,
            'pages': n,
            'wordscore': wordscore,
            '5 Most Common Words': fdist_top5,
            'Study Design': sdist_top3
            
        }

        compendium.append(cpdi)
    return

def bibtexwriting(doi_results):
    '''This takes the validation info from pdf2doi and extracts the entries for appendation to the main compendium item dict'''
    bibtex = doi_results['validation_info']
    bp = BibTexParser(interpolate_strings=False)
    bib_database = bp.parse(bibtex)
    bib_database.entries[0]
    doi_url = as_text(bib_database.entries[0]['url'])
    publisher = as_text(bib_database.entries[0]['publisher'])
    journal = as_text(bib_database.entries[0]['journal'])
    volume = as_text(bib_database.entries[0]['volume'])
    number = as_text(bib_database.entries[0]['number'])
    title = as_text(bib_database.entries[0]['title'])
    author = as_text(bib_database.entries[0]['author'])
    year = as_text(bib_database.entries[0]['year'])

    return doi_url, publisher, journal, volume, number, title, author, year

def redaction(manuscript):
    '''
    All non-alphanumeric characters are removed.
    '''
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
    '''The remaining tokenized words are compared against several lists of words, by way of the lambda overlap function.
    target_words are the words we're looking for in a study. 
    bycatch_words are words that generally indicate a false positive
    research_words are words that help us determine the underlying study design: was it a randomized control or analytical?
    The length of the target_words minus the length of the bycatch words determines the wordscore.
    A positive wordscore means a paper is more likely than not to be a match, and vice versa.
    TO DO: have target words import from separate txt file'''

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
    sdist = FreqDist(research_word_overlap)
    sdist_top3 = sdist.most_common(3)
    return sdist_top3

def frequency(all_words):
    '''The five most common words in the paper are calculated.'''
    fdist = FreqDist(all_words) #Determines the frequency of the most common filtered words.
    fdist_top5 = fdist.most_common(5) #Gets the top 10 most common words
    return fdist_top5

def finalize(compendium):
    '''A dataframe is generated using pandas.'''
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
        }

    df_new = df\
        .groupby(df['title'])\
        .agg(aggregation_functions)
    print(df_new.head())
    finish(df_new)

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
        
#========================
#    MAIN LOOP TIME
#========================

compendium = []
main(dir, 0, 3)
finalize(compendium)
