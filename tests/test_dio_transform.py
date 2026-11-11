from pathlib import Path
from xml.etree.ElementTree import canonicalize

from databoard_core.flows import ParseWorkflow

FIXTURES = Path(__file__).parent / 'fixtures' / 'dio'
DIO = {'formalism': 'ebnf', 'dialect': 'dio'}


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
