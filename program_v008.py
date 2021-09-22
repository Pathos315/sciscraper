import os, requests, json, pandas as pd, time, datetime, json, random, logging

__version__ = '0.0.8'

now = datetime.datetime.now()
date = now.strftime('%y%m%d')
export_folder = 'PDN Scraper Exports'

logging.basicConfig(filename=f'scraper_v008.log', level=logging.DEBUG, 
                    format = '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

path = '/Users/johnfallot/Downloads/Ideas_Evidence_2.csv'
URL_DMNSNS = "https://app.dimensions.ai/discover/publication/results.json"

def doi_scrape(target: str) -> pd.DataFrame:
    with open (target, newline='') as f:
        print ('\nGetting digital object identifiers (dois):')
        _df = [doi for doi in pd.read_csv(f, usecols=['DOI'])['DOI']]
        _search_terms = (search_text for search_text in _df)
        numb_files = len(_df)
        return pd.DataFrame([run_scrape(search_text, search_field='doi', total=numb_files) for search_text in (_search_terms)])

def pub_scrape(target: pd.DataFrame) -> pd.DataFrame:
    print ('\nGetting Pub IDs:')
    _df = target.explode('cited_dimensions_ids', 'title')
    _search_terms = (search_text for search_text in _df['cited_dimensions_ids'])
    _src_title = pd.Series(_df['title'])
    numb_files = len(_df)
    return (pd.DataFrame([run_scrape(i, 'full_search',total=numb_files) for i in (_search_terms)])).join(_src_title, lsuffix='_new', rsuffix='_sources')

def run_scrape(search_text=None, search_field:str=None, total=None):
    print (f'Searching for {search_text} via a {search_field}-style search | Total Entries: {total} | Less than {total % 60} minutes remaining from {now}', end='\r')
    querystring = {"search_mode":"content","search_text":f"{search_text}","search_type":"kws","search_field":f"{search_field}"}
    time.sleep(1)

    try:
        r = requests.request("GET", URL_DMNSNS, params=querystring) 
        r.raise_for_status()
        logging.info(r.status_code)
        
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error Encountered, moving to next available object. Reason Given:", errh)
        logging.error(r.status_code, errh)
        pass

    except requests.exceptions.RequestException as e:
        print("Unexcepted error encountered, moving to next available object. Reason Given:", e)
        logging.error(r.status_code, e)
        pass
    
    try:
        docs = json.loads(r.text)['docs']
        for item in docs:
            return get_data_entry(item, keys=['title','author_list','publisher',
                    'pub_date','doi','id','abstract','acknowledgements',
                    'journal_title','volume','issue','times_cited',
                    'mesh_terms', 'cited_dimensions_ids'])
    
    except json.decoder.JSONDecodeError as je:
        print(f"{search_text} failed to serialize to Python object, moving to next available object. Reason Given:", je)
        logging.error(je)
        pass

    except KeyError as ke:
        print(f"{search_text} failed to serialize to Python object, moving to next available object. Reason Given:", ke)
        logging.error(ke)
        pass

def get_data_entry(item, keys:list = None):
    return {key: item.get(key,'') for key in keys}

def export(dataframe: pd.DataFrame=None):
    os.mkdir(export_folder) if not os.path.exists(export_folder) else os.chdir(export_folder)
    print_id = random.randint(0,100)
    export_name = f'{date}_DIMScrape_Refactor_{print_id}.csv'
    dataframe.to_csv(export_name)
    print(dataframe.head())
    logging.info(f"\nA spreadsheet was exported to {export_name} in {export_folder}.\n")
    print(f"\nA spreadsheet was exported to {export_name} in {export_folder}.\n")

def main():
    t1 = time.perf_counter()
    res1 = doi_scrape(path)
    export(res1)
    res2 = pub_scrape(res1)
    export(res2)
    t2 = time.perf_counter()
    logging.info(f'\nExtraction finished in {t2-t1} seconds.\n')
    print(f'\nExtraction finished in {t2-t1} seconds.\n')
    quit()

if __name__ == "__main__":
    main()