import os
import requests
import codecs
import ciso8601

from jinja2 import Template
from cachetools import cached, TTLCache
from common.containers import DBContext

import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt

class StatisticsService:
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
    def visualize_bar_chart(self,x1, x_label1, x2, x_label2, title):
        # Figure Size
        fig, ax = plt.subplots(figsize =(16, 9))
        
        # Horizontal Bar Plot
        ax.barh(x_label1, x1)
        
        # Remove axes splines
        for s in ['top', 'bottom', 'left', 'right']:
            ax.spines[s].set_visible(False)
        
        # Remove x, y Ticks
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        
        # Add padding between axes and labels
        ax.xaxis.set_tick_params(pad = 5)
        ax.yaxis.set_tick_params(pad = 10)
        
        # Add x, y gridlines
        ax.grid(b = True, color ='grey',
                linestyle ='-.', linewidth = 0.5,
                alpha = 0.2)
        
        # Show top values
        ax.invert_yaxis()
        
        # Add annotation to bars
        for i in ax.patches:
            plt.text(i.get_width()+0.2, i.get_y()+0.5,
                    str(round((i.get_width()), 2)),
                    fontsize = 10, fontweight ='bold',
                    color ='grey')
        
        # Add Plot Title
        ax.set_title(title,
                    loc ='left', )
        
        # # Add Text watermark
        # fig.text(0.9, 0.15, 'Jeeteshgavande30', fontsize = 12,
        #         color ='grey', ha ='right', va ='bottom',
        #         alpha = 0.7)
        
        return plt
    # method for getting statistics from API by country
    def __get_statistics_by_country_from_api(self, country_name):
        url = "https://covid-193.p.rapidapi.com/statistics"
        query_string = {'country': country_name}
        headers = {
            'x-rapidapi-host': "covid-193.p.rapidapi.com",
            'x-rapidapi-key': self.covid_api_token
        }
        response = requests.request("GET", url, headers=headers, params=query_string)
        return response.json()

    # method for getting statistics from API for all countries
    def __get_statistics_all_countries_from_api(self):
        url = "https://covid-193.p.rapidapi.com/statistics"
        headers = {
            'x-rapidapi-host': "covid-193.p.rapidapi.com",
            'x-rapidapi-key': self.covid_api_token
        }
        response = requests.request("GET", url, headers=headers)
        return response.json()

    # method for rendering statistics as html
    @cached(cache)
    def __get_statistics_by_country_as_html(self, country_name):
        try:
            statistics_json = self.__get_statistics_by_country_from_api(country_name)
            if len(statistics_json['response']) == 0:
                with codecs.open('templates/idunnocommand.html', 'r', encoding='UTF-8') as file:
                    template = Template(file.read())
                    return template.render(text_command=country_name)
            else:
                with codecs.open('templates/country_statistics.html', 'r', encoding='UTF-8') as file:
                    template = Template(file.read())
                    return template.render(date=ciso8601.parse_datetime(statistics_json['response'][0]['time']).date(),
                                           country=statistics_json['response'][0]['country'].upper(),
                                           new_cases=statistics_json['response'][0]['cases']['new'],
                                           active_cases=statistics_json['response'][0]['cases']['active'],
                                           critical_cases=statistics_json['response'][0]['cases']['critical'],
                                           recovered_cases=statistics_json['response'][0]['cases']['recovered'],
                                           total_cases=statistics_json['response'][0]['cases']['total'],
                                           new_deaths=statistics_json['response'][0]['deaths']['new'],
                                           total_deaths=statistics_json['response'][0]['deaths']['total'])
        except Exception as e:
            raise e

    # method for getting statistic for top 20 countries as image
    def __get_top_20_country_from_api_as_image(self,case):
        try:
            statistics_json = self.__get_statistics_all_countries_from_api()
            if len(statistics_json['response']) == 0:
                with codecs.open('templates/idunnocommand.html', 'r', encoding='UTF-8') as file:
                    template = Template(file.read())
                    return template.render(text_command='top 20 countries')
            else:
                dataframe = statistics_json['response']
                if case=='1':
                    total=[]
                    population=[]
                    country=[]
                    for i in range(20):
                        maxDeath=0
                        for data in dataframe:
                            if data['deaths']['total']!=None:
                                if maxDeath<data['deaths']['total']:
                                    maxDeath=data['deaths']['total']
                                    countryDeath=data['country']
                                    populationDeath=data['population']
                        total.append(maxDeath)
                        population.append(populationDeath)
                        country.append(countryDeath)
                        dataframe = list(filter(lambda x: x['country']!=countryDeath,dataframe))
                    plt = self.visualize_bar_chart(x1=total, x_label1=country,x2=[],x_label2=[], title='TOP 20 countries for deaths' )
                elif case=='2':
                    country=[]
                    dailyCases=[]
                    for i in range(20):
                        maxCases=0
                        for data in dataframe:
                            if data['cases']['new']!=None:
                                dailyCase=int(data['cases']['new'].replace('+',''))
                                if maxCases<dailyCase:
                                    maxCases=dailyCase
                                    countryCases=data['country']
                        dailyCases.append(maxCases)
                        country.append(countryCases)
                        dataframe = list(filter(lambda x: x['country']!=countryCases,dataframe))
                    plt = self.visualize_bar_chart(x1=dailyCases, x_label1=country,x2=[],x_label2=[], title='TOP 20 countries for daily cases' )
                plt.savefig('viz_stat.png')
        except Exception as e:
            raise e

    # method for getting statistics by country_name
    def get_statistics_by_country_name(self, country_name, user_name):
        self.db_context.save_query(country_name, user_name)
        return self.__get_statistics_by_country_as_html(country_name)

    # method for getting top 20 country deaths
    def get_top_20_country(self, case, user_name):
        self.db_context.save_query('top 20 countries', user_name)
        return self.__get_top_20_country_from_api_as_image(case)

    # method for getting statistics of users and queries
    def get_statistics_of_users_queries(self):
        query_statistics = self.db_context.get_users_queries()
        with codecs.open('templates/query_statistics.html', 'r', encoding='UTF-8') as file:
            template = Template(file.read())
            return template.render(queries=query_statistics['queries'], users=query_statistics['users'])