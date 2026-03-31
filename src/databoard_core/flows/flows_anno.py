import pandas as pd

from databoard_core import utils
from databoard_core.flows import BaseWorkflow

class AnnoWorkflow (BaseWorkflow):

    promptPrefix = 'anno'

    """
    Workflow to annotate text

    Getting started:
    1. Prepare the rules in a csv file with the columns 'category', 'description', 'example'.
    2. Prepare a csv file with the text to be coded in the 'text' column.
    3. Apply the workflow as follows:

    wf = new AnnoWorkflow(rules = 'path_to_rulebook.csv')
    codings = wf.csvToCsv('path_to_input.csv', 'path_to_result.csv'):
    
    The following settings are supported, in addition to the BaseWorkflow settings:
    - promptFolder: The folder name of prompt files (default 'prompts/default') or False if you provide prompts directly.
    - systemPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.
    - userPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.
    
    :param rules: Path to a csv file containing the rulebook,
                  with the columns 'category', 'description' and 'example',
                  see the load_rules() method for further explanation.
                  Alternatively, a list of dicts with the same keys.
    :param settings Default settings
    """
    def __init__(self, rules = None, settings={}):
        """
        Init workflow class

        Settings:
        - promptFolder: The folder name of prompt files (default 'prompts') or False if you provide prompts directly.
        - systemPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.
        - userPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.

        :param rules: Path to a csv file containing the codebook,
                       with the columns 'category', 'description' and 'example'.
                       Alternatively, a list of dicts with the same keys.
                       Set to None if you don't want to use a codebook
                       and provide all information in the prompt.
        :param settings: Default settings
        """

        self.rules = rules

        default = {
            'rules': rules
        }

        settings = {**default, **settings}
        super().__init__(settings)

    def load_rules(self, input):
        """
        Load the annotation rules from a csv or xlsx file and
        convert it to a format for prompting.

        :param input: The path to a file containing the columns:
                      - description: The annotation rule (e.g. "Persons, whether identified by a name or a pronoun.")
                      - example: Example of an annotated text segment (e.g. "Anna")
                      - category: The resulting value attribute (e.g. "person")
                      Alternatively, a list of dicts with the same keys.
        :return: A tuple containing the prompt version in the first element and the data frame in the second.
        """

        if isinstance(input, str):
            df = utils.read_table(input)
        elif isinstance(input, list):
            df = pd.DataFrame(input)
        else:
            raise ValueError('Unsupported input value')

        # check columns
        required_columns = {'category', 'description', 'example'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Data must contain {required_columns}")

        # reformat to strings
        rules = "\n".join(
            f"- **Rule**: {row['description']}\n"
            f"  - **Examples**: \"{row['example']}\"\n"
            f"  - **Attribute value**: \"{row['category']}\"\n"
            for _, row in df.iterrows()
        )

        return (rules, df)

    def prepareSettings(self, settings):
        """
        Decide on the default prompts

        :param settings:
        :return:
        """

        settings = super().prepareSettings(settings)

        default = {
            'systemPrompt': 'anno_default_system.txt',
            'userPrompt': 'anno_default_user.txt'
        }

        rules = settings.get('rules', None)
        if rules is not None:
            self.rules = self.load_rules(rules)
        else:
            self.rules = None

        return {**default, **settings}

    def prepareData(self, inputText):
        return {
            'text': inputText,
            'rules': self.rules
        }
