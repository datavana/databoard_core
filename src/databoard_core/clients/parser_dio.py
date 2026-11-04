from databoard_core.clients.parser import ParserClient


class DioParserClient(ParserClient):
    """
    Parser client for the DIO (Deutsche Inschriften Online) Dialect, EBNF Formalism.
    """

    def answer(self, content):
        try:
            # Import lazily: loading the generated parser is expensive and requires DHParser
            from databoard_core.resources.parser import dioParser

            tree, messages = dioParser.compile_snippet(content)
            xml = tree.as_xml() if tree is not None else None
            errors = [self.convertError(m) for m in messages]
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
        from DHParser.error import NOTICE, WARNING, ERROR, FATAL

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
