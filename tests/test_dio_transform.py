import json
import subprocess
import sys
from pathlib import Path
from xml.etree.ElementTree import canonicalize

from databoard_core.flows import ParseWorkflow

FIXTURES = Path(__file__).parent / 'fixtures' / 'dio'
DIO = {'rules': {'formalism': 'ebnf', 'dialect': 'dio'}}


def readFixture(name):
    return (FIXTURES / name).read_text(encoding='utf-8')


# A raw transcription as it comes from T3 parses to the same slim XML as in the grammar development project (leiden),
# because results must not depend on where an inscription is parsed.
# The test inscription is invented, but uses the same markup as real inscriptions.
# It contains look-alike word separators (U+2219) that only parse after preprocessing.
# The XML is compared in canonical form, so the serialization of empty elements does not matter.
def test_raw_inscription_gives_expected_xml():
    result = ParseWorkflow().dataToData(readFixture('test_inscription.txt'), DIO)[0]

    assert result['errors'] == []
    assert canonicalize(result['xml']) == canonicalize(readFixture('test_inscription.xml'))


# Letters, spaces, terminators and binders are serialized as plain text, so the XML stays readable.
def test_output_contains_no_letters_elements():
    result = ParseWorkflow().dataToData(readFixture('test_inscription.txt'), DIO)[0]

    assert '<letters' not in result['xml']


# A leading byte order mark and surrounding whitespace do not change the result,
# because exports from other tools often contain them.
# Tabs are included, because the grammar itself only skips spaces and line breaks around the container.
def test_bom_and_surrounding_whitespace_are_ignored():
    text = '﻿\t\n  ' + readFixture('test_inscription.txt') + '\n\t  '
    result = ParseWorkflow().dataToData(text, DIO)[0]

    assert result['errors'] == []
    assert canonicalize(result['xml']) == canonicalize(readFixture('test_inscription.xml'))


# A character the preprocessing does not cover (U+0387 GREEK ANO TELEIA, a look-alike of the middle dot)
# gives a parse error with its position and a partial tree, so researchers can locate the problem.
# Without the parser configuration, the error would end in a fatal error without XML.
def test_parse_error_gives_error_with_position_and_partial_tree():
    text = readFixture('test_inscription.txt').replace('∙', '·', 1)
    result = ParseWorkflow().dataToData(text, DIO)[0]

    assert result['failed']
    assert ('error', 4, 18) in [(e['level'], e['line'], e['column']) for e in result['errors']]
    assert 'fatal' not in [e['level'] for e in result['errors']]
    assert result['xml'] is not None


# The parser configuration is in effect in a fresh process that parses before anything else,
# because this is the situation in a Celery worker.
# A subprocess is used because other tests have already imported the parser and loaded its configuration
# in the pytest process; only a new interpreter starts from scratch, without running Celery.
def test_parser_configuration_applies_in_fresh_process():
    script = (
        "import json, sys\n"
        "from databoard_core.flows import ParseWorkflow\n"
        "text = open(sys.argv[1], encoding='utf-8').read().replace('\\u2219', '\\u0387', 1)\n"
        "print(json.dumps(ParseWorkflow().dataToData(text, {'rules': {'formalism': 'ebnf', 'dialect': 'dio'}})[0]))\n"
    )
    output = subprocess.run([sys.executable, '-c', script, str(FIXTURES / 'test_inscription.txt')],
                            capture_output=True, text=True, check=True).stdout
    result = json.loads(output.strip().splitlines()[-1])

    assert 'fatal' not in [e['level'] for e in result['errors']]
    assert result['xml'] is not None
