#%%
#
# Extract triples from text.
# According to the resource description framework (RDF) a triple
# consists of subject, predicate and object.

from databoard_core.flows import TripleWorkflow

import os
import pandas as pd
import json
import dotenv
dotenv.load_dotenv("databoard_core/.env")

#%%

folder = "databoard_core/examples/data"

wf = TripleWorkflow()

results = wf.csvToCsv(
    os.path.join(folder, "movies.xlsx"),
    os.path.join(folder, "movies_triples.csv")
)

#%% Parse the triples

triples = results[['llm_result']]
triples["llm_result"] = triples["llm_result"].apply(
    lambda x: json.loads(x) if pd.notna(x) else []
)
triples = triples.explode("llm_result", ignore_index=True)
triples = pd.json_normalize(triples["llm_result"])

print(triples)
