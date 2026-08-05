#
# UniGPT client class. Queries an OpenAI compatible server to generate responses to prompts.
#

import os
import json
from openai import OpenAI, NOT_GIVEN, APIStatusError

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
           str(self.settings.get('gpt_url','')),
            str(self.settings.get('gpt_modelname', '')),
            str(self.settings.get('gpt_temperature', ''))
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
            # Defaults
            modelname = self.settings.get('gpt_modelname', None)
            if modelname is None:
                modelname = 'Llama-3.3-70B'

            try:
                temperature = self.settings.get('gpt_temperature', None)
                if temperature is None:
                    temperature = NOT_GIVEN
                else:
                    temperature = float(temperature)
            except ValueError:
                raise ValueError("The 'temperature' setting must be a valid float.")

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
                model = modelname,
                temperature = temperature
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
            status = self._format_error(e)

        result = {'text': result, 'status': status, 'tokens': tokens}
        return result

    def _format_error(self, e):
        if self.settings.get('rawError', True):
            return str(e)

        msg = type(e).__name__
        if isinstance(e, APIStatusError):
            statuscode = str(e.status_code)
            reason = self._classify_error(e, getattr(e, 'code', None))
            if reason is not None:
                statuscode += " " + reason

            msg += f' ({statuscode})'
        elif isinstance(e, ValueError):
            msg += f' ({str(e)})'

        return msg

    def _classify_error(self, e, code):
        # 1) Clean messages
        if code and not str(code).isdigit():
            return str(code)

        # 2) Search heuristic
        haystack = self._error_haystack(e).lower()
        if any(s in haystack for s in (
                'contextwindowexceeded',
                'context_length_exceeded',
                'context window',
        )):
            return 'context window exceeded'

        return None

    def _error_haystack(self, e):
        """Suchtext aus möglichst strukturierten Quellen bauen."""
        body = getattr(e, 'body', None)
        if isinstance(body, dict):
            err = body.get('error', body)
            if isinstance(err, dict):
                return str(err.get('message', '')) or str(err)
            return str(err)
        return getattr(e, 'message', None) or str(e)

