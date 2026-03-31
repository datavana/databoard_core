#%%
#
# Annotate text
#

# A rule book is an Excel or CSV file with the columns
# - category: An identifier of the category, used as value attribute of the XML elements
# - description: The definition of the category, one or two sentences.
# - example: An example text for the category
#
# The input file is an Excel or CSV file with content
# to be annotated in the column 'text'. Additional columns are
# allowed. The workflow classes support configuring other defaults
# for the column name or even working with folders, if required.
#
# The ouput file will be created as Excel or CSV file,
# however you name the file.
#
# See the user and system prompts used for annotations in the src/resources/prompts folder.
# The rules and each text are inserted into the prompts (note the placeholders in the prompts).
# The result is postprocessed and stored in the output file.
#
# You can inspect the generated prompts and results in the data/.cache folder of the root repository.
#
# The settings supported by the workflow classes are documented in the readme of this repository
# and in the method `BaseWorkflow::processData()` in  flows/flows.py.

import os
from databoard_core.flows import AnnoWorkflow

import dotenv
dotenv.load_dotenv("databoard_core/.env")

#%%

folder = "databoard_core/examples/data"

wf = AnnoWorkflow(rules = os.path.join(folder, "figures.xlsx"))

codings = wf.csvToCsv(
    os.path.join(folder, "movies.xlsx"),
    os.path.join(folder, "movies_figures.csv")
)

