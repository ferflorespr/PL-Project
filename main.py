"""UPRM-Edge precision-aware language front end.

Run: python main.py program.uedge
The lexer validates and tokenizes the source; parser work is still in progress.
"""

import argparse
import ast
from decimal import Decimal, InvalidOperation
from pathlib import Path


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
    *tuple(dict.fromkeys(reserved.values())),
)


# ============================================================================
# 3. LEXER | Owner: Fernando + 
# ============================================================================
class LexerError(Exception):
    """Raised when source text cannot be tokenized."""


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
        raise LexerError(
            f"malformed decimal at line {token.lineno}"
        ) from exc
    return token


def t_FLOAT_LITERAL(token):
    r"(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)(?:[fF](?:16|32|64|128))?\b|\d+[fF](?:16|32|64|128)\b"
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
        token.value = ast.literal_eval(token.value)
    except (SyntaxError, ValueError) as exc:
        raise LexerError(
            f"malformed string at line {token.lineno}"
        ) from exc
    return token


def t_UNTERMINATED_STRING(token):
    r'"(?:[^"\\\n]|\\.)*(?:\n|$)'
    raise LexerError(f"malformed string at line {token.lineno}")


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
    character = token.value[0]
    raise LexerError(f"unexpected token {character!r} at line {token.lineno}")


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
# TODO: Define start = "program" and operator precedence/associativity.
# TODO: Agree on braces, semicolons, condition parentheses, for-loop syntax,
#       function return syntax, and optional constructs before writing rules.
# TODO: Implement p_* functions with grammar docstrings and AST actions.
#
# Production checklist:
# [ ] program / statement_list / statement / block
# [ ] variable_declaration / assignment
# [ ] function_declaration / parameters / function_call / arguments
# [ ] if_statement / optional_else
# [ ] while_statement / for_statement
# [ ] return_statement / print_statement
# [ ] expression: literals, identifiers, calls, grouping, unary/binary operators
# [ ] empty: only where the agreed syntax allows an empty construct
#
# Production function shape, for reference only:
# def p_program(p):
#     "program : statement_list"
#     p[0] = ...  # Use the AST representation agreed in section 6.

# ============================================================================
# 4. COMMON-CORE YACC GRAMMAR | Owner: Team
# ============================================================================
import ply.yacc as yacc

# Tells PLY that the root/starting rule of our grammar is "program"
start = "program"

# Defines operator precedence and associativity from lowest to highest.
# This prevents ambiguity in mathematical expressions (e.g., ensuring 
# multiplication happens before addition without requiring extra parentheses).
precedence = (
    ("left", "EQ", "NE"),                    # ==, !=
    ("left", "LT", "LE", "GT", "GE"),        # <, <=, >, >=
    ("left", "PLUS", "MINUS"),               # +, -
    ("left", "TIMES", "DIVIDE", "MODULO"),   # *, /, %
    ("right", "UMINUS"),                     # Unary minus (e.g., -5)
)


def p_program(p):
    """program : statement_list"""
    # Root rule: wraps the entire list of parsed statements into an AST node tuple
    p[0] = ("program", p[1])


def p_statement_list_empty(p):
    """statement_list : """
    # Base case for recursion: an empty statement list returns an empty list
    p[0] = []


def p_statement_list_multiple(p):
    """statement_list : statement_list statement"""
    # Recursive case: appends a new statement to the existing list of statements
    p[0] = p[1] + [p[2]]


def p_statement(p):
    """statement : variable_declaration
                 | assignment_statement
                 | function_declaration
                 | if_statement
                 | while_statement
                 | for_statement
                 | return_statement
                 | print_statement
                 | expression_statement"""
    # Statement router: matches any valid statement type and passes it up
    p[0] = p[1]


def p_block(p):
    """block : LBRACE statement_list RBRACE"""
    # Represents a code block enclosed in curly braces { statement_list }[cite: 6]
    p[0] = ("block", p[2])


def p_type_specifier_builtin(p):
    """type_specifier : BOOL
                      | INT8
                      | INT16
                      | INT32
                      | INT64
                      | INT128
                      | UINT8
                      | UINT16
                      | UINT32
                      | UINT64
                      | UINT128
                      | FLOAT16
                      | FLOAT32
                      | FLOAT64
                      | FLOAT128
                      | DECIMAL64
                      | DECIMAL128
                      | ID"""
    # Matches any built-in precision type keyword or custom identifier type[cite: 6, 7]
    p[0] = p[1]


def p_type_specifier_generic(p):
    """type_specifier : ID LT type_arguments GT"""
    # Matches generic collection types like Series<float64>[cite: 7]
    p[0] = ("generic_type", p[1], p[3])


def p_type_arguments(p):
    """type_arguments : type_arguments COMMA type_specifier
                      | type_specifier"""
    # Handles single or comma-separated type parameters inside generics (e.g., Map<K, V>)
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_variable_declaration(p):
    """variable_declaration : LET ID ASSIGN expression SEMICOLON
                            | LET ID COLON type_specifier ASSIGN expression SEMICOLON"""
    # Handles variable creation, supporting both implicit types (let x = 5;) 
    # and precision-aware typed declarations (let x: int8 = 5;)[cite: 6, 7]
    if len(p) == 6:
        p[0] = ("var_decl", p[2], None, p[4])       # No explicit type given
    else:
        p[0] = ("var_decl", p[2], p[4], p[6])       # Explicit type included


def p_assignment_statement(p):
    """assignment_statement : assignment_target ASSIGN expression SEMICOLON"""
    # Handles reassigning values to existing variables, array indices, or object members
    p[0] = ("assign", p[1], p[3])


def p_assignment_target(p):
    """assignment_target : ID
                         | member_access
                         | index_expression"""
    # Specifies what can be legally assigned to on the left-hand side
    p[0] = p[1]


def p_if_statement(p):
    """if_statement : IF LPAREN expression RPAREN block optional_else"""
    # Parses conditional if-branches, requiring parentheses around conditions[cite: 2, 7]
    p[0] = ("if", p[3], p[5], p[6])


def p_optional_else(p):
    """optional_else : ELSE block
                     | ELSE if_statement
                     | empty"""
    # Handles trailing else blocks or else-if chains
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None


def p_while_statement(p):
    """while_statement : WHILE LPAREN expression RPAREN block"""
    # Parses while loops with parenthesized conditions[cite: 2, 7]
    p[0] = ("while", p[3], p[5])


def p_for_statement(p):
    """for_statement : FOR LPAREN for_init SEMICOLON expression SEMICOLON expression RPAREN block"""
    # Parses C-style for loops: for (init; condition; update) { block }[cite: 2, 7]
    p[0] = ("for", p[3], p[5], p[7], p[9])


def p_for_init(p):
    """for_init : variable_declaration
                | assignment_statement
                | empty"""
    # Handles initialization statement inside a for-loop header
    p[0] = p[1]


def p_return_statement(p):
    """return_statement : RETURN expression SEMICOLON
                        | RETURN SEMICOLON"""
    # Parses return statements with or without an expression value[cite: 2, 6]
    if len(p) == 4:
        p[0] = ("return", p[2])
    else:
        p[0] = ("return", None)


def p_print_statement(p):
    """print_statement : PRINT LPAREN expression RPAREN SEMICOLON"""
    # Parses built-in print calls used for outputting values[cite: 2, 6]
    p[0] = ("print", p[3])


def p_expression_statement(p):
    """expression_statement : expression SEMICOLON"""
    # Wraps standalone expressions that terminate with a semicolon (like function calls)
    p[0] = ("expr_stmt", p[1])


def p_function_declaration(p):
    """function_declaration : FUNC ID LPAREN parameter_list RPAREN return_annotation block"""
    # Parses user-defined functions: func name(params) : return_type { body }[cite: 2, 6, 7]
    p[0] = ("func_decl", p[2], p[4], p[6], p[7])


def p_parameter_list(p):
    """parameter_list : parameters
                      | empty"""
    # Returns a list of function parameters, or an empty list if none exist
    p[0] = p[1] if p[1] is not None else []


def p_parameters(p):
    """parameters : parameters COMMA parameter
                  | parameter"""
    # Accumulates multiple parameters separated by commas
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_parameter(p):
    """parameter : ID COLON parameter_mode type_specifier
                 | ID COLON type_specifier"""
    # Parses individual parameters, supporting reference types (e.g., ref or ref mut)[cite: 6, 7]
    if len(p) == 5:
        p[0] = ("param", p[1], p[3], p[4])  # With reference mode
    else:
        p[0] = ("param", p[1], None, p[3])  # Standard pass-by-value parameter


def p_parameter_mode(p):
    """parameter_mode : REF MUT
                      | REF"""
    # Identifies parameter passing rules for financial data efficiency[cite: 6, 7]
    if len(p) == 3:
        p[0] = "ref_mut"                    # Mutable reference
    else:
        p[0] = "ref"                        # Read-only reference


def p_return_annotation(p):
    """return_annotation : COLON type_specifier
                         | empty"""
    # Parses the optional return type definition of a function (e.g., : float64)[cite: 6, 7]
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None


def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MODULO expression
                  | expression EQ expression
                  | expression NE expression
                  | expression LT expression
                  | expression LE expression
                  | expression GT expression
                  | expression GE expression"""
    # Binary operations combining two expressions with an operator[cite: 2, 6]
    p[0] = ("binop", p[2], p[1], p[3])


def p_expression_uminus(p):
    """expression : MINUS expression %prec UMINUS"""
    # Unary minus operation for negative numbers or expressions (e.g., -x)
    p[0] = ("unary", "-", p[2])


def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""
    # Parenthesized sub-expressions used to override standard operator precedence
    p[0] = p[2]


def p_expression_literal(p):
    """expression : INT_LITERAL
                  | FLOAT_LITERAL
                  | DECIMAL_LITERAL
                  | BOOL_LITERAL
                  | STRING_LITERAL"""
    # Raw literal values (numbers, booleans, strings)[cite: 2, 6]
    p[0] = ("literal", p[1])


def p_expression_id(p):
    """expression : ID"""
    # Variable or identifier lookups in an expression[cite: 2, 6]
    p[0] = ("id", p[1])


def p_expression_call(p):
    """expression : expression LPAREN argument_list RPAREN"""
    # Function calls or explicit type casting (e.g., int8(val))[cite: 2, 6, 7]
    p[0] = ("call", p[1], p[3])


def p_argument_list(p):
    """argument_list : arguments
                     | empty"""
    # Returns argument lists passed into function calls
    p[0] = p[1] if p[1] is not None else []


def p_arguments(p):
    """arguments : arguments COMMA expression
                 | expression"""
    # Accumulates multiple comma-separated arguments for a function call
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_expression_member(p):
    """expression : expression DOT ID"""
    # Object member or property access using dot notation (e.g., context.portfolio)[cite: 7]
    p[0] = ("member", p[1], p[3])


def p_expression_index(p):
    """expression : expression LBRACKET expression RBRACKET"""
    # Array or series indexing using brackets (e.g., prices[i])[cite: 7]
    p[0] = ("index", p[1], p[3])


def p_empty(p):
    """empty : """
    # Helper production representing an empty match for optional syntax rules
    p[0] = None

# ============================================================================
# 5. PRECISION-AWARE TRACK | Owner: __________
# ============================================================================
# Provisional syntax agreed for this template:
#     let x: int8 = 1;
#     Typed parameter shape: x: float16
#
# TODO: Check the Track Selection Guide for the complete precision type set.
# TODO: Confirm function return type syntax and whether inference is permitted.
# TODO: Define precision_type productions for supported type keywords.
# TODO: Connect types to variable declarations, parameters, and return types.
# TODO: Require type syntax wherever the track requires it.
# TODO: Reject missing required types, unsupported types, and malformed colons.
# TODO: Keep semantic checks (such as value ranges) separate from syntax checks.


# ============================================================================
# 6. AST, DIAGNOSTICS, AND PARSER ENTRY POINT | Owner: __________
# ============================================================================
# TODO: Agree on one AST representation used by all grammar actions.
# TODO: Implement p_error for unexpected tokens and unexpected EOF.
# TODO: Report file, line, and column for lexical and syntax errors.
# TODO: Reject malformed input instead of accepting only its valid prefix.
# TODO: Agree on autograder output and nonzero error exit codes.
#
# Future entry point (intentionally not implemented):
# def parse_source(source):
#     lexer = lex.lex()
#     parser = yacc.yacc(start="program", write_tables=False)
#     return parser.parse(source, lexer=lexer)
class ParserError(Exception):
    """Raised when source text contains syntax errors."""
    pass


def p_error(p):
    """Error handling hook for PLY when a syntax error occurs."""
    if p:
        # Raises a clean error containing the unexpected token and exact line number[cite: 2]
        raise ParserError(f"unexpected token {p.value!r} at line {p.lineno}")
    else:
        # Handles unexpected end-of-file errors
        raise ParserError("unexpected end of file")


def parse_source(source: str):
    """Coordinates parsing by initializing a fresh lexer and yacc parser instance."""
    lexer = build_lexer()
    parser = yacc.yacc(start="program", write_tables=False, debug=False)
    return parser.parse(source, lexer=lexer, tracking=True)

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
    parser = argparse.ArgumentParser(description="Read a UPRM-Edge source file.")
    parser.add_argument("source_file", type=Path, help="UPRM-Edge source file")
    args = parser.parse_args()

    try:
        return args.source_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")


def main() -> int:
    source = load_source_file()
    try:
        for _ in tokenize_source(source):
            pass
    except LexerError as exc:
        print(f"Error: {exc}")
        return 1
    # TODO: Call parse_source(source) after the grammar is implemented.
    print("Parsed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
