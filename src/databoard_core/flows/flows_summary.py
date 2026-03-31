import pandas as pd

from databoard_core import utils
from databoard_core.flows import BaseWorkflow

class SummaryWorkflow(BaseWorkflow):

    promptPrefix = 'summary'

    """
    Workflow to summarize text

    Getting started:
    1. Prepare a folder with text files
    2. Create an empty output folder
    3. Apply the workflow as follows:

    inputfolder = 'inputfoldername'
    inputfiles =[os.path.join(inputfolder, f) for f in os.listdir(inputfolder)]

    wf = new SummaryWorkflow()
    wf.filesToFiles(inputfiles, 'outputfolderpath'):
    
    The mode parameter determines pre- and postprocessing of the data.
    - By default, as single summary is returned
      The default prompts are summary_single_system.txt and summary_single_user.txt.    
    - In multi summary mode, resulting text for each category defined in the rules is returned in the columns. Set mode to "multi".
      The default prompts for the multi summary mode are summary_multi_system.txt and summary_multi_user.txt.    
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
                      with the columns 'category', 'description', and optionally 'example'.
                      Alternatively, a list of dicts with the same keys.
                      Set to None if you don't want to use a codebook
                      and provide all information in the prompt.
        :param mode: The coding mode.
                     - single (default): Only one answer is returned.
                     - multi: One answer for each category is returned.
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

        :param input: The path to a file containing the columns 'category', 'description', and optionally 'example'.
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
            rule = f"- {row['category']}: {row['description']}"
            if ('example' in row) and pd.notna(row['example']):
                rule += f" ({row['example']})"
            rules += rule + "\n"

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
                'systemPrompt': 'summary_multi_system.txt',
                'userPrompt': 'summary_multi_user.txt'
            }
        else:
            default = {
                'systemPrompt': 'summary_single_system.txt',
                'userPrompt': 'summary_single_user.txt'
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
        """
        Count the first 30 characters of the resulting texts

        :param cases:
        :return:
        """
        if self.reportCodings:

            # Text in multiple columns
            if (self.mode == 'multi') and (len(self.outputColumns) > 0):
                result = cases.melt(
                    value_vars=self.outputColumns,
                    var_name='Category',
                    value_name='Value'
                ).dropna(subset=['Value'])

                result['Value'] = result['Value'].str.split(',')
                result = result.explode('Value')
                result['Value'] = result['Value'].str.strip().str.slice(0,30)
                result = result[result['Value'].astype(str).str.strip() != ""]
                groups = ['Category', 'Value']

            # Single column
            elif (self.outputColumn is not None) and (self.outputColumn in cases.columns):
                result = cases[[self.outputColumn]].copy()
                result[self.outputColumn] = result[self.outputColumn].str.strip().str.slice(0,30)
                groups = [self.outputColumn]

            counts = result.groupby(groups).size().reset_index(name='Count')
            counts = counts.sort_values(by='Count', ascending=False)

            print(counts)

