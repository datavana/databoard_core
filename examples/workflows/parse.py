#%%
#
# Parse texts that are written in a Dialect, for example inscriptions
# in the DIO notation, and get XML.
#
# The Formalism and the Dialect select the parser, see the README.
# Note: Parsing happens locally. No LLM and no access token is needed.

from databoard_core.flows import ParseWorkflow

#%% Parse a list of texts

texts = [
    "anno domini 1455",
    "anno domini [1455-1500]",
]

wf = ParseWorkflow()

results = wf.dataToData(texts, {
    'formalism': 'ebnf',
    'dialect': 'dio'
})

#%% There is one result per text, in the order of the input

for text, result in zip(texts, results):
    print(text)
    print("  failed:", result['failed'])
    print("  xml:", result['xml'])
    for error in result['errors']:
        print("  ", error['level'], error['line'], error['column'], error['message'])

#%% A combination without a parser is rejected

try:
    wf.dataToData(texts, {'formalism': 'ebnf', 'dialect': 'isodate'})
except ValueError as e:
    print(e)
