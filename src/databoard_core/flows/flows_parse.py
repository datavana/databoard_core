import databoard_core.clients as clients


class ParseWorkflow:
    """
    Workflow to parse texts written in a Dialect and get XML

    In contrast to the LLM workflows, no prompts, cache or model settings apply.

    Getting started:

    wf = ParseWorkflow()
    results = wf.dataToData(['text one', 'text two'], {'formalism': 'ebnf', 'dialect': 'dio'})
    """

    def __init__(self, settings={}):
        """
        Init workflow class

        Settings:
        - formalism: The Formalism of the Parser, e.g. 'ebnf'
        - dialect: The Dialect of the input texts, e.g. 'dio'

        :param settings: Default settings
        """
        self.settings = settings

    def dataToData(self, input, settings={}):
        """
        Parse a string or a list of strings

        :param input: A string or a list of strings
        :param settings: See __init__(), overrides the default settings
        :return: A list with one result per input in input order.
                 Each result is a dict with the keys 'xml' and 'errors'.
        """
        settings = {**self.settings, **settings}
        input = [input] if isinstance(input, str) else input

        parserClass = clients.get_parser_class(settings.get('formalism'), settings.get('dialect'))
        client = parserClass()

        return [client.answer(text) for text in input]
