import ply.lex as lex

from domain.exceptions import InvalidQuery

tokens = (
    "NUMBER",
    "CURRENCY_CODE",
    "TO",
)

t_ignore = " \t"


# PLY reads each t_xxx pattern from its docstring at lexer-build time
# (module import), so this file must never run under `python -OO` /
# PYTHONOPTIMIZE=2 (which strips docstrings) -- it fails loudly at import
# with "SyntaxError: Can't build lexer", not silently.
def t_TO(t):
    r"to\b"
    return t


def t_NUMBER(t):
    r"\d+(\.\d+)?"
    return t


def t_CURRENCY_CODE(t):
    r"\b[A-Z]{3}\b"
    return t


def t_error(t):
    raise InvalidQuery(f"Unexpected character '{t.value[0]}' in query")


lexer = lex.lex()
