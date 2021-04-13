#Module to download data files containing COVID19 data, cleaning and
#organising data and writing cleaned data to a database file.

#This module(when executed) also replaces the downloaded files with new file from net
#which are older than 2 days

#Part of Project: COVID19 Statstics\Visualisation


#https://covid19.who.int/WHO-COVID-19-global-data.csv
#https://covid.ourworldindata.org/data/owid-covid-data.csv
#https://api.covid19india.org/data.json
#https://api.covid19india.org/states_daily.json
#https://api.covid19india.org/data.json

import requests
from datetime import *
from pathlib import Path
import os
import platform
import pickle
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import traceback

#Setting pandas options for debugging\output to shell 
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

#List of file names downloaded from internet and used for making
#pandas DataFrame objects
files = [
    'covid19_global_data.csv',
    'states_daily.json',
    'states_total.json'
    ]

#List of download urls
urls = [
    'https://covid.ourworldindata.org/data/owid-covid-data.csv',
    'https://api.covid19india.org/states_daily.json',
    'https://api.covid19india.org/data.json'
    ]

#Flag to check if files are downloaded or not
download = False

try:
    for file, url in zip(files, urls):

        #Creating neccessary file paths and data directory
        if platform.system() == 'Windows':
            my_file = Path('.\\data\\'+file)
            my_file.parent.mkdir(exist_ok=True)
            directory = '.\\data\\'
        else:
            my_file = Path('./data/'+file)
            my_file.parent.mkdir(exist_ok=True)
            directory = './data/'

        #Check if file already exists
        if my_file.is_file():

            file_mtime = datetime.fromtimestamp(os.stat(my_file)[-2]) #file modify time
            now = datetime.now()

            time_elapsed = now - file_mtime

        #Execute this block if file does not exist or file is older than 2 days
        if not my_file.is_file() or time_elapsed > timedelta(hours=23):
            
            response = requests.get(url)
            response.raise_for_status()    # Check that the request was successful

            download = True

            with open(my_file, "wb") as f:
                f.write(response.content)

    if download:
        
        #Defining df containing data of all countries (Aggregate)
        parent_df = pd.read_csv(directory+'covid19_global_data.csv',
                                header=0,
                                #index_col=['location', 'date'],
                                #nrows=70,
                                usecols=['iso_code', 'continent', 'location',
                                         'date', 'total_cases', 'new_cases',
                                         'total_deaths', 'new_deaths',
                                         'new_tests', 'total_tests',
                                         'tests_per_case', 'positive_rate',
                                         'population',
                                         'population_density'],
                                parse_dates=['date']
                                )

        #Cleaning and organising parent_df
        i = parent_df[parent_df.location=='International'].index
        parent_df.drop(i, inplace=True)

        parent_df = parent_df.fillna(value={'total_cases':0, 'new_cases':0,
                                            'total_deaths':0, 'new_deaths':0,
                                            'new_tests':0, 'total_tests':0,
                                            'tests_per_case':0, 'positive_rate':0,
                                            'population':0, 'population_density':0,
                                            'continent':'Global'}
                                     )

        parent_df = parent_df.astype(dtype={'iso_code':'string', 'continent':'string',
                                            'location':'string', 'total_cases':'int64',
                                            'new_cases':'int64', 'total_deaths':'int64',
                                            'new_deaths':'int64', 'new_tests':'int64',
                                            'total_tests':'int64',
                                            'tests_per_case':'float64',
                                            'positive_rate':'float64',
                                            'population':'int64',
                                            'population_density':'float64'}
                                     )

        parent_df.rename(columns={'location':'country'}, inplace=True)


        #Defining df containing data of all states of India (Daily)
        with open(directory+'states_daily.json', mode='r') as fp:
            dict_india = json.load(fp) 

        india_df = pd.DataFrame(dict_india['states_daily'])
        india_df.drop(columns='dateymd', inplace=True)

        #Cleaning and organising india_df
        india_df = india_df.melt(id_vars=['date','status'])

        india_df = pd.pivot_table(india_df,values='value',
                                  index=['date','variable'],
                                  columns=['status'], aggfunc=np.sum)

        india_df.reset_index(inplace=True)
        india_df['date']= pd.to_datetime(india_df['date'])
        india_df.sort_values(by=['variable', 'date'], inplace=True)
        india_df.columns.name = None
        india_df.reset_index(drop=True, inplace=True)

        india_df.rename(columns={'variable':'state',
                                 'Confirmed':'confirmed',
                                 'Deceased':'deceased',
                                 'Recovered':'recovered'},
                        inplace=True)

        india_df = india_df.astype(dtype={'state':'string',
                                          'confirmed':'int64',
                                          'deceased':'int64',
                                          'recovered':'int64'})

        #Replacing states codes in india_df with state names
        with open('.\\data\\state_code_dict.pickle', 'rb') as fh:
            state_dict = pickle.load(fh)
        #state_dict = code_to_dict()
        state_dict['tt'] = 'Total'
        india_df['state'].replace(to_replace=state_dict,
                         inplace=True)


        #Defining df containing data of all states of India (Aggregate)
        with open(directory+'states_total.json', mode='r') as fp:
            dict_in_tot = json.load(fp) 

        in_tot_df = pd.DataFrame(dict_in_tot['statewise'])

        #Cleaning and organising in_tot_df
        in_tot_df.drop(columns=['deltaconfirmed', 'deltadeaths', 'deltarecovered',
                                'migratedother', 'statenotes'],
                       inplace=True)

        #in_tot_df.columns.tolist()
        cols = ['statecode', 'state',  'lastupdatedtime', 'confirmed',
                'active', 'recovered', 'deaths', ] #Reordering columns
        in_tot_df = in_tot_df[cols]

        in_tot_df.drop(index=in_tot_df[in_tot_df['state']=='State Unassigned'].index,
                       inplace=True)

        in_tot_df.reset_index(drop=True, inplace=True)
        in_tot_df['lastupdatedtime']= pd.to_datetime(in_tot_df['lastupdatedtime'],
                                                     dayfirst=True)
        in_tot_df = in_tot_df.astype({'statecode':'string',
                                      'state':'string',
                                      'confirmed':'int64',
                                      'active':'int64',
                                      'recovered':'int64',
                                      'deaths':'int64'})
except Exception:
    e = traceback.format_exc()
    print(e)

else:
    if download:
        #Writing the cleaned DataFrames(3) to database file
        engine = create_engine(f'sqlite:///{directory}data.db', echo=False)

        parent_df.to_sql('global', con=engine, if_exists='replace', index_label='ID')
        india_df.to_sql('india_daily', con=engine, if_exists='replace', index_label='ID')
        in_tot_df.to_sql('india_total', con=engine, if_exists='replace', index_label='ID')


if __name__ == '__main__':
    
    if download:
        print("Files downloaded succesfully:")

    try:
        for file in files:
            print(file,
                  datetime.fromtimestamp(os.stat(my_file)[-2]).strftime('%Y-%m-%d %H:%M:%S'))
    except FileNotFoundError:
        print('Files not found.')
