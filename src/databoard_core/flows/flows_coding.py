import pandas as pd

from databoard_core import utils
from databoard_core.flows import BaseWorkflow

class CodingWorkflow (BaseWorkflow):

    promptPrefix = 'coding'

    """
    Workflow to code cases

    Getting started:
    1. Prepare a codebook in a csv file with the columns 'category', 'description', 'example'.
    2. Prepare a csv file with the text to be coded in the 'text' column.
    3. Apply the workflow as follows:

    wf = new CodingWorkflow(rules = 'path_to_codebook.csv')
    codings = wf.csvToCsv('path_to_input.csv', 'path_to_result.csv'):

    The mode parameter determines pre- and postprocessing of the data.
    - By default, the best matching category is returned. Set mode to "single".
      The default prompts are coding_single_system.txt and coding_single_user.txt.
    - To get a result for each category instead of the best matching category, set mode to "multi".
      The default prompts for the multinomial workflow are coding_multi_system.txt and coding_multi_user.txt.
    """
    def __init__(self, rules = None, mode = "single", settings={}):
        """
        Init workflow class

        Settings:
        - reportCodings Whether to output a summary table.
        - promptFolder: The folder name of prompt files (default 'prompts/default') or False if you provide prompts directly.
        - systemPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.
        - userPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.

        :param rules: Path to a csv file containing the codebook,
                      with the columns 'category', 'description' and 'example'.
                      Alternatively, a list of dicts with the same keys.
                      Set to None if you don't want to use a codebook
                      and provide all information in the prompt.
        :param mode: The coding mode.
                     - single (default): Only the best matching category is returned.
                     - multi: A result for each category is returned.
        :param settings: Default settings
        """

        self.mode = mode
        self.rules = rules

        default = {
            'mode' : mode,
            'rules': rules
        }

        settings = {**default, **settings}
        super().__init__(settings)


    def load_rules(self, input):
        """
        Load the codebook from a csv or xlsx file and
        convert it to a format for prompting.

        :param input: The path to a file containing the columns 'category', 'description' and 'example'.
                      Alternatively, a list of dicts with the same keys.
        :return: A tuple containing the prompt version in the first element and the data frame in the second.
        """

        if isinstance(input, str):
            df = utils.read_table(input)
        elif isinstance(input, list):
            df = pd.DataFrame(input)
        else:
            raise ValueError('Unsupported input value')

        # Check columns
        required_columns = {'category', 'description'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Data must contain {required_columns}")

        # Format rules
        # TODO: Implement pattern parsing for rules
        rules = ""
        for idx, row in df.iterrows():
            rule = f"- **Category**: {row['category']}\n"
            rule += f"  - **Description**: {row['description']}\n"
            if ('example' in row) and pd.notna(row['example']):
                rule += f"  - **Example**: ({row['example']})\n"
            rules += rule

        return (rules, df)

    def prepareSettings(self, settings):
        """
        Decide on the default prompts

        :param settings:
        :return:
        """

        settings = super().prepareSettings(settings)
        self.mode = settings.get('mode', 'single')
        self.reportCodings = settings.get('reportCodings', True)

        if self.mode == 'multi':
            default = {
                'systemPrompt': 'coding_multi_system.txt',
                'userPrompt': 'coding_multi_user.txt'
            }
        else:
            default = {
                'systemPrompt': 'coding_single_system.txt',
                'userPrompt': 'coding_single_user.txt'
            }

        self.outputColumns = []
        self.multinomial = False
        self.rules = None

        rules = settings.get('rules', None)
        if rules is not None:
            self.rules, self.rules_df = self.load_rules(rules)

            if self.mode != 'single':
                self.multinomial = True
                for catIndex, catRow in self.rules_df.iterrows():
                    columnName = utils.clean_name(catRow['category'])
                    columnName = f'llm_result_{columnName}'
                    self.outputColumns.append(columnName)

        return {**default, **settings}

    def prepareData(self, inputText):
        return {
            'text': inputText,
            'rules': self.rules
        }

    def reportResults(self, cases):
        if self.reportCodings:

            # Codes in multiple columns
            if (self.mode == 'multi') and (len(self.outputColumns) > 0):
                counts = cases.melt(value_vars=self.outputColumns, var_name='Category', value_name='Value')
                counts = pd.pivot_table(counts, index='Category', columns='Value', aggfunc='size', fill_value=0)
                counts['Total'] = counts.sum(axis=1)
                print(counts)

            # Single column
            elif (self.outputColumn is not None) and (self.outputColumn in cases.columns):
                print(cases[self.outputColumn].value_counts())
