"""UPRM-Edge precision-aware language front end (lexer + parser).

Run: python main.py program.uedge

Prints "Parsed successfully" and exits 0 for a valid program.  For any lexical
or syntax error it prints "Error: <description> at line <N>" and exits 0
(the autograder reports any nonzero status as a runtime error).
"""

import argparse
import ast
import sys
import types
import warnings
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, "ply.zip")  # course-provided PLY, if present next to this file


# ============================================================================
# 1. PLY SETUP | Owner: Fernando + 
# ============================================================================
import ply.lex as lex
import ply.yacc as yacc


# ============================================================================
# 2. TOKEN CONTRACT | Owner: Fernando + 
# ============================================================================
reserved = {
    "let": "LET",
    "func": "FUNC",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "return": "RETURN",
    "print": "PRINT",
    "ref": "REF",
    "mut": "MUT",
    "bool": "BOOL",
    "int8": "INT8",
    "int16": "INT16",
    "int32": "INT32",
    "int64": "INT64",
    "int128": "INT128",
    "uint8": "UINT8",
    "uint16": "UINT16",
    "uint32": "UINT32",
    "uint64": "UINT64",
    "uint128": "UINT128",
    "float16": "FLOAT16",
    "float32": "FLOAT32",
    "float64": "FLOAT64",
    "float128": "FLOAT128",
    "decimal64": "DECIMAL64",
    "decimal128": "DECIMAL128",
}

# Keywords that name a precision type (used by the precision-aware grammar).
TYPE_TOKENS = (
    "BOOL",
    "INT8", "INT16", "INT32", "INT64", "INT128",
    "UINT8", "UINT16", "UINT32", "UINT64", "UINT128",
    "FLOAT16", "FLOAT32", "FLOAT64", "FLOAT128",
    "DECIMAL64", "DECIMAL128",
)

tokens = (
    "ID",
    "INT_LITERAL",
    "FLOAT_LITERAL",
    "DECIMAL_LITERAL",
    "BOOL_LITERAL",
    "STRING_LITERAL",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "MODULO",
    "EQ",
    "NE",
    "LT",
    "GT",
    "LE",
    "GE",
    "ASSIGN",
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",
    "COMMA",
    "SEMICOLON",
    "COLON",
    "DOT",
    "ARROW",
    *tuple(dict.fromkeys(reserved.values())),
)


# ============================================================================
# 3. LEXER | Owner: Fernando + 
# ============================================================================
class FrontEndError(Exception):
    """A lexical or syntax error that carries the line where it happened."""

    def __init__(self, message, lineno=None):
        super().__init__(message)
        self.message = message
        self.lineno = lineno

    def __str__(self):
        if self.lineno is None:
            return self.message
        return f"{self.message} at line {self.lineno}"


class LexerError(FrontEndError):
    """Raised when source text cannot be tokenized."""


class ParseError(FrontEndError):
    """Raised when the token stream does not match the grammar."""


t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_MODULO = r"%"
t_EQ = r"=="
t_NE = r"!="
t_LE = r"<="
t_GE = r">="
t_LT = r"<"
t_GT = r">"
t_ASSIGN = r"="
t_ARROW = r"->"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_COMMA = r","
t_SEMICOLON = r";"
t_COLON = r":"
t_DOT = r"\."
t_ignore = " \t\r"


def t_COMMENT(token):
    r"//[^\n]*"
    pass


def t_DECIMAL_LITERAL(token):
    r"(?:\d+\.\d*|\.\d+|\d+)[dD](?:64|128)\b"
    suffix_length = 4 if token.value[-3:] == "128" else 3
    try:
        token.value = Decimal(token.value[:-suffix_length])
    except InvalidOperation as exc:
        raise LexerError("malformed decimal", token.lineno) from exc
    return token


def t_FLOAT_LITERAL(token):
    r"(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)(?:[fF](?:16|32|64|128)\b)?|\d+[fF](?:16|32|64|128)\b"
    suffix_start = max(token.value.rfind("f"), token.value.rfind("F"))
    numeric_text = token.value if suffix_start < 0 else token.value[:suffix_start]
    token.value = float(numeric_text)
    return token


def t_INT_LITERAL(token):
    r"\d+"
    token.value = int(token.value)
    return token


def t_STRING_LITERAL(token):
    r'"(?:[^"\\\n]|\\.)*"'
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            token.value = ast.literal_eval(token.value)
    except (SyntaxError, ValueError) as exc:
        raise LexerError("malformed string", token.lineno) from exc
    return token


def t_UNTERMINATED_STRING(token):
    r'"(?:[^"\\\n]|\\.)*(?:\n|$)'
    raise LexerError("malformed string", token.lineno)


def t_ID(token):
    r"[A-Za-z_][A-Za-z0-9_]*"
    if token.value == "true":
        token.type = "BOOL_LITERAL"
        token.value = True
    elif token.value == "false":
        token.type = "BOOL_LITERAL"
        token.value = False
    else:
        token.type = reserved.get(token.value, "ID")
    return token


def t_newline(token):
    r"\n+"
    token.lexer.lineno += len(token.value)


def t_error(token):
    raise LexerError(f"unexpected token \u2018{token.value[0]}\u2019", token.lexer.lineno)


def build_lexer():
    """Create a new lexer so callers do not share line-number state."""
    return lex.lex()


def tokenize_source(source: str):
    """Yield all tokens in source or raise LexerError."""
    lexer = build_lexer()
    lexer.input(source)
    yield from lexer


# ============================================================================
# 4. COMMON-CORE YACC GRAMMAR | Owner: __________
# ============================================================================
# Agreed syntax (C-like, braces and semicolons required):
#
#   program        : statement*
#   statement      : declaration ';' | assignment ';' | call ';'
#                  | 'print' expression ';'          (print(x); is print + grouping)
#                  | 'return' [expression] ';'
#                  | 'if' expression block ['else' (block | if_statement)]
#                  | 'while' expression block
#                  | 'for' '(' [init] ';' [expression] ';' [assignment] ')' block
#                  | 'func' ID '(' [parameters] ')' [('->' | ':') type] block
#                  | block
#   block          : '{' statement* '}'
#   expression     : arithmetic / comparison, unary '-', '(' expression ')',
#                    literals, identifiers, calls, and explicit casts type(expr)
#
# Operator precedence is declared below (lowest to highest). Because blocks are
# mandatory, "if ... else" has no dangling-else ambiguity.
precedence = (
    ("left", "EQ", "NE"),
    ("left", "LT", "GT", "LE", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MODULO"),
    ("right", "UMINUS"),
)

start = "program"
# AST: plain tuples whose first item is the node kind, e.g.
#   ("program", [stmt, ...])
#   ("let", name, type_or_None, expr)        ("assign", name, expr)
#   ("func", name, [(pname, ptype), ...], return_type_or_None, block)
#   ("if", cond, then_block, else_block_or_None)   ("while", cond, block)
#   ("for", init, cond, update, block)       ("return", expr_or_None)
#   ("print", expr)        ("call", name, [args])   ("block", [stmt, ...])
#   ("binop", op, l, r)    ("unop", op, e)    ("cast", type, e)
#   ("literal", kind, value)                  ("var", name)


def p_program(p):
    "program : statement_list"
    p[0] = ("program", p[1])


def p_statement_list_many(p):
    "statement_list : statement_list statement"
    p[0] = p[1] + [p[2]]


def p_statement_list_empty(p):
    "statement_list : empty"
    p[0] = []


def p_empty(p):
    "empty :"
    p[0] = None


def p_statement_simple(p):
    """statement : declaration SEMICOLON
                 | assignment SEMICOLON"""
    p[0] = p[1]


def p_statement_call(p):
    "statement : function_call SEMICOLON"
    p[0] = p[1]


def p_statement_compound(p):
    """statement : if_statement
                 | while_statement
                 | for_statement
                 | function_declaration
                 | block"""
    p[0] = p[1]


def p_print_statement(p):
    "statement : PRINT expression SEMICOLON"
    p[0] = ("print", p[2])


def p_return_statement(p):
    """statement : RETURN SEMICOLON
                 | RETURN expression SEMICOLON"""
    p[0] = ("return", p[2] if len(p) == 4 else None)


def p_block(p):
    "block : LBRACE statement_list RBRACE"
    p[0] = ("block", p[2])


# ---- declarations and assignment (precision-aware forms live here too) -----
def p_declaration_let(p):
    "declaration : LET ID ASSIGN expression"
    p[0] = ("let", p[2], None, p[4])


def p_declaration_let_typed(p):
    "declaration : LET ID COLON precision_type ASSIGN expression"
    p[0] = ("let", p[2], p[4], p[6])


def p_declaration_c_style(p):
    "declaration : precision_type ID ASSIGN expression"
    p[0] = ("let", p[2], p[1], p[4])


def p_assignment(p):
    "assignment : ID ASSIGN expression"
    p[0] = ("assign", p[1], p[3])


# ---- functions --------------------------------------------------------------
def p_function_declaration(p):
    "function_declaration : FUNC ID LPAREN parameters RPAREN return_type block"
    p[0] = ("func", p[2], p[4], p[6], p[7])


def p_return_type(p):
    """return_type : ARROW precision_type
                   | COLON precision_type"""
    p[0] = p[2]


def p_return_type_empty(p):
    "return_type : empty"
    p[0] = None


def p_parameters_empty(p):
    "parameters : empty"
    p[0] = []


def p_parameters_list(p):
    "parameters : parameter_list"
    p[0] = p[1]


def p_parameter_list_one(p):
    "parameter_list : parameter"
    p[0] = [p[1]]


def p_parameter_list_many(p):
    "parameter_list : parameter_list COMMA parameter"
    p[0] = p[1] + [p[3]]


def p_parameter_untyped(p):
    "parameter : ID"
    p[0] = (p[1], None)


def p_parameter_colon(p):
    "parameter : ID COLON precision_type"
    p[0] = (p[1], p[3])


def p_parameter_c_style(p):
    "parameter : precision_type ID"
    p[0] = (p[2], p[1])


def p_function_call(p):
    "function_call : ID LPAREN arguments RPAREN"
    p[0] = ("call", p[1], p[3])


def p_arguments_empty(p):
    "arguments : empty"
    p[0] = []


def p_arguments_list(p):
    "arguments : argument_list"
    p[0] = p[1]


def p_argument_list_one(p):
    "argument_list : expression"
    p[0] = [p[1]]


def p_argument_list_many(p):
    "argument_list : argument_list COMMA expression"
    p[0] = p[1] + [p[3]]


# ---- control flow -----------------------------------------------------------
def p_if_statement(p):
    "if_statement : IF expression block optional_else"
    p[0] = ("if", p[2], p[3], p[4])


def p_optional_else_block(p):
    "optional_else : ELSE block"
    p[0] = p[2]


def p_optional_else_if(p):
    "optional_else : ELSE if_statement"
    p[0] = p[2]


def p_optional_else_empty(p):
    "optional_else : empty"
    p[0] = None


def p_while_statement(p):
    "while_statement : WHILE expression block"
    p[0] = ("while", p[2], p[3])


def p_for_statement(p):
    """for_statement : FOR LPAREN for_init SEMICOLON for_condition SEMICOLON for_update RPAREN block"""
    p[0] = ("for", p[3], p[5], p[7], p[9])


def p_for_init(p):
    """for_init : declaration
                | assignment
                | empty"""
    p[0] = p[1]


def p_for_condition(p):
    """for_condition : expression
                     | empty"""
    p[0] = p[1]


def p_for_update(p):
    """for_update : assignment
                  | empty"""
    p[0] = p[1]


# ============================================================================
# 5. PRECISION-AWARE TRACK | Owner: __________
# ============================================================================
# Provisional syntax agreed for this template:
#     let x: int8 = 1;      int8 x = 1;      let x = 1;   (type inferred)
#     Typed parameter shape: x: float16   (also: float16 x; plain `x` is
#     accepted too so common-core programs without types still parse)
#     Return type:  func f(x: int8) -> int8 { ... }   (':' also accepted)
#     Explicit cast: int8(x), float16(x)
# Semantic checks (value ranges, overflow, rounding) belong to Subproject 2.
def p_precision_type(p):
    p[0] = p[1]


p_precision_type.__doc__ = "precision_type : " + "\n | ".join(TYPE_TOKENS)


def p_expression_cast(p):
    "expression : precision_type LPAREN expression RPAREN"
    p[0] = ("cast", p[1], p[3])


# ---- expressions ------------------------------------------------------------
def p_expression_binary(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MODULO expression
                  | expression EQ expression
                  | expression NE expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression"""
    p[0] = ("binop", p[2], p[1], p[3])


def p_expression_unary_minus(p):
    "expression : MINUS expression %prec UMINUS"
    p[0] = ("unop", "-", p[2])


def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression_call(p):
    "expression : function_call"
    p[0] = p[1]


def p_expression_id(p):
    "expression : ID"
    p[0] = ("var", p[1])


def p_expression_int(p):
    "expression : INT_LITERAL"
    p[0] = ("literal", "int", p[1])


def p_expression_float(p):
    "expression : FLOAT_LITERAL"
    p[0] = ("literal", "float", p[1])


def p_expression_decimal(p):
    "expression : DECIMAL_LITERAL"
    p[0] = ("literal", "decimal", p[1])


def p_expression_bool(p):
    "expression : BOOL_LITERAL"
    p[0] = ("literal", "bool", p[1])


def p_expression_string(p):
    "expression : STRING_LITERAL"
    p[0] = ("literal", "string", p[1])


# ============================================================================
# 6. AST, DIAGNOSTICS, AND PARSER ENTRY POINT | Owner: __________
# ============================================================================
# Token types that can end an expression (used to detect a missing ';' or ')').
_ENDERS = {
    "ID", "INT_LITERAL", "FLOAT_LITERAL", "DECIMAL_LITERAL",
    "BOOL_LITERAL", "STRING_LITERAL", "RPAREN",
}

# Token type -> source text, used to word error messages.
TOKEN_TEXT = {
    name[2:]: value.replace("\\", "")
    for name, value in list(globals().items())
    if name.startswith("t_") and isinstance(value, str) and name != "t_ignore"
}
TOKEN_TEXT.update({token_type: text for text, token_type in reserved.items()})

# State shared between parse_source() and p_error().
_context = types.SimpleNamespace(parser=None, stream=None)


class TokenStream:
    """Wraps the lexer so p_error can see line numbers and open ( and {."""

    def __init__(self, lexer):
        self.lexer = lexer
        self.parens = 0
        self.braces = 0
        self.before = (0, 0)       # (parens, braces) open before the latest token
        self.last_line, self.last_type = 1, None
        self.prev_line, self.prev_type = 1, None   # the token before the latest

    def input(self, data):
        self.lexer.input(data)

    def token(self):
        tok = self.lexer.token()
        self.before = (self.parens, self.braces)
        if tok is None:
            return None
        self.prev_line, self.prev_type = self.last_line, self.last_type
        self.last_line, self.last_type = tok.lineno, tok.type
        if tok.type == "LPAREN":
            self.parens += 1
        elif tok.type == "RPAREN":
            self.parens -= 1
        elif tok.type == "LBRACE":
            self.braces += 1
        elif tok.type == "RBRACE":
            self.braces -= 1
        return tok


def quote(text):
    return f"\u2018{text}\u2019"


def token_text(tok):
    if tok.type in TOKEN_TEXT:
        return TOKEN_TEXT[tok.type]
    if tok.type == "BOOL_LITERAL":
        return "true" if tok.value else "false"
    if tok.type == "STRING_LITERAL":
        return f'"{tok.value}"'
    return str(tok.value)


def state_accepts_semicolon():
    """True if the parser could shift ';' here (True when it cannot tell)."""
    try:
        parser = _context.parser
        return "SEMICOLON" in parser.action[parser.statestack[-1]]
    except Exception:
        return True


def p_error(tok):
    """Called by PLY on the first syntax error; reject instead of recovering."""
    stream = _context.stream
    parens, braces = stream.before
    if tok is None:
        line = prev_line = stream.last_line
        prev_type = stream.last_type
    else:
        line, prev_line, prev_type = tok.lineno, stream.prev_line, stream.prev_type

    closes_paren = tok is None or tok.type in ("SEMICOLON", "LBRACE", "RBRACE") \
        or tok.lineno > prev_line
    if parens > 0 and prev_type in _ENDERS and closes_paren:
        raise ParseError("missing closing ')'", line)
    if (
        prev_type in _ENDERS
        and (tok is None or tok.lineno > prev_line)
        and state_accepts_semicolon()
    ):
        raise ParseError(f"expected {quote(';')}", prev_line)
    if tok is None:
        if braces > 0:
            raise ParseError("missing closing '}'")
        raise ParseError("unexpected end of file", line)
    raise ParseError(f"unexpected token {quote(token_text(tok))}", line)


def build_parser():
    """Build the LALR parser; tolerate PLY versions with fewer yacc() options."""
    options = {"start": "program", "debug": False, "write_tables": False}
    if hasattr(yacc, "NullLogger"):
        options["errorlog"] = yacc.NullLogger()
    for dropped in ("write_tables", "errorlog", "debug", "start"):
        try:
            return yacc.yacc(**options)
        except TypeError:
            options.pop(dropped, None)
    return yacc.yacc()


def parse_source(source):
    """Parse source text into an AST tuple or raise LexerError/ParseError."""
    stream = TokenStream(build_lexer())
    parser = build_parser()
    _context.parser = parser
    _context.stream = stream
    return parser.parse(source, lexer=stream)


# ============================================================================
# 7. VALIDATION CHECKLIST | Owner: __________
# ============================================================================
# [x] Every keyword, literal, operator, and punctuation token
# [x] Keyword prefixes remain identifiers: letter, float16_value
# [x] Comments, whitespace, escaped strings, and line tracking
# [ ] Nested functions/calls, blocks, branches, and loops as allowed by grammar
# [ ] Arithmetic/comparison precedence and unary operators
# [ ] Valid precision declarations, parameters, and return types
# [ ] Missing/malformed track-specific syntax is rejected
# [ ] Missing operands, delimiters, braces, and unexpected EOF are rejected
# [ ] CLI accepts one path, including paths containing spaces
# [ ] Missing/extra arguments and unreadable files fail without prompting


# ============================================================================
# 8. COMMAND-LINE FILE LOADING | Fernando + 
# ============================================================================
def load_source_file() -> str:
    """Read the single source file supplied on the command line."""
    parser = argparse.ArgumentParser(description="Parse a UPRM-Edge source file.")
    parser.add_argument("source_file", type=Path, help="UPRM-Edge source file")
    args = parser.parse_args()

    try:
        return args.source_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")


def emit(text):
    """Print as UTF-8 regardless of the terminal's encoding (curly quotes)."""
    try:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.flush()
    except AttributeError:
        print(text)


def main() -> int:
    source = load_source_file()
    try:
        parse_source(source)
    except FrontEndError as exc:
        emit(f"Error: {exc}")
        return 0  # the grader treats a nonzero status as a runtime error
    except Exception as exc:  # never show a traceback to the autograder
        emit(f"Error: internal parser failure ({exc})")
        return 0
    emit("Parsed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())