import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from urllib.request import urlopen
import pickle
import platform

def code_to_dict():
    url = 'https://en.wikipedia.org/wiki/States_and_union_territories_of_India'
    html = urlopen(url) 
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all('table')

    iso = []
    states = []

    num = 1

    for table in tables[3:5]:
        rows = table.find_all('tr')
        
        for row in rows:
            states.append(row.find_all('th')[0].text.strip())
            cells = row.find_all('td')
            
            
            if len(cells) > 1:
                iso.append(cells[0].text.lstrip('IN ').lstrip('-').rstrip(' \n').lower())
                
        num += 1

        if num > 2:
            break

    states.remove('State')
    states.remove('Union territory')

    dict_state = dict(zip(iso, states))

    if platform.system() == 'Windows':
        directory = '.\\data\\'
    else:
        directory = './data/'

    with open(f'{directory}state_code_dict.pickle', 'wb') as fh:
        pickle.dump(dict_state, fh)

    return dict_state

if __name__=='__main__':
    dict_state = code_to_dict()
    print(dict_state)


