import pandas as pd

from databoard_core import utils
import databoard_core.clients as clients
from .flows import BaseWorkflow

# Error levels that make an input count as failed. Notices and warnings do not.
FAILING_LEVELS = ('error', 'fatal')


class ParseWorkflow(BaseWorkflow):
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
        super().__init__(settings)

    def processData(self, input, output=None, settings={}):
        """
        Parse the text values in a data frame, string, or list of strings.

        :param input: A data frame with a 'text' column, a string, or a list of strings
        :param output: Optional path to write the parse results as a table
        :param settings: See __init__(), overrides the default settings
        :raises ValueError: If formalism or dialect is missing or no parser exists for the pair
        :return: A list with one result per input in input order.
                 Each result is a dict with the keys 'xml', 'errors' and 'failed'.
                 'failed' is True if the errors contain an error or fatal entry.
                 The XML may be a partial tree if errors occurred.
        """
        settings = {**self.settings, **settings}

        if isinstance(input, pd.DataFrame):
            if 'text' not in input.columns:
                raise ValueError("Input data frame must contain a 'text' column")
            texts = input['text'].tolist()
        elif isinstance(input, str):
            texts = [input]
        elif isinstance(input, list):
            texts = input
        else:
            raise ValueError("Unsupported input format")

        for name in ('formalism', 'dialect'):
            if not settings.get(name):
                raise ValueError(f"Missing option '{name}'")

        parserClass = clients.get_parser_class(settings['formalism'], settings['dialect'])
        client = parserClass()
        client.settings.update(settings)

        results = [self.buildResult(client.answer(text)) for text in texts]

        if output is not None:
            utils.write_table(pd.DataFrame(results), output)

        return results

    def buildResult(self, answer):
        """
        Add the failed flag to the answer of a parser client

        :param answer: A dict with the keys 'xml' and 'errors'
        :return: A dict with the keys 'xml', 'errors' and 'failed'
        """
        errors = answer.get('errors') or []
        failed = any(e.get('level') in FAILING_LEVELS for e in errors)
        return {'xml': answer.get('xml'), 'errors': errors, 'failed': failed}
