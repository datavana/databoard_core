#
# Ollama client class. Queries a local Ollama server to generate responses to prompts.
#

import os
import ollama

from databoard_core.clients import LLmClient

class OllamaClient(LLmClient):
    def __init__(self, ollama_host=None):
        """
        Queries the local Ollama

        By default, connects to localhost.
        Alternative server URLs can either be passed to the constructor
        or set in the environment variable DATABOARD_OLLAMA_SERVER.
        """

        super().__init__()

        if ollama_host is None:
            ollama_host = os.getenv('DATABOARD_OLLAMA_SERVER', 'localhost')

        self.settings = {
            'ollama_host': ollama_host,
            'ollama_port' : 11434,
            'ollama_model' : 'llama3.2'
        }

    def getClient(self):
        if self.client is None:
            host = 'http://' + self.settings['ollama_host'] + ':' + str(self.settings['ollama_port'])
            self.client = ollama.Client(host=host)
        return self.client

    def answer(self, prompt_content, prompt_system):
        client = self.getClient()

        status = ''
        result = ''

        try:
            response = client.generate(
                model = self.settings['ollama_model'],
                system= prompt_system,
                prompt = prompt_content,
                stream=False
            )
            result = response['response']

        except Exception as e:
            status = str(e)

        return {'text' : result, 'status' : status}
