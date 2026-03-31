#%%
#
# Summaries reduce text to simplified paraphrases or abstract words
# The summary workflow can be used for qualitative content analysis procedures.
#
# a) The multi mode determines all text segments matching selection criteria defined by the rule book.
#    The text segments are then recuced to one to three words.
#    This resembles open coding procedures as developed in grounded theory.
# b) The single mode summarizes and thus shortens the text.
#    You can, for example, use this for topic modeling by instructing the LLM to reduce the text to one topic.
#
# The single mode summary workflow skips any postprocessing.
# Therefore, it allows you to provide any user and system prompt
# and retrieve the direct answer of the LLM.
#
# The input file is an Excel or CSV file containing content to be coded in the 'text' column.
# Additional columns are allowed. The workflow classes support configuring other defaults
# for the column name or even working with folders, if required.
#
# The ouput file will be created as Excel or CSV file,
# however you name the file.
#
# The settings supported by the workflow classes are documented in the readme of this repository
# and in the method `BaseWorkflow::processData()` in  flows/flows.py.

from databoard_core.flows import SummaryWorkflow

import os
import dotenv
dotenv.load_dotenv("databoard_core/.env")


#%% Summarize by reducing the text to the topic

folder = "databoard_core/examples/data"

wf = SummaryWorkflow()

results = wf.csvToCsv(
    os.path.join(folder, "movies.xlsx"),
    os.path.join(folder, "movies_topics.csv"),
    {
        'systemPrompt': 'Output one word describing the topic of each movie.',
        'userPrompt' : '{{text}}',
        'promptFolder': False
    }
)

#%% Summarize according to predefined selection criteria

folder = "databoard_core/examples/data"

wf = SummaryWorkflow(
    rules = [
        {'category': 'topic', 'description': 'Text describing the topic of the movies'},
        {'category': 'figures', 'description': 'Text describing the figures of the movies'},
        {'category': 'plot', 'description': 'Text describing the plot of the movies'},
    ],
    mode = 'multi'
)

codings = wf.csvToCsv(
    os.path.join(folder, "movies.xlsx"),
    os.path.join(folder, "movies_summaries.csv")
)
