class Client:
    """
    Base class for data processing clients.
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
        Generate a cache key for storing answers based on inputs

        :return: String
        """
        return 'undefined'

    def answer(self, prompt):
        """
        Generate a response

        :param prompt: An object with the input to process by the client.
                       The type of object depends on the specific class.
                       For example, the LlmClient expects an object with keys 'user' and 'system'.
        :return: A dict with the response text and status
        """

        return {'text': None, 'status': None}
