import pytest

from databoard_core.clients import ParserClient, register_parser, unregister_parser
from databoard_core.flows import ParseWorkflow


class StubParserClient(ParserClient):
    """Placeholder parser: answers with fixed XML derived from the input."""
    def answer(self, content):
        return {'xml': f'<stub>{content}</stub>', 'errors': []}


@pytest.fixture
def stubOptions():
    register_parser('stub', 'test', StubParserClient)
    yield {'formalism': 'stub', 'dialect': 'test'}
    unregister_parser('stub', 'test')


def test_returns_result_with_xml_and_errors_per_input(stubOptions):
    results = ParseWorkflow().dataToData(['a', 'b'], stubOptions)

    assert len(results) == 2
    for result in results:
        assert set(result.keys()) == {'xml', 'errors'}


def test_preserves_input_order(stubOptions):
    results = ParseWorkflow().dataToData(['first', 'second', 'third'], stubOptions)

    assert [r['xml'] for r in results] == [
        '<stub>first</stub>', '<stub>second</stub>', '<stub>third</stub>'
    ]


def test_empty_list_returns_empty_list(stubOptions):
    assert ParseWorkflow().dataToData([], stubOptions) == []


def test_single_string_is_treated_as_list_of_one(stubOptions):
    results = ParseWorkflow().dataToData('only', stubOptions)

    assert results == [{'xml': '<stub>only</stub>', 'errors': []}]


def test_settings_from_constructor_are_used(stubOptions):
    results = ParseWorkflow(stubOptions).dataToData(['x'])

    assert results[0]['xml'] == '<stub>x</stub>'


def test_dio_is_registered_and_returns_result_shape():
    # Interface only: the output quality of the DIO parser is not tested here
    results = ParseWorkflow().dataToData(['anno domini'], {'formalism': 'ebnf', 'dialect': 'dio'})

    assert len(results) == 1
    assert set(results[0].keys()) == {'xml', 'errors'}
    assert isinstance(results[0]['errors'], list)
