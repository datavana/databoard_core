import json

from databoard_core.flows import BaseWorkflow

class TripleWorkflow(BaseWorkflow):
    promptPrefix = 'triples'

    """
    Workflow to extract triples from a text

    Getting started:
    1. Prepare a folder with text files
    2. Create an empty output folder
    3. Apply the workflow as follows:

    inputfolder = 'inputfoldername'
    inputfiles =[os.path.join(inputfolder, f) for f in os.listdir(inputfolder)]

    wf = new TripleWorkflow()
    wf.filesToFiles(inputfiles, 'outputfolderpath'):
    """

    def __init__(self, settings={}):
        """
        Init workflow class

        Settings:
        - promptFolder: The folder name of prompt files (default 'prompts/default') or False if you provide prompts directly.
        - systemPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.
        - userPrompt: Depending on promptFolder setting, either the prompt file name or the prompt.

        :param settings: Default settings
        """
        default = {
            'systemPrompt': 'triples_default_system.txt',
            'userPrompt' : False
        }

        settings = {**default, **settings}
        super().__init__(settings)

    def extractPattern(self, value, cases, index, settings):
        """
        Extracts data from the result.

        :param value:
        :param cases:
        :param index:
        :param settings:
        :return:
        """
        triples = []
        lines = value.strip().split("\n")
        for line in lines:
            parts = line.split('" "')
            parts = [p.strip().strip('"') for p in parts]

            if len(parts) != 3:
                cases.at[index, self.statusColumn] = "Triple pattern not valid"

            else:
                triples.append({
                    "subject": parts[0],
                    "predicate": parts[1],
                    "object": parts[2]
                })

        cases.at[index, self.outputColumn] = json.dumps(triples)
        return cases

    def parseTriples(self, tripleColumn, caseColumn = None):
        """
        Helper to convert the JSON result to a list of triples

        :param tripleColumn:
        :param caseColumn:
        :return:
        """

        output = []
        for idx, rowValue in enumerate(tripleColumn):
            triples = json.loads(rowValue)

            if caseColumn is not None:
                caseNo = caseColumn[idx]
            else:
                caseNo = idx + 1
            for triple in triples:
                triple = {'case': caseNo, **triple}
                output.append(triple)

        return output