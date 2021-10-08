import os
import requests 
import json
import pandas as pd
import time
import datetime
import random
import logging

from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict
from typing import Optional
from dataclass_wizard import JSONWizard
from contextlib import suppress, contextmanager
from tqdm import tqdm


__version__ = '1.00'

now=datetime.datetime.now()
date=now.strftime('%y%m%d')
export_dir=os.path.realpath('PDN Scraper Exports')
msg_error_1='[sciscraper]: HTTP Error Encountered, moving to next available object. Reason Given:'

logging.basicConfig(filename=f'{date}_scraper.log', level=logging.DEBUG, 
                    format = '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

PRIME_SRC =os.path.realpath('sample.csv')
URL_DMNSNS ='https://app.dimensions.ai/discover/publication/results.json'
RESEARCH_DIR=os.path.realpath(f'{date}_PDN Research Papers From Scrape')
URL_SCIHUB='https://sci-hubtw.hkvisa.net/'

### Scrape Request Classes ###

class ScrapeRequest:
    '''The abstraction of the program's web scraping requests, which dynamically returns its appropriate subclasses based on the provided inputs.'''
    _registry = {}

    def __init_subclass__(cls, slookup_code, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[slookup_code] = cls
        
    def __new__(cls, s_bool: bool):
        '''
        The ScrapeRequest class looks for the boolean value passed to it from the FileRequest class.
        A value of True, or 1, would return a SciHubScrape subclass. Whereas a value of False, of 0, would return a JSONScrape subclass.
        '''
        if s_bool == False:
            slookup_code = 'json'
        elif s_bool == True:
            slookup_code = 'sci'
        else:
            raise Exception('[sciscraper]: Invalid prefix detected. Check to make sure you have a .csv and not a directory.')

        subclass = cls._registry[slookup_code]

        obj = object.__new__(subclass)
        return obj

    def download(self) -> None:
        raise NotImplementedError

class SciHubScrape(ScrapeRequest, slookup_code='sci'):
    '''
    The SciHubScrape class takes the provided string from a prior list comprehension.
    Using that string value, it posts it to the selected website, and then downloads the ensuing pdf file that appears as a result of that query.
    '''
    
    def download(self, search_text: str):
        self.sessions = requests.Session()
        self.base_url = URL_SCIHUB
        print(f'[sciscraper]: Delving too greedily and too deep for download links for {search_text}, by means of dark and arcane magicx.', end='\r')
        self.payload={'request': f'{search_text}'}
        with change_dir(RESEARCH_DIR):
            time.sleep(1)
            with suppress(requests.exceptions.HTTPError, requests.exceptions.RequestException):
                r=self.sessions.post(url=self.base_url, data=self.payload)
                r.raise_for_status()
                logging.info(r.status_code)
                soup=BeautifulSoup(r.text, 'lxml')
                self.links=list(((item['onclick']).split('=')[1]).strip("'") for item in soup.select('button[onclick^=\'location.href=\']'))
                self.enrich_scrape()

    def enrich_scrape(self, search_text:str):
        for link in self.links:
            paper_url=f'{link}=true'
            paper_title=f'{date}_{search_text.replace("/","")}.pdf'
            time.sleep(1)
            paper_content=(requests.get(paper_url, stream=True, allow_redirects=True)).content
            with open('temp_file.txt', 'wb') as _tempfile:
                _tempfile.write(paper_content)
            file=open(paper_title, 'wb')
            for line in open('temp_file.txt', 'rb').readlines():
                file.write(line)
            file.close()
            os.remove('temp_file.txt')

class JSONScrape(ScrapeRequest, slookup_code='json'):
    '''
    The JSONScrape class takes the provided string from a prior list comprehension.
    Using that string value, it gets the resulting JSON data, parses it, and then returns a dictionary, which gets appended to a list.
    '''

    def download(self, search_text:str) -> dict:
        self.sessions = requests.Session()
        self.search_field = self.specify_search(search_text)
        self.base_url = URL_DMNSNS
        print(f'[sciscraper]: Searching for {search_text} via a {self.search_field}-style search.', end='\r')
        querystring={'search_mode':'content','search_text':f'{search_text}','search_type':'kws','search_field':f'{self.search_field}'}
        time.sleep(1)

        with suppress(requests.exceptions.HTTPError, requests.exceptions.RequestException):
            r=self.sessions.get(self.base_url, params=querystring) 
            r.raise_for_status()
            logging.info(r.status_code)
        
        with suppress(json.decoder.JSONDecodeError,KeyError):
            docs=json.loads(r.text)['docs']
            for item in docs:
                return self.get_data_entry(item, keys=['title','author_list','publisher',
                    'pub_date','doi','id','abstract','acknowledgements',
                    'journal_title','volume','issue','times_cited',
                    'mesh_terms', 'cited_dimensions_ids'])

    def specify_search(self, search_text:str):
        if search_text.startswith('pub'):
            self.search_field='full_search'
        else:
            self.search_field='doi'
        return self.search_field

    def get_data_entry(self, item, keys: Optional[list]) -> dict:
        return asdict(DataEntry.from_dict({key: item.get(key,'') for key in keys}))

### Context Manager metaclass ###

@contextmanager
def change_dir(destination:str):
    try:
        __dest = os.path.realpath(destination)
        cwd = os.getcwd()
        if not os.path.exists(__dest):
            os.mkdir(__dest)
        os.chdir(__dest)
        yield
    finally:
        os.chdir(cwd)

### File Request Classes ###

class FileRequest:
    _registry = {}

    def __init_subclass__(cls, dlookup_code, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[dlookup_code] = cls

    def __new__(cls, target, slookup_key=None):
        if isinstance(target, str):
            if target.endswith('csv'): 
                dlookup_code = 'doi'
            else: raise Exception('[sciscraper]: Invalid prefix detected. Check to make sure you have a .csv and not a directory.')
        
        elif isinstance(target, pd.DataFrame): 
            dlookup_code = 'pub'
        else: raise Exception('[sciscraper]: Invalid prefix detected. Check to make sure you have a .csv and not a directory.')

        subclass = cls._registry[dlookup_code]

        obj = object.__new__(subclass)
        obj.slookup_key = slookup_key
        return obj

    def fetch_terms(self) -> None:
        raise NotImplementedError

class DOIRequest(FileRequest, dlookup_code='doi'):
    def __init__(self, target:str, slookup_key:bool=False):
        self.target = target
        self.slookup_key = slookup_key
        self.scraper = ScrapeRequest(self.slookup_key)

    def fetch_terms(self):
        with open(self.target, newline='') as f:
            self.df=[doi for doi in pd.read_csv(f, usecols=['DOI'])['DOI']]
            self.search_terms =(search_text for search_text in self.df if search_text is not None)
        
        return pd.DataFrame(list(self.scraper.download(search_text) for search_text in tqdm(list(self.search_terms))))

class PubIDRequest(FileRequest, dlookup_code='pub'):
    def __init__(self, target: pd.DataFrame, slookup_key:bool=False):
        print('\nGetting Pub IDs:')
        self.target = target
        self.slookup_key = slookup_key
        self.scraper = ScrapeRequest(self.slookup_key)

    def fetch_terms(self):
        self.df=self.target.explode('cited_dimensions_ids', 'title')
        self.search_terms =(search_text for search_text in self.df['cited_dimensions_ids'] if search_text is not None)
        self.src_title=pd.Series(self.df['title'])

        return pd.DataFrame(list(self.scraper.download(search_text) for search_text in tqdm(list(self.search_terms)))).join(self.src_title)

@dataclass(frozen=True, order=True)
class DataEntry(JSONWizard):
    title: str=''
    author_list: str=''
    publisher: str=''
    pub_date: str=''
    abstract: str=''
    acknowledgements: str=''
    journal_title: str =''
    volume: str =''
    issue: str =''
    times_cited: int = 0
    mesh_terms: list[str] = field(default_factory=list)
    cited_dimensions_ids: list[str] = field(default_factory=list)
    id: str=field(default='')
    doi: str=field(default='')

### General methods for exporting files and content ###

def export(dataframe: Optional[pd.DataFrame]):
    with change_dir(export_dir):
        print_id=random.randint(0,100)
        export_name=f'{date}_DIMScrape_Refactor_{print_id}.csv'
        msg_spreadsheetexported=f'\n[sciscraper]: A spreadsheet was exported as {export_name} in {export_dir}.\n'
        dataframe.to_csv(export_name)
        print(dataframe.head())
        logging.info(msg_spreadsheetexported)
        print(msg_spreadsheetexported)

def main():
    start=time.perf_counter()
    results = FileRequest(target=PRIME_SRC,slookup=False).fetch_terms()
    export(results)
    
    elapsed = time.perf_counter() - start
    msg_timestamp=f'\n[sciscraper]: Extraction finished in {elapsed} seconds.\n'
    logging.info(msg_timestamp)
    print(msg_timestamp)
    if not results:
        return
    quit()

if __name__ == '__main__':
    main()
