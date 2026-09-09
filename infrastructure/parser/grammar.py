from decimal import Decimal

import ply.yacc as yacc

from application.dtos import ParsedQuery
from domain.entities import Currency
from domain.exceptions import InvalidQuery
from infrastructure.parser.lexer import tokens  # noqa: F401 -- required by ply.yacc

# PLY reads the p_xxx grammar rule from its docstring at parser-build time
# (module import), so this file must never run under `python -OO` /
# PYTHONOPTIMIZE=2 (which strips docstrings) -- it fails loudly at import
# with "SyntaxError: Can't build parser", not silently.


def p_query(p):
    """query : NUMBER CURRENCY_CODE TO CURRENCY_CODE"""
    # p[1] always matches the NUMBER token's \d+(\.\d+)? pattern, so it is
    # always a valid Decimal literal -- no InvalidOperation to guard against.
    p[0] = ParsedQuery(
        amount=Decimal(p[1]),
        source_currency=Currency(p[2]),
        target_currency=Currency(p[4]),
    )


def p_error(p):
    if p is None:
        raise InvalidQuery("Query is incomplete")
    raise InvalidQuery(f"Unexpected token '{p.value}' in query")


parser = yacc.yacc(write_tables=False, debug=False)
