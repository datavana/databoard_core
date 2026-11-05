import databoard_core.clients as clients

# Error levels that make an input count as failed. Notices and warnings do not.
FAILING_LEVELS = ('error', 'fatal')


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
        - formalism: The Formalism of the Parser, e.g. 'ebnf' (required)
        - dialect: The Dialect of the input texts, e.g. 'dio' (required)
        - rules: Reserved for later use. It is passed to the parser client, but not processed yet.

        :param settings: Default settings
        """
        self.settings = settings

    def dataToData(self, input, settings={}):
        """
        Parse a string or a list of strings

        :param input: A string or a list of strings
        :param settings: See __init__(), overrides the default settings
        :raises ValueError: If formalism or dialect is missing or no parser exists for the pair
        :return: A list with one result per input in input order.
                 Each result is a dict with the keys 'xml', 'errors' and 'failed'.
                 'failed' is True if the errors contain an error or fatal entry.
                 The XML may be a partial tree if errors occurred.
        """
        settings = {**self.settings, **settings}
        input = [input] if isinstance(input, str) else input

        for name in ('formalism', 'dialect'):
            if not settings.get(name):
                raise ValueError(f"Missing option '{name}'")

        parserClass = clients.get_parser_class(settings['formalism'], settings['dialect'])
        client = parserClass()
        client.settings['rules'] = settings.get('rules')

        return [self.buildResult(client.answer(text)) for text in input]

    def buildResult(self, answer):
        """
        Add the failed flag to the answer of a parser client

        :param answer: A dict with the keys 'xml' and 'errors'
        :return: A dict with the keys 'xml', 'errors' and 'failed'
        """
        errors = answer.get('errors') or []
        failed = any(e.get('level') in FAILING_LEVELS for e in errors)
        return {'xml': answer.get('xml'), 'errors': errors, 'failed': failed}
