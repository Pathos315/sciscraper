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

__version__ = '0.0.10'

now=datetime.datetime.now()
date=now.strftime('%y%m%d')
export_dir=os.path.realpath('PDN Scraper Exports')
research_dir=os.path.realpath('PDN Research Papers From Scrape')
msg_error_1='HTTP Error Encountered, moving to next available object. Reason Given:'

logging.basicConfig(filename=f'scraper_v008.log', level=logging.DEBUG, 
                    format = '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

PRIME_SRC ='sample.csv'
URL_DMNSNS ='https://app.dimensions.ai/discover/publication/results.json'
URL_SCIHUB='https://sci-hub.ru'

class ImportFromCSV:
    def __init__(self, target:str):
        self.target = target
        with open(self.target, newline='') as f:
            self.df=[doi for doi in pd.read_csv(f, usecols=['DOI'])['DOI']]
        self.search_terms =(self.search_text for self.search_text in self.df if self.search_text is not None)
        self.numb_files=len(self.df)
        
    def do_scrape(self):
        self.output = pd.DataFrame([run_scrape(self.search_text, search_field='doi', total=self.numb_files) for self.search_text in list(self.search_terms)])
        return self.output

    def do_export(self):
        return export(self.output)

class ScrapeWithPubID:
    def __init__(self, target: pd.DataFrame):
        print('\nGetting Pub IDs:')
        self.target = target
        self.df=target.explode('cited_dimensions_ids', 'title')
        self.search_terms =(self.search_text for self.search_text in self.df['cited_dimensions_ids'] if self.search_text is not None)
        self.src_title=pd.Series(self.df['title'])
        self.numb_files=len(self.df)

    def do_scrape(self):
        self.output = (pd.DataFrame([run_scrape(self.search_text, 'full_search', total=self.numb_files) for self.search_text in list(self.search_terms)])).\
            join(self.src_title, lsuffix='_new', rsuffix='_sources')
        return self.output

    def do_export(self):
        return export(self.output)

class ScrapeFromSciHub:
    def __init__(self, target: pd.DataFrame):
        print('\nPreparing to webscrape:')
        self.df = self.target = target
        self.search_terms =(self.search_text for self.search_text in self.df['doi'] if self.search_text is not None)
        self.numb_files=len(self.df)

    def do_post(self):
        return [sci_post(self.search_text, self.numb_files) for self.search_text in list(self.search_terms)]

def sci_post(search_text, total):
    print(f'Delving too greedily and too deep for download links for {search_text}, by means of dark and arcane magicx. | Total Entries: {total}', end='\r')
    querystring={'request': f'{search_text}'}

    if not os.path.exists(research_dir):
        os.mkdir(research_dir)
    else: 
        os.chdir(research_dir)

    time.sleep(1)

    try:
        r=requests.post(URL_SCIHUB, data=querystring)
        r.raise_for_status()
        logging.info(r.status_code)
        soup=BeautifulSoup(r.text, 'lxml')
        links=[((item['onclick']).split('=')[1]).strip("'") for item in soup.select('button[onclick^=\'location.href=\']')]
        for link in links:
            paper_url=f'{link}=true'
            paper_title=f'{date}_{str(search_text).replace("/","")}.pdf'
            time.sleep(1)
            paper_content=(requests.get(paper_url, stream=True, allow_redirects=True)).content
            with open('temp_file.txt', 'wb') as _tempfile:
                _tempfile.write(paper_content)
            file=open(f'{paper_title}', 'wb')
            for line in open('temp_file.txt', 'rb').readlines():
                file.write(line)
            file.close()
            os.remove('temp_file.txt')

    except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as errh:
        print(msg_error_1, errh)
        logging.error(r.status_code, errh)
        return None
      
def run_scrape(search_text, search_field:str, total) -> dict:
    print(f'Searching for {search_text} via a {search_field}-style search | Total Entries: {total} | Less than {total % 60} minutes remaining from {now}', end='\r')
    querystring={'search_mode':'content','search_text':f'{search_text}','search_type':'kws','search_field':f'{search_field}'}
    msg_error_2=f'{search_text} failed to serialize to Python object, moving to next available object. Reason Given:'
    time.sleep(1)

    try:
        r=requests.request('GET', URL_DMNSNS, params=querystring) 
        r.raise_for_status()
        logging.info(r.status_code)
        
    except (requests.exceptions.HTTPError,requests.exceptions.RequestException) as errh:
        print(msg_error_1, errh)
        logging.error(r.status_code, errh)
        return None
    
    try:
        docs=json.loads(r.text)['docs']
        for item in docs:
            return get_data_entry(item, keys=['title','author_list','publisher',
                    'pub_date','doi','id','abstract','acknowledgements',
                    'journal_title','volume','issue','times_cited',
                    'mesh_terms', 'cited_dimensions_ids'])
    
    except (json.decoder.JSONDecodeError,KeyError) as err:
        print(msg_error_2, err)
        logging.error(err)
        return None

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

def get_data_entry(item, keys: Optional[list]) -> dict:
    return asdict(DataEntry.from_dict({key: item.get(key,'') for key in keys}))

def export(dataframe: Optional[pd.DataFrame]):
    if not os.path.exists(export_dir):
        os.mkdir(export_dir)
    else: 
        os.chdir(export_dir)
    print_id=random.randint(0,100)
    export_name=f'{date}_DIMScrape_Refactor_{print_id}.csv'
    msg_spreadsheetexported=f'\nA spreadsheet was exported as {export_name} in {export_dir}.\n'
    dataframe.to_csv(export_name)
    print(dataframe.head())
    logging.info(msg_spreadsheetexported)
    print(msg_spreadsheetexported)
    
def main():
    t1=time.perf_counter()
    d = ImportFromCSV(target=PRIME_SRC)
    output_doi = d.do_scrape()
    d.do_export()
    p = ScrapeWithPubID(output_doi)
    p.do_scrape()
    p.do_export()
    t2=time.perf_counter()
    msg_timestamp=f'\nExtraction finished in {t2-t1} seconds.\n'
    logging.info(msg_timestamp)
    print(msg_timestamp)
    quit()

if __name__ == '__main__':
    main()
