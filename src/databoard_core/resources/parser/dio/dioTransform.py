#
# Transform DIO transcriptions into XML
#
# Step 1: Preprocess the text.
#         Replaces broken markup and look-alike characters, see dio_preprocess.csv.
# Step 2: Parse the text with the dio.ebnf grammar, using the settings from dioConfig.ini.
# Step 3: Serialize the tree as slim XML: letters, spaces, terminators and binders
#         become plain text, lines are kept inline.
#
# This is the Databoard version of transform/parse.py in the grammar development project (leiden).
#

import csv
import re
from pathlib import Path

from DHParser.configuration import read_local_config

RESOURCES = Path(__file__).parent

# The settings must be in place before the first parse in a process or thread reads them
if not read_local_config(str(RESOURCES / 'dioConfig.ini')):
    raise FileNotFoundError(f"Missing parser configuration {RESOURCES / 'dioConfig.ini'}")

from databoard_core.resources.parser.dio import dioParser

STRING_TAGS = ["letters", "terminator", "space", "binder"]
INLINE_TAGS = ["lno", "lin", "snt", "snr", "wtr", "z", "abr", "del", "cpl", "add", "insec", "lig",
               "b", "strong", "em", "chr", "sup", "sub", "nl", "appalpha", "appnum"]


def loadRules(filename):
    """
    Load the preprocessing rules

    :param filename: A semicolon separated file with the columns search (a regex) and replace.
                     Further columns (cases, comment) are documentation only.
    :return: A list of tuples with the compiled pattern and the replacement
    """
    with open(filename, encoding='utf-8', newline='') as file:
        return [(re.compile(row['search']), row['replace']) for row in csv.DictReader(file, delimiter=';')]


RULES = loadRules(RESOURCES / 'dio_preprocess.csv')


def preprocess(text):
    """
    Unify a raw transcription before parsing

    :param text: The raw text
    :return: The text with all rules applied in file order, without surrounding whitespace and BOM
    """
    for pattern, replace in RULES:
        text = pattern.sub(replace, text)
    return text.strip().lstrip('﻿')


def transform(text):
    """
    Preprocess, parse and serialize a DIO transcription

    :param text: The raw text
    :return: A tuple with the XML (None if parsing produced no tree) and the list of DHParser messages
    """
    source = preprocess(text)

    # DHParser takes a text without a line break for a file name.
    # A line break makes sure the content is always parsed as source text, never loaded as a file.
    if '\n' not in source:
        source += '\n'

    tree, messages = dioParser.compile_snippet(source)
    xml = tree.as_xml(string_tags=STRING_TAGS, inline_tags=INLINE_TAGS, indentation=2) if tree is not None else None
    return xml, messages
