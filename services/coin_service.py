import os
import requests

from cachetools import cached, TTLCache
from common.containers import DBContext
import codecs

from jinja2 import Template
import ciso8601

class CoinService:
    """This class provide quotes for coin"""

    # cache time 3 hours
    cache = TTLCache(maxsize=100, ttl=10800)

    def __init__(self):
        try:
            self.coin_api_token = os.getenv('X_CMC_PRO_API_KEY')
            self.db_context = DBContext.mongo_db_context()
        except Exception as e:
            raise e
    
    # method for getting quotes fpr coin from API
    def __get_quotes_for_coin_from_api(self, coin, currency):
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        query_string = {'symbol': coin,'convert':currency}
        headers = {
            'X-CMC_PRO_API_KEY': self.coin_api_token,
            'Accept': 'application/json'
        }
        response = requests.request("GET", url, headers=headers, params=query_string)
        return response.json()

    # method for parsing as html
    def __get_quotes_for_coin_as_html(self, coin, currency):
        try:
            coin_json = self.__get_quotes_for_coin_from_api(coin,currency)
            if len(coin_json['data']) == 0:
                with codecs.open('templates/idunnocommand.html', 'r', encoding='UTF-8') as file:
                    template = Template(file.read())
                    return template.render(text_command=coin + ',' + currency)
            else:
                with codecs.open('templates/coin_quotes.html', 'r', encoding='UTF-8') as file:
                    template = Template(file.read())
                    return template.render(date=ciso8601.parse_datetime(coin_json['data'][coin]['last_updated']).date(),
                                           coin_currency=coin_json['data'][coin]['symbol'].upper() + ':' + currency.upper(),
                                           price=coin_json['data'][coin]['quote'][currency]['price'],
                                           volume_24h=coin_json['data'][coin]['quote'][currency]['volume_24h'],
                                           volume_change_24h=coin_json['data'][coin]['quote'][currency]['volume_change_24h'],
                                           percent_change_1h=coin_json['data'][coin]['quote'][currency]['percent_change_1h'],
                                           percent_change_7d=coin_json['data'][coin]['quote'][currency]['percent_change_7d'],
                                           percent_change_30d=coin_json['data'][coin]['quote'][currency]['percent_change_30d'],
                                           percent_change_60d=coin_json['data'][coin]['quote'][currency]['percent_change_60d'],
                                           percent_change_90d=coin_json['data'][coin]['quote'][currency]['percent_change_90d'],)
        except Exception as e:
            raise e
    
    # method for getting quotes by coin and currency
    def get_coin_quotes_by_coin_currency(self, coin, currency, user_name):
        self.db_context.save_query(coin + ':' + currency, user_name)
        return self.__get_quotes_for_coin_as_html(coin, currency)