from databoard_core.clients.parser import ParserClient


class DioParserClient(ParserClient):
    """
    Compatibility client for the DIO dialect with its formalism and dialect preconfigured.
    """

    def __init__(self):
        super().__init__()
        self.settings.update({'formalism': 'ebnf', 'dialect': 'dio'})
