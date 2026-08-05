import os
import json
import re
import pandas as pd
from tqdm import tqdm
from pathlib import Path

import databoard_core.utils as utils
import databoard_core.clients as llm

# Provide the UNI-GPT access token and server URL
# in the environment variables:
# - Create .env file with the access token and URL,
#   see .env.default for a blueprint
# - Install python-dotenv:
#   pip install python-dotenv

#import dotenv
#dotenv.load_dotenv("databoard_core/.env")

class BaseWorkflow:
    """
    Base class for workflows.
    Don't use this class directly,
    use one of the derived workflow classes.

    Settings:
    - promptFolder
    - cacheFolder
    - logFolder

    :param settings Default settings
    """
    def __init__(self, settings = {}):

        defaultPromptFolder = Path(__file__).parent.parent / 'resources' / 'prompts'

        default = {
            'promptFolder': defaultPromptFolder,
            'cacheFolder' : 'data/.cache',
            'logFolder': 'data/.logs',
        }

        self.outputColumn = None
        self.multinomial = False
        self.rules_df = None

        self.settings = {**default, **settings}
        self.client = None

    def getClient(self, settings):
        """
        Instantiate a LLM client.

        By default, a UniGptClient() is created.
        You can provide an alternative client in the 'client' key of the settings.

        Settings:
        - client: An alternative client derived from LLmClient()

        :param settings:
        :return: A LLM client
        """
        if self.client is None:
            self.client = settings.get('client', None)

        if self.client is None:
            self.client = llm.UniGptClient()

        # Raw answer setting
        rawAnswer = settings.get('rawAnswer', None)
        if rawAnswer is not None:
            self.client.settings['rawAnswer'] = rawAnswer

        # Raw error setting
        rawError = settings.get('rawError', rawAnswer)
        if rawError is not None:
            self.client.settings['rawError'] = rawError

        # Client settings
        model = settings.get('model', None)
        if model is not None:
            self.client.settings['gpt_modelname'] = model

        temperature = settings.get('temperature', None)
        self.client.settings['gpt_temperature'] = temperature

        # Alternative: local ollama
        # self.client = llm.OllamaClient()

        return self.client

    def getPrompt(self, content, data = {}):
        """
        Generate a prompt by replacing placeholders with data.

        Placeholders are strings in double curly brackets that will be replaced by
        corresponding data values.

        Example content of a prompt file:
        Summarize in six words: {{text}}

        :param content: The prompt template text.
                        Set to None for generating a prompt directly from the data.
        :param data: A dict with keys matching the placeholders to be replaced by the values.
                     If a prompt is to be generated without a file, provide the prompt
                     value in the 'text' key.
        :return: A string with data instead of placeholders
        """

        if content is not None:
            for key, value in data.items():
                # Curly brackets need to be doubled for escaping purposes. The outer bracket ist the format string bracket.
                content = content.replace(f'{{{{{key}}}}}', str(value))
        else:
            content = data.get('text')

        return content

    def log(self, message, scope = None):
        print(message)

        logFile = self.settings.get('logFile')
        if logFile is None:
            logFolder = self.settings.get('logFolder')
            logFile = scope + '.log' if scope is not None else 'default.log'
            logFile = os.path.join(logFolder, logFile) if logFile is not None else None

        if logFile is not None:
            os.makedirs(os.path.dirname(logFile), exist_ok=True)
            try:
                with open(logFile, 'a') as file:
                    file.write(f"{message}\n")
            except Exception as e:
                print(f"Failed to write to log file: {e}")

    def writeToCache(self, path, name, value):
        """
        Write a value to the cache

        :param path: The path within the cache (i.e. the folder name)
        :param name:  The cache key (i.e. the file name)
        :param value:  The cache value (i.e. the file content)
        :return:
        """
        cacheFolder = self.settings.get('cacheFolder')
        if cacheFolder is not None:
            cacheFile = os.path.join(cacheFolder, path, name)
            os.makedirs(os.path.dirname(cacheFile), exist_ok=True)
            try:
                if not isinstance(value, str):
                    value = json.dumps(value)

                with open(cacheFile, 'w', encoding="utf-8") as file:
                    file.write(value)
            except Exception as e:
                print(f"Failed to write to cache file {name}: {e}")

    def getFromCache(self, path, name, default = None):
        cacheFolder = self.settings.get('cacheFolder')
        if cacheFolder is not None:
            cacheFile = os.path.join(cacheFolder, path, name)
            try:
                with open(cacheFile, 'r', encoding="utf-8") as file:
                    return file.read()
            except FileNotFoundError:
                return default
            except Exception as e:
                print(f"Failed to read from cache file: {e}")

        return default

    def prepareSettings(self, settings):
        """
        Hook to overwrite in a workflow if the settings need to be changed before
        the data is procesed

        :param settings:
        :return:
        """

        self.outputColumn = settings.get('outputCol', 'llm_result')
        self.statusColumn = settings.get('statusCol', 'llm_status')
        self.tokensColumn = settings.get('tokensCol', 'llm_tokens')

        return settings

    def prepareData(self, inputText):
        return {
            'text': inputText
        }

    def extractPattern(self, value, cases, index, settings):
        """
        Extracts data from the result and puts it into the data frame.

        :param value:
        :param cases:
        :param index:
        :param settings:
        :return:
        """
        value = value.strip()
        rawAnswer = settings.get('rawAnswer', False)

        # Extract multinomial result and add category by category
        if self.multinomial and self.rules_df is not None and not rawAnswer:
            for catIndex, catRow in self.rules_df.iterrows():
                category = catRow['category'].strip()
                columnName = category.lower().replace(' ', '_').replace('.', '-')
                columnName = f'llm_result_{columnName}'

                if columnName not in cases.columns:
                    cases[columnName] = None

                pattern = r'^[ -]*' + re.escape(category) + r'[: ]*(.*)$'
                match = re.search(pattern, value, re.MULTILINE |re.IGNORECASE)
                if match:
                    cases.at[index, columnName] = match.group(1).strip()

        # Directly save the result to the data frame
        else:
            cases.at[index, self.outputColumn] = value

        return cases

    def reportResults(self, cases):
        pass

    def processData(self, input, output, settings = {}):
        """
        Process the data

        Adds the column 'llm_result' with the coding result.
        Errors will be logged in the column 'llm_status'.

        The prompt file content may contain the placeholders {{text}} and {{rules}}.
        The {{text}} placeholder is replaced with the input data.
        The {{rules}} placeholder is replaced with the result of load_rules().

        Optional settings:
        - inputCol Name of the column in the input data containing the text to process. Defaults to 'text'.
                   Either set inputCol or fileCol to a string value and the other to None.
        - fileCol Name of the column in the input data containing a file name to load. Defaults to None.
                  Either set inputCol or fileCol to a string value and the other to None.
        - outputCol Name of the column to store the result. Defaults to 'llm_result'.
        - outputFolder Name of the folder where the result text should be stored or None.
                       If None, no files will be generated.
                       Defaults to None.
        - statusCol Name of the column to log errors. Defaults to 'llm_status'.
        - promptFolder Folder that contains the prompt files. Defaults to 'prompts/default'.
                       Set to False if you provide the prompts as text
                       in the systemPrompt and userPrompt parameters.
        - systemPrompt: A file name to the system prompt file. Defaults to 'coding_system.txt'.
                        If promptFolder is False, the prompt text.
        - userPrompt: A file name to the user prompt file. Defaults to 'coding_user.txt'.
                      To feed the text into the model without a prompt file, set userPrompt to False.
                      If promptFolder is False, provide the prompt text.
        - useCache: Whether to load answers from the cache if they already were retrieved early.
                    A cache entry is identified by a hash generated from
                    the LLM configuration (server name, model name), the system prompt and the user prompt.
                    Possible values are:
                    False for skipping the cache.
                    True for querying the LLM if no cache entry exits.
                    'Only' for only processing values that are in the cache, without any new queries to the LLM.
        - rawAnswer: Whether to return the answer message or all raw values of the model response. Defaults to False.
        - rawError: Whether to return raw error messages or to map them to short status messages. Defaults to False.
        - model: The model name to use. Defaults to the model defined in the LLM client.
        - temperature: The temperature to use. Defaults to the temperature defined in the LLM client.
        :param input: Path to a csv or excel file containing cases. Or a pandas data frame.
                      By default, provide input text in the 'text' column, see the inputCol setting.
        :param output: Path to the output csv file. Set to None for not writing the result to a table (csv, Excel) file.
        :param settings
        :return: A pandas data frame with the new columns 'llm_result' and 'llm_status'
        """

        # Init settings
        settings = self.prepareSettings({**self.settings, **settings})

        inputColumn = settings.get('inputCol', 'text')
        fileColumn = settings.get('fileCol', None)
        caseColumn = settings.get('caseCol', None)
        outputFolder = settings.get('outputFolder', None)
        useCache = settings.get('useCache', True)

        # Init prompts
        promptFolder = settings.get('promptFolder', self.settings.get('promptFolder'))
        if promptFolder == False:
            systemPromptTemplate = settings.get('systemPrompt', self.settings.get('systemPrompt'))
            userPromptTemplate = settings.get('userPrompt', self.settings.get('userPrompt'))
        else:
            systemPromptFile = settings.get('systemPrompt', self.settings.get('systemPrompt'))
            systemPromptFile = os.path.join(str(promptFolder), systemPromptFile)
            with open(systemPromptFile, 'r') as file:
                systemPromptTemplate = file.read()

            userPromptFile = settings.get('userPrompt', self.settings.get('userPrompt'))
            userPromptTemplate = None
            if userPromptFile != False:
                userPromptFile = os.path.join(str(promptFolder), userPromptFile)
                with open(userPromptFile, 'r') as file:
                    userPromptTemplate = file.read()

        # Prepare inputs
        if isinstance(input, str):
            cases = utils.read_table(input)
        elif isinstance(input, pd.DataFrame):
            cases = input
        else:
            raise ValueError("Unsupported input format")

        # Init client
        myLlmClient = self.getClient(settings)
        modelKey = myLlmClient.getCacheKey()
        totalCount = 0

        for index, row in tqdm(cases.iterrows(), total=len(cases), desc="Processing cases"):

            caseNumber = str(index + 1).zfill(5) if caseColumn is None else row[caseColumn]
            outputFilename = f"{caseNumber}.txt" if not caseNumber.endswith(".txt") else caseNumber

            if fileColumn is not None:
                with open(row[fileColumn], 'r', encoding='utf-8') as file:
                    inputText = file.read()
            else:
                inputText = row[inputColumn]

            data = self.prepareData(inputText)
            systemPrompt = self.getPrompt(systemPromptTemplate, data)
            userPrompt = self.getPrompt(userPromptTemplate, data)

            try:
                cacheKey = utils.hash(modelKey, systemPrompt, userPrompt)

                loadCache = useCache != False
                cacheValue = self.getFromCache(cacheKey, 'answer.txt') if loadCache else None
                queryLlm = (useCache != 'only') and cacheValue is None

                if queryLlm:
                    # Log query
                    self.writeToCache(cacheKey,'system.txt', systemPrompt)
                    self.writeToCache(cacheKey, 'user.txt', userPrompt)

                    # Query the LLM
                    answer = myLlmClient.answer(userPrompt, systemPrompt)

                    if answer['status'] is not None:
                        self.log(answer)
                        raise ValueError(str(answer['status']))

                    if answer['text'] == "":
                        self.log(answer)
                        raise ValueError("The answer is empty.")

                    # Log response
                    self.writeToCache(cacheKey, 'answer.txt', answer)

                elif cacheValue is not None:
                    answer = json.loads(cacheValue)
                else:
                    continue

                # Save result to file
                if outputFolder is not None:
                    answerFilePath = os.path.join(outputFolder, outputFilename)
                    with open(answerFilePath, 'w+', encoding='utf-8') as answerFile:
                        answerFile.write(answer['text'])

                # Add results to data frame
                cases = self.extractPattern(answer['text'], cases, index, settings)

                # Add token count
                cases.at[index, self.tokensColumn] = answer.get('tokens')
                totalCount += 1

            except Exception as e:
                self.log(f"Error processing case {caseNumber}: {e}")
                cases.at[index, self.outputColumn] = None
                cases.at[index, self.statusColumn] = str(e)

        # Save result table
        if output is not None:
            utils.write_table(cases, output)

        # Report
        self.reportResults(cases)

        # Report case count
        print("Total processed cases:", totalCount)

        # Report token count
        if self.tokensColumn in cases.columns:
            total_sum = cases[self.tokensColumn].sum()
            print("Total processed tokens:", total_sum)

        # Return data frame
        return cases

    def dataToData(self, input, settings={}):
        """
        Process a string and return the result

        This is just a wrapper for processData(),
        see processData() for a full explanation.

        :param input: A list of input texts
        :param settings
        :return: A pandas data frame with the columns 'text', 'llm_result' and 'llm_status'
        """
        input = [input] if isinstance(input, str) else input
        input = pd.DataFrame({'text': input})
        return self.processData(input, None, settings)

    def csvToCsv(self, input_file, output_file, settings={}):
        """
        Process a csv / excel file and save the result to a csv / excel file

        This is just a wrapper for processData(),
        see processData() for a full explanation.

        :param input: Path to a csv or excel file containing cases.
                      By default, provide input text in the 'text' column, see the inputCol setting.
        :param output_file: Path to the output csv file.
        :param settings
        :return: A pandas data frame with the new columns 'llm_result' and 'llm_status'
        """
        return self.processData(input_file, output_file, settings)

    def csvToFiles(self, input_file, output_folder, settings = {}):
        """
        Process a csv / excel file and save the result to files

        This is just a wrapper for processData() which sets the output_file to None
        and instead passed the output_folder in the settings.
        See processData() for a full explanation.

        :param input_file: Input csv file path.
        :param output_folder: Output folder path.
        :param settings: Settings passed to the processData() method.
        :return: A pandas data frame with the new columns 'llm_result' and 'llm_status'
        """

        settings['outputFolder'] = output_folder
        return self.processData(input_file,None, settings)

    def filesToFiles(self, input_files, output_folder, settings={}):
        """
        Process input files and save the result to an output folder

        This is just a wrapper for processData() which converts the input file list
        to a data frame and sets the outputFolder setting.
        See processData() for a full explanation.

        :param input_files: A list of file names for text files
        :param output_folder: A folder to store the results
        :param settings: Passed to processData()
        :return: A pandas data frame
        """

        input = pd.DataFrame({
            'case': [os.path.basename(file) for file in input_files],
            'inputfile': input_files
        })

        settings['outputFolder'] = output_folder
        settings['fileCol'] = 'inputfile'
        settings['caseCol'] = 'case'
        return self.processData(input, None, settings)

    def filesToCsv(self, input_files, output_file, settings={}):
        """
        Process input files and save the result to a csv / excel file

        This is just a wrapper for processData() which converts the input file list
        to a data frame. See processData() for a full explanation.

        :param input_files: A list of file names for text files
        :param output_file: A csv or excel file name to store the results.
        :param settings: Passed to processData()
        :return: A pandas data frame
        """

        input = pd.DataFrame({
            'case': [os.path.basename(file) for file in input_files],
            'inputfile': input_files
        })

        settings['fileCol'] = 'inputfile'
        settings['caseCol'] = 'case'
        return self.processData(input, output_file, settings)
