#
# UniGPT client class. Queries an OpenAI compatible server to generate responses to prompts.
#

import os
import json
from openai import OpenAI, NOT_GIVEN

from databoard_core import utils
from databoard_core.clients import LLmClient


class UniGptClient (LLmClient):
    def __init__(self, base_url=None, access_token=None):
        """
        Queries UniGPT

        Either pass URL and token to the contructor or
        set the environment variables DATABOARD_GPT_SERVER
        and DATABOARD_GPT_ACCESSTOKEN to access the server

        """
        super().__init__()

        if base_url is None:
            base_url = os.getenv('DATABOARD_GPT_SERVER')
        if access_token is None:
            access_token = os.getenv('DATABOARD_GPT_ACCESSTOKEN')

        self.settings = {
            'gpt_url': base_url,
            'gpt_token' : access_token
        }

    def setModel(self, modelname):
        """
        Set the model to use

        One of the following models:
        ['gpt-oss-120b', 'Apertus-8B-Instruct-2509', 'mistral-small', 'gemma-3-27b-it', 'Llama-3.3-70B',
         'Qwen3-Embedding-4B', 'mixtral-8x7B', 'gemma-3']

        :param modelname:
        :return:
        """
        self.settings['gpt_modelname'] = modelname

    def getCacheKey(self):
        return utils.hash(
            self.settings.get('gpt_url',''),
            self.settings.get('gpt_modelname', ''),
            self.settings.get('gpt_temperature', '')
        )

    def getClient(self):
        if self.client is None:
            self.client = OpenAI(api_key=self.settings['gpt_token'], base_url=self.settings['gpt_url'])
        return self.client

    def models(self):
        """
        List available models
        :return:
        """
        client = self.getClient()
        models = client.models.list()
        return [m.id for m in models.data]

    def answer(self, prompt_content, prompt_system):
        client = self.getClient()

        result = ''
        status = None
        tokens = None

        try:

            response = client.chat.completions.create(
                messages=[
                    {
                        'role': 'system',
                        'content':  prompt_system,
                    },
                    {
                        'role': 'user',
                        'content': prompt_content,
                    },
                ],
                model = self.settings.get('gpt_modelname', 'Llama-3.3-70B'),
                temperature = self.settings.get('gpt_temperature', NOT_GIVEN)
            )

            if self.settings.get('rawAnswer', False):
                if hasattr(response, "to_dict"):
                    result = response.to_dict()
                elif hasattr(response, "__dict__"):
                    result = vars(response)
                else:
                    result = str(response)
                result = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                result = response.choices[0].message.content
                tokens = response.usage.total_tokens

        except Exception as e:
            status = str(e)

        result = {'text': result, 'status': status, 'tokens': tokens}
        return result
