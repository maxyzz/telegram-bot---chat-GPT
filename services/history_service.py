import os
import requests
from cachetools import cached, TTLCache
import codecs

import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from jinja2 import Template
import ciso8601
from common.containers import DBContext

class HistoryService:
    """This class provide information about statistics"""

     # cache time 3 hours
    cache = TTLCache(maxsize=100, ttl=10800)

    def __init__(self):
        try:
            self.covid_api_token = os.getenv('COVID_STAT_API_TOKEN')
            self.db_context = DBContext.mongo_db_context()
        except Exception as e:
            raise e
    
     # visualization of chartBar
    def visualize_bar_chart(self,x, x_label, y, y_label, title):
        
        # plt.figure(figsize = (10,4))
        # plt.title(title)
        # plt.xlabel(x_label)
        # plt.ylabel(y_label)
        # index = np.arange(len(x))
        # plt.xticks(index, x, fontsize=5, rotation=30)
        # plt.plot(x, y)
        
        months = mdates.MonthLocator()  # every month
        locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
        formatter = mdates.ConciseDateFormatter(locator)
        fig, ax = plt.subplots(figsize=(15, 4))
        ax.title.set_text(title)
        # Set common labels
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.plot(x, y)
        ax.format_xdata = mdates.DateFormatter('%Y-%m-%dT%H:%M:%S')
        
        # format the ticks
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_major_formatter(formatter)
        # ax.xaxis.set_minor_locator(months)
        # round to nearest years...
        datemin = np.datetime64(x[0],'Y')
        datemax = np.datetime64(x[-1],'Y') + np.timedelta64(1, 'Y')

        ax.set_xlim(datemin, datemax)
        
        ax.grid(True)
        fig.autofmt_xdate()
        
        return plt

    # method for getting history from API
    def __get_history_by_country_from_api(self, country_name):
        url = "https://covid-193.p.rapidapi.com/history"
        query_string = {'country': country_name}
        headers = {
            'x-rapidapi-host': "covid-193.p.rapidapi.com",
            'x-rapidapi-key': self.covid_api_token
        }
        response = requests.request("GET", url, headers=headers, params=query_string)
        return response.json()

    # method for visualization history
    @cached(cache)
    def __get_history_by_country_from_api_as_image(self, country_name):
        try:
            history_json = self.__get_history_by_country_from_api(country_name)
            if len(history_json['response']) == 0:
                with codecs.open('templates/idunnocommand.html', 'r', encoding='UTF-8') as file:
                    template = Template(file.read())
                    return template.render(text_command=country_name)
            else:
                dataframe = history_json['response']
                x=[]
                y=[]
                for data in dataframe:
                    if data['cases']['new']!=None:
                        x.append(ciso8601.parse_datetime(data['time']))
                        y.append(int(data['cases']['new'].replace('+','')))
                # # get last 10 days
                # x=x[:10]
                # y=y[:10]
                plt = self.visualize_bar_chart(x=x[::-1], x_label='Date', y=y[::-1], y_label='Total Cases', title='Daily Cases for ' + country_name.upper())
                plt.savefig('viz_hist.png')
        except Exception as e:
            raise e

    # method for getting history by country_name
    def get_history_by_country_name(self, country_name, user_name):
        self.db_context.save_query(country_name, user_name)
        return self.__get_history_by_country_from_api_as_image(country_name)