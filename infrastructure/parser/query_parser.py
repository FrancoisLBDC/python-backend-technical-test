import threading

from application.dtos import ParsedQuery
from infrastructure.parser.grammar import parser
from infrastructure.parser.lexer import lexer

# `lexer` and `parser` are PLY singletons with mutable per-call state
# (lexer.lexdata/lexpos, parser.symstack/statestack) shared across every
# QueryParser instance. Without this lock, two concurrent parse() calls can
# stomp on each other's state and silently produce a result computed from
# the wrong input, with no exception raised.
_parse_lock = threading.Lock()


class QueryParser:
    def parse(self, text: str) -> ParsedQuery:
        with _parse_lock:
            return parser.parse(text.strip(), lexer=lexer)
