# Databoard Core

The databoard project develops tools and workflows for
working with machine learning models such as LLMs and parsers.

## Folder structure

Don't be frightened by the deeply nested folder structure.
It follows the standard Python package structure and 
makes the core classes available to the databoard server and to your local scripts.

The core repository is a Python package:

- src/databoard_core/clients contains the client classes to interact with LLMs and parsers.
- src/databoard_core/flow contains the workflow classes that provide wrappers to feed data into
  an LLM and convert the output to the desired target format.
- src/databoard_core/resources/prompts contains the default prompting templates to generate LLM prompts.
- src/databoard_core/utils contains utility functions.

## Branches

The main branch contains a slim version without local models.
For deploying the databoard server, use the main branch.

The localmodels branch contains clients for running local models (e.g. ollama).
Thus, it requires CUDA and other large dependencies.
We are planning to split local model clients into a separate repository.

## Installation

For local development, you create a `databoard` working directory
and clone the `databoard_core` repository into this directory as a subfolder. 

Then you create a Python venv within the working directory 
and install the core repository as a Python module in edit mode.
This makes the core classes available to your local scripts.

```
pip install -e ./databoard_core
pip install -r ./databoard_core/requirements.txt
```

Copy the .env.default file to .env and set the environment variables as needed.

## Usage

After installing the package, see the `examples` folder for example scripts that use the core classes.

- examples/workflows: Use the datavana workflow classes to feed data into an LLM, with pre- and processing steps.
  The parse.py example uses the ParseWorkflow to parse texts into XML, without an LLM.
- examples/clients: Direct API requests to LLMs.
- examples/embeddings: Use Qdrant to generate and query vector representations of text data (experimental).


# Base components

The `BaseWorkflow()` class implements the following input-output-functions
making your life easy:

- dataToData: String input, string output.
- csvToFiles: CSV input, output is stored in single text files for each case. 
- filesToCsv: One text file for each case, CSV output. 
- csvToCsv: From a csv table to a csv table. 
- filesToFiles: From a folder with input files to a folder with output files.
 
Four different workflows are derived from the base class:  

- CodingWorkflow: The workflow is used for content analysis if you have predefined categories.
  You provide a codebook with category name, description, and optionally examples.  
  The LLM workflow will output one or multiple matching categories.
- SummaryWorkflow: The workflow is used for qualitative content analysis approaches.
  The input is condensed into a shorter summary, phrase or keyword. 
  If you provide categories, one summary or keyword is provided for each category.
  This workflow is very open. You can use it to bypass pre- and postprocessing and 
  work with raw LLM results.
- AnnoWorkflow: The workflow can be used to find text segments, for example for annotating
  named entities. According to a rule set, the matching text segments are enclosed in tags.   
- TripleWorkflow: The workflow is used for extracting statements from the inputs.  
  Each statement consists of a subject-predicate-object triple. Such a structure
  is, for example, used for knowledge graphs (RDF).
  
Two types of LLM interfaces are implemented:
- Ollama: You can use a locally running Ollama docker container (in the localmodels branch).
- UniGPT: You can use the UniGPT provided models. The interface is in principle compatible
  with other LLM providers such as OpenAI APIs. 

The workflow functions support the following settings:

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
- rawAnswer: Whether to return the answer message or all raw values of the model response.
- model: The model name to use. Defaults to the model defined in the LLM client.
- temperature: The temperature to use. Defaults to the temperature defined in the LLM client.

# Parsing

The `ParseWorkflow()` class parses texts that are written in a specific notation and returns XML.
It does not use an LLM. No prompts, cache or model settings apply.

```
wf = ParseWorkflow()
results = wf.dataToData(['text one', 'text two'], {'formalism': 'ebnf', 'dialect': 'dio'})
```

Settings:

- formalism (required): The kind of specification the parser is built from, for example `ebnf`.
- dialect (required): The notation of the input texts, for example `dio`.
  The pair of formalism and dialect selects the parser.
  There are no defaults. A missing option or a pair without a parser raises a `ValueError`.
- rules: Reserved for later use. The value is passed to the parser client, but not processed yet.

The input is a string or a list of strings.
The workflow returns one result per input, in the order of the input.
Each result is a dict with the following keys:

- xml: The parsed text as XML. If errors occurred, this may be a partial tree or None.
- errors: A list of errors. Each error has the keys `level`, `code`, `line`, `column` and `message`.
  The level is one of `notice`, `warning`, `error` or `fatal`.
- failed: True if the errors contain an `error` or `fatal` entry. Notices and warnings do not fail an input.

## Available parsers

The parser list maps a pair of formalism and dialect to a parser client:

| Formalism | Dialect | Description                            |
|-----------|---------|----------------------------------------|
| ebnf      | dio     | Die Deutschen Inschriften Online (DIO) |

Use `has_parser(formalism, dialect)` from `databoard_core.clients` to check whether a pair is available.

## Adding a new dialect

1. Put the grammar (for example `mydialect.ebnf`) and the generated parser (for example `mydialectParser.py`)
   side by side in `src/databoard_core/resources/parser`.
   The copy in this repository is the canonical one, see `docs/adr/0002-core-holds-canonical-grammars.md`.
   Grammar development and parser tests happen elsewhere.
2. Add a client class derived from `ParserClient` in `src/databoard_core/clients`.
   Its `answer(content)` method returns a dict with `xml` and `errors`, see `parser_dio.py` for an example.
3. Register the client with `register_parser(formalism, dialect, clientClass)`
   at the end of `src/databoard_core/clients/parser_registry.py`.
