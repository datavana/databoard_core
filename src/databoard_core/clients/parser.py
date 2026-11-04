class ParserClient:
    """
    Base class for parser clients.
    Don't use this class directly, use one of the subclasses instead.

    A parser client turns a text written in one Dialect into XML.
    """
    def __init__(self):
        self.settings = {}

    @staticmethod
    def makeError(level, code, line, column, message):
        """
        Create an error entry

        :param level: One of 'notice', 'warning', 'error', 'fatal'
        :param code: The error code of the parser
        :param line: The line number or None
        :param column: The column number or None
        :param message: The error message
        :return: A dict
        """
        return {'level': level, 'code': code, 'line': line, 'column': column, 'message': message}

    def answer(self, content):
        """
        Parse a text

        :param content: The text to parse
        :return: A dict with the XML (None if parsing produced no tree) and a list of errors
        """

        return {'xml': None, 'errors': []}
