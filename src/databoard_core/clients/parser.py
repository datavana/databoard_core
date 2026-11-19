from importlib import import_module

from databoard_core.clients.client import Client


# A formalism selects the transform module layout; the dialect selects its module.
_FORMALISM_TRANSFORM_MODULES = {
    'ebnf': 'databoard_core.resources.parser.{dialect}.{dialect}Transform',
}


class ParserClient(Client):
    """
    Base class for parser clients.

    A parser client turns a text written in one Dialect into XML.
    """
    def __init__(self):
        super().__init__()

    def getClient(self):
        if self.client is None:
            formalism = self.settings.get('formalism')
            if not isinstance(formalism, str):
                raise ValueError(f"Unsupported parser formalism '{formalism}'")

            module_template = _FORMALISM_TRANSFORM_MODULES.get(formalism)
            if module_template is None:
                raise ValueError(f"Unsupported parser formalism '{formalism}'")

            dialect = self.settings.get('dialect')
            if not isinstance(dialect, str) or not dialect.isidentifier():
                raise ValueError(f"Invalid parser dialect '{dialect}'")

            module_name = module_template.format(dialect=dialect)
            self.client = import_module(module_name)
        return self.client

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

        try:
            xml, messages = self.getClient().transform(content)
            errors = [self.convertError(message) for message in messages]
        except Exception as e:
            xml = None
            errors = [self.makeError('fatal', None, None, None, str(e))]

        return {'xml': xml, 'errors': errors}

    def convertError(self, message):
        """
        Convert a DHParser error to an error entry

        :param message: A DHParser Error object
        :return: A dict, see ParserClient.makeError()
        """
        from DHParser.error import WARNING, ERROR, FATAL

        if message.code >= FATAL:
            level = 'fatal'
        elif message.code >= ERROR:
            level = 'error'
        elif message.code >= WARNING:
            level = 'warning'
        else:
            level = 'notice'

        line = message.line if message.line >= 0 else None
        column = message.column if message.column >= 0 else None
        return self.makeError(level, message.code, line, column, str(message.message))
