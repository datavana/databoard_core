from databoard_core.clients.parser_dio import DioParserClient

# Maps (formalism, dialect) to a parser client class
_parsers = {}


def register_parser(formalism, dialect, clientClass):
    """
    Register a parser client class for a Formalism and Dialect

    :param formalism: The Formalism, e.g. 'ebnf'
    :param dialect: The Dialect, e.g. 'dio'
    :param clientClass: A class derived from ParserClient
    """
    _parsers[(formalism, dialect)] = clientClass


def unregister_parser(formalism, dialect):
    """
    Remove a registered parser client class
    """
    _parsers.pop((formalism, dialect), None)


def has_parser(formalism, dialect):
    """
    Check whether a parser is registered for a Formalism and Dialect

    :param formalism: The Formalism, e.g. 'ebnf'
    :param dialect: The Dialect, e.g. 'dio'
    :return: True or False
    """
    return (formalism, dialect) in _parsers


def get_parser_class(formalism, dialect):
    """
    Get the parser client class for a Formalism and Dialect

    :param formalism: The Formalism, e.g. 'ebnf'
    :param dialect: The Dialect, e.g. 'dio'
    :return: A class derived from ParserClient
    :raises ValueError: If no parser is registered for the pair
    """
    try:
        return _parsers[(formalism, dialect)]
    except KeyError:
        raise ValueError(f"No parser for formalism '{formalism}' and dialect '{dialect}'")


register_parser('ebnf', 'dio', DioParserClient)
