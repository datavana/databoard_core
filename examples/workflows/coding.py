#%%
#
# Code cases
#

#
# A codebook is an Excel or CSV file with the columns
# - category: A number or word for the category
# - description: The definition of the category, one or two sentences.
# - example: An example text for the category
#
# The input file is an Excel or CSV file with content
# to be coded in the column 'text'. Additional columns are
# allowed. The workflow classes support configuring other defaults
# for the column name or even working with folders, if required.
#
# The ouput file will be created as Excel or CSV file,
# however you name the file.
#
# The examples use data from the folder examples/data and store results in this folder.
#
# See the user and system prompts used for coding in the src/resources/prompts folder.
# The rules and each text are inserted into the prompts (note the placeholders in the prompts).
# The result is postprocessed and stored in the output file.
#
# The settings supported by the workflow classes are documented in the readme of this repository
# and in the method `BaseWorkflow::processData()` in  flows/flows.py.

import os
from databoard_core.flows import CodingWorkflow

import dotenv
dotenv.load_dotenv("databoard_core/.env")

#%% Use a codebook to categorize each text into one category

folder = "databoard_core/examples/data"

wf = CodingWorkflow(rules = os.path.join(folder, "genres.xlsx"))

codings = wf.csvToCsv(
    os.path.join(folder, "movies.xlsx"),
    os.path.join(folder, "movies_genres.csv")
)

#%% Allow each text to be assigned to all categories

folder = "databoard_core/examples/data"

wf = CodingWorkflow(rules = os.path.join(folder, "genres.xlsx"), mode = 'multi')

codings = wf.csvToCsv(
    os.path.join(folder, "movies.xlsx"),
    os.path.join(folder, "movies_genres.csv")
)

#%% You see the <anno> tags?

codings['llm_result']