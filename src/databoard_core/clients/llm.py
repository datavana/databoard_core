class LLmClient:
    """
    Base class for large language model clients.
    Don't use this class directly, use one of the subclasses instead.
    """
    def __init__(self):
        self.settings = {}
        self.client = None

    def getClient(self):
        """
        Load the client
        :return: The client class
        """
        return self.client

    def getCacheKey(self):
        """
        Generate a cache key from the LLM server and model

        :return: String
        """
        return 'undefined'

    def answer(self, prompt_content, prompt_system):
        """
        Generate a response

        :param prompt_content: The user prompt
        :param prompt_system: The system prompt
        :return: A dict with the response text and status
        """

        return {'text': None, 'status': None}
