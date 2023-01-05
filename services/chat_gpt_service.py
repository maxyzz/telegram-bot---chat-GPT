import os

from cachetools import cached, TTLCache
from common.containers import DBContext

import openai

class ChatGPTservice:
    """This class provide answers from chatGPT"""

    # cache time 3 hours
    cache = TTLCache(maxsize=100, ttl=10800)

    def __init__(self):
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.model = os.getenv('OPENAI_MODEL')
            self.db_context = DBContext.mongo_db_context()
        except Exception as e:
            raise e
    
    # method for getting response from chatGPT
    def __get_response_from_openai(self, user_input):
        try:
            response_ai = openai.Completion.create(engine=self.model, prompt=user_input, max_tokens=1024).choices[0].text
        except Exception as e:
            raise e
        
        return response_ai

    # method for getting response from chatGPT
    def get_response_from_openai(self, user_input, user_name):
        self.db_context.save_query(user_input, user_name)
        return self.__get_response_from_openai(user_input)