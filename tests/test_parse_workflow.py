import pytest

from databoard_core.clients import ParserClient, register_parser, unregister_parser
from databoard_core.flows import ParseWorkflow


class StubParserClient(ParserClient):
    """Placeholder parser: answers with fixed XML derived from the input."""
    def answer(self, content):
        return {'xml': f'<stub>{content}</stub>', 'errors': []}


class LevelStubParserClient(ParserClient):
    """Placeholder parser: the input names the error level to report, or 'ok' for none."""
    def answer(self, content):
        errors = [] if content == 'ok' else [self.makeError(content, 1, 2, 3, 'msg')]
        return {'xml': f'<partial>{content}</partial>', 'errors': errors}


@pytest.fixture
def levelOptions():
    register_parser('stub', 'levels', LevelStubParserClient)
    yield {'formalism': 'stub', 'dialect': 'levels'}
    unregister_parser('stub', 'levels')


@pytest.fixture
def stubOptions():
    register_parser('stub', 'test', StubParserClient)
    yield {'formalism': 'stub', 'dialect': 'test'}
    unregister_parser('stub', 'test')


def test_returns_result_with_xml_and_errors_per_input(stubOptions):
    results = ParseWorkflow().dataToData(['a', 'b'], stubOptions)

    assert len(results) == 2
    for result in results:
        assert set(result.keys()) == {'xml', 'errors', 'failed'}


def test_preserves_input_order(stubOptions):
    results = ParseWorkflow().dataToData(['first', 'second', 'third'], stubOptions)

    assert [r['xml'] for r in results] == [
        '<stub>first</stub>', '<stub>second</stub>', '<stub>third</stub>'
    ]


def test_empty_list_returns_empty_list(stubOptions):
    assert ParseWorkflow().dataToData([], stubOptions) == []


def test_single_string_is_treated_as_list_of_one(stubOptions):
    results = ParseWorkflow().dataToData('only', stubOptions)

    assert results == [{'xml': '<stub>only</stub>', 'errors': [], 'failed': False}]


def test_settings_from_constructor_are_used(stubOptions):
    results = ParseWorkflow(stubOptions).dataToData(['x'])

    assert results[0]['xml'] == '<stub>x</stub>'


def test_dio_is_registered_and_returns_result_shape():
    # Interface only: the output quality of the DIO parser is not tested here
    results = ParseWorkflow().dataToData(['anno domini'], {'formalism': 'ebnf', 'dialect': 'dio'})

    assert len(results) == 1
    assert set(results[0].keys()) == {'xml', 'errors', 'failed'}
    assert isinstance(results[0]['errors'], list)


def test_notices_and_warnings_do_not_fail_the_input(levelOptions):
    results = ParseWorkflow().dataToData(['ok', 'notice', 'warning'], levelOptions)

    assert [r['failed'] for r in results] == [False, False, False]


def test_error_and_fatal_fail_the_input(levelOptions):
    results = ParseWorkflow().dataToData(['error', 'fatal'], levelOptions)

    assert [r['failed'] for r in results] == [True, True]


def test_errors_keep_their_fields(levelOptions):
    result = ParseWorkflow().dataToData(['warning'], levelOptions)[0]

    assert result['errors'] == [
        {'level': 'warning', 'code': 1, 'line': 2, 'column': 3, 'message': 'msg'}
    ]


def test_partial_xml_is_kept_when_errors_occur(levelOptions):
    result = ParseWorkflow().dataToData(['error'], levelOptions)[0]

    assert result['failed'] is True
    assert result['xml'] == '<partial>error</partial>'


def test_mixed_batch_has_a_flag_per_input(levelOptions):
    results = ParseWorkflow().dataToData(['ok', 'error', 'warning', 'fatal'], levelOptions)

    assert [r['failed'] for r in results] == [False, True, False, True]
