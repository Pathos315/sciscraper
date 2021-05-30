import os
import PyPDF2
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
import pandas as pd
from PyPDF2 import PdfFileReader

class LabAsst:

    def extract(self):
        self.study_paths = []
        self.titles = []

        d = "/Users/johnfallot/Desktop/PDN_studies"
        for path in os.scandir(d):
            self.full_path = os.path.join(d, path)
            if os.path.isfile(self.full_path):
                self.study_paths.append(self.full_path)
                self.titles.append(path)
                return
            
    def read(self):
        for path in self.study_paths:
            self.read_pdf = PyPDF2.PdfFileReader(path)
            return
    
    def transform(self):
        for page_num in range(self.read_pdf.getNumPages()):
            self.page = self.read_pdf.getPage(page_num)
            self.prime_extraction = self.page.extractText() #gets the raw text from each page using PDFPy2
            self.no_grawlix = self.prime_extraction.translate({ord(i): None for i in '%$><:;"][}{|/``~-#@!&*_\n'}) #Deletes all extraneous punctuation marks
            self.stop_words = set(stopwords.words('english')) #sets the stopwords to be filtered out
            self.word_tokens = nltk.tokenize.word_tokenize(self.no_grawlix) #Breaks up and tokenizes the remaining text
            self.filtered_words = [w for w in self.word_tokens if not w in self.stop_words] #Filters out the stopwords
            self.filtered_words = [] 

            for w in self.word_tokens:
                if w not in self.stop_words:
                    self.filtered_words.append(w) #The remaining non-stop words are appended to a new list

            self.token_p = nltk.tokenize.blankline_tokenize(self.no_grawlix) #Meanwhile, the full paragraphs are tokenized.
            self.fdist = FreqDist(self.filtered_words) #Determines the frequency of the most common filtered words.
            self.fdist_top10 = self.fdist.most_common(10) #Gets the top 10 most common words
            self.results = sorted(self.fdist_top10, reverse=True)

            self.dictionary = {

                'Name': self.titles,
                'Full Text': self.no_grawlix,
                'Results': self.results,
                'Pages': self.read_pdf.getNumPages()

                }

            study_list.append(self.dictionary)

        return

labsist = LabAsst()
study_list = []

for i in range(0,3):

    print(f'Getting Studies, {i}')

    labsist.extract()
    labsist.read()
    labsist.transform()

df = pd.DataFrame(study_list)
print(df.head())
df.to_csv('210530_studies_4.csv')