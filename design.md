# UPRM-Edge: Quantitative Finance Design Direction

## Purpose

UPRM-Edge is a precision-aware programming language. Its main idea is that the programmer explicitly chooses numeric precision, such as `int8` or `float16`, instead of treating every number as an interchangeable integer or floating-point value. Quantitative finance is a useful application area because financial systems must balance numerical accuracy, execution speed, memory use, and reproducibility.

The language could develop in a broad directions:


1. A research and strategy language for statistics, modeling, and backtesting, similar to Python, R, or Julia.

These directions are related, but they require different language and runtime priorities.

## Why Precision Matters in Finance

Financial software should not use low precision everywhere. A small rounding error can accumulate across many trades, produce incorrect risk estimates, or change whether an order is accepted. At the same time, high precision has a cost in memory, bandwidth, and computation.

UPRM-Edge can make these choices visible in source code. For example:

```uedge
let signal: float16 = 0.73;
let price: float64 = 184.125;
let quantity: int32 = 200;
let account_balance: decimal128 = 100000.00;
```

This example uses lower precision for an approximate model signal, standard floating-point precision for market data, an integer for share quantity, and decimal arithmetic for money. The exact type set is still a design decision, but a finance-oriented language should eventually support more than `int8` and `float16`.

Useful numeric categories include:

- Fixed-width integers such as `int8`, `int16`, `int32`, and `int64`.
- Binary floating-point values such as `float16`, `float32`, and `float64`.
- Fixed-point or decimal values for prices, cash, fees, and accounting.
- Explicit rounding rules and checked numeric conversions.
- Overflow detection instead of silent wraparound in financial calculations.


## Direction: Strategy Research and Backtesting

In a research-oriented design, UPRM-Edge would prioritize readable code, rapid experiments, and safe numerical behavior. This direction is closer to Python, R, and Julia.

Possible uses include:

- Loading historical price data.
- Computing returns, volatility, and technical indicators.
- Developing factor and portfolio strategies.
- Running event-driven or vectorized backtests.
- Simulating transaction costs and slippage.
- Measuring risk with drawdown, Value at Risk, and stress tests.
- Comparing the effect of numeric precision on a strategy.

The most distinctive feature could be precision experiments. A researcher could run the same strategy with different numeric types and measure changes in speed, memory, model output, and profitability. The compiler could warn when a low-precision conversion may materially affect a calculation.

### Research-Language Trade-offs

| Advantage | Cost or Risk |
|---|---|
| Easier for students to learn and extend | Slower than optimized C++ in live execution |
| Fast strategy prototyping | A flexible runtime can make performance less predictable |
| Clear experiments with numeric precision | Results may differ across types or hardware |
| Opportunity to connect with Python libraries | Foreign-library calls weaken runtime control |
| Simpler initial interpreter implementation | Large datasets may require later optimization |
| Useful for education and reproducible research | Not automatically safe for real-money trading |

This direction is achievable in stages. The first version can interpret an abstract syntax tree, support scalar calculations, and print results. Later versions can add arrays, time-series operations, data import, backtesting, and compiled numeric kernels.

## Recommended Direction: Research First, Execution Later

The best initial direction for UPRM-Edge is a precision-aware strategy and backtesting language. It matches the current parser-focused scope and lets students contribute features related to their interests without requiring an entire production trading stack.

The language can later introduce a restricted execution subset for performance-critical code. A strategy could be researched using high-level features, while a small function marked for execution would allow only statically typed values, bounded memory, and predictable operations. That subset could eventually compile to native code.

This creates a path between the two goals:

```text
research code -> validated strategy -> restricted execution function -> native code
```

The research environment would resemble Python, R, or Julia, while the restricted subset would move toward C++-like predictability. The same precision-aware type system would connect both layers.

## Proposed Finance Features

### Numeric Safety

- Add `int16`, `int32`, `int64`, `float32`, and `float64`.
- Add a decimal or fixed-point type for money and exchange prices.
- Require explicit conversion when precision may be lost.
- Detect overflow, underflow, division by zero, and invalid values.
- Define rounding modes, especially for fees and accounting.
- Warn when two incompatible financial units are mixed.

### Strategy Development

- Arrays and time-series values.
- Date and timestamp types with explicit time zones.
- Functions for returns, moving averages, variance, and correlation.
- CSV or columnar-data import.
- Event-driven backtesting with orders, fills, positions, and cash.
- Transaction-cost, spread, latency, and slippage models.
- Deterministic random seeds for reproducible simulations.

### Performance

- Type inference without hiding precision decisions.
- Vectorized operations for time-series data.
- Optional ahead-of-time or just-in-time compilation.
- A profiler that reports runtime and memory by numeric type.
- A restricted, allocation-free mode for latency-sensitive functions.

### Reliability

- Unit-aware types such as shares, dollars, percentages, and timestamps.
- Tests that compare backtest and live-execution calculations.
- Audit logs containing strategy inputs, precision choices, and outputs.
- Compiler warnings for look-ahead bias patterns where detectable.
- Separation between research simulation and real order submission.

## Supporting Different Student Interests

The project can be divided into independent areas so students can connect the language to their own niche interests:

| Interest | Possible Contribution |
|---|---|
| Compiler design | Type checking, numeric conversions, optimization |
| Quantitative finance | Indicators, portfolio rules, and risk measures |
| Data science | Arrays, data frames, statistics, and visualization export |
| Systems/HFT | Native compilation, memory layout, networking, and benchmarking |
| Machine learning | Low-precision inference and model-signal types |
| Cybersecurity | Sandboxing, safe strategy execution, and audit trails |
| User experience | Error messages, notebooks, documentation, and debugging tools |
| Testing | Numerical edge cases, property tests, and reproducible backtests |

This modular approach gives the language one common theme—explicit and safe numerical precision—while allowing different teams to develop specialized tools.

## Proposed Research and Backtesting Language Specification

The first complete version should target research, simulation, and backtesting. It should favor reproducible results and safe arithmetic while still making large time-series operations efficient.

### Numeric Types

Type names should state their exact size. Names such as `long` vary between platforms, while `int64` always communicates the same range. Similarly, `double` should be accepted only as an optional alias for `float64`, not as the primary type name.

| Category | Proposed Types | Intended Use |
|---|---|---|
| Signed integers | `int8`, `int16`, `int32`, `int64`, `int128` | Quantities, indexes, counters, and timestamps |
| Unsigned integers | `uint8`, `uint16`, `uint32`, `uint64`, `uint128` | Nonnegative identifiers, flags, and compact data |
| Binary floating point | `float16`, `float32`, `float64` | Signals, statistics, indicators, and model calculations |
| Extended floating point | `float128` | Optional high-precision research calculations |
| Decimal | `decimal64`, `decimal128` | Prices, cash, fees, accounting, and exact base-10 rounding |
| Boolean | `bool` | Conditions and data-quality flags |

`int128`, `uint128`, and `decimal128` should have defined language behavior even if a machine implements them in software. `float128` should be optional because native support and representation differ across platforms. A program that requires an optional type must receive a clear compile-time error when the target does not support it.

Money should not default to binary floating point. `float64` is appropriate for many statistical calculations, but `decimal128` or a future fixed-point type is safer for balances, order prices, commissions, and final accounting.

Numeric literals may use a type suffix when inference would be unclear:

```uedge
let shares: int32 = 250;
let probability: float32 = 0.625f32;
let price: decimal128 = 184.12d128;
let event_time: int64 = 1712345678000;
```

The language should reject silent narrowing. A conversion from `float64` to `float32`, `int64` to `int8`, or `decimal128` to a binary float must be explicit. Integer overflow should produce an error by default rather than wrap silently.

### Value and Reference Semantics

Passing everything by reference is not necessary and could make strategy code harder to reason about. The recommended model is:

- Scalars, including numbers and booleans, pass by value.
- Small immutable records pass by value.
- Arrays, tables, time series, portfolios, and order books use references internally to avoid expensive copies.
- Function parameters are read-only by default.
- Mutation requires an explicit `ref mut` parameter.
- A plain `ref` parameter permits shared access but not mutation.

Proposed syntax:

```uedge
func mean(prices: ref Series<float64>): float64 {
    // prices can be read without copying the series
}

func apply_split(prices: ref mut Series<decimal128>, ratio: decimal128) {
    // mutation is visible to the caller
}

func position_value(price: decimal128, shares: int64): decimal128 {
    return price * shares;
}
```

This design gives large financial datasets reference efficiency while keeping ordinary calculations predictable. The compiler should reject a mutable reference when another active reference could observe the same data. An initial interpreter can enforce a simpler rule: only one `ref mut` parameter may refer to a value during a function call.

Returning references should be excluded from the first version. Functions should return values or owned collections so references cannot outlive their data. More advanced lifetime rules can be considered after the core language works.

### Collections and Financial Data

The research language should eventually include generic collections:

```uedge
Series<float64>
Series<decimal128>
Table
Matrix<float32>
Array<int64>
```

A `Series<T>` represents ordered observations with timestamps and a missing-value policy. A `Table` stores named columns that may have different types. A `Matrix<T>` supports numerical and machine-learning operations. Collections should use copy-on-write or reference-backed storage so assignment does not immediately duplicate a large dataset.

### Type Promotion Rules

Promotion must be deterministic and visible:

- Operations between the same types preserve that type.
- Smaller integers may promote to a larger integer when the conversion is lossless.
- Integer and floating-point operations produce an appropriate floating-point type only through a defined promotion rule.
- Decimal and binary floating-point values do not mix implicitly.
- Signed and unsigned integer mixing requires a safe common type or an explicit conversion.
- Comparisons may promote losslessly but must reject ambiguous or lossy comparisons.

The compiler should display the inferred result type in diagnostics. This is especially useful when a long expression changes precision.

### Initial Backtesting Model

The first backtesting engine should be deterministic and event-driven. A strategy receives historical events and returns orders; the engine controls fills, costs, and portfolio updates.

```uedge
func on_bar(context: ref mut Context, bar: ref Bar) {
    let fast: float64 = sma(context.close, 10);
    let slow: float64 = sma(context.close, 30);

    if fast > slow {
        context.order("AAPL", 100);
    }
}
```

Core backtesting types should include `Timestamp`, `Bar`, `Order`, `Fill`, `Position`, `Portfolio`, `Series<T>`, and `Context`. The engine should model commissions, bid-ask spread, slippage, and execution delay. It must prevent a strategy from reading future observations, since avoiding look-ahead bias is more important than raw execution speed in this phase.

### Version-One Scope

The first usable language version should implement:

1. Fixed-width signed integers through `int64`.
2. `float32`, `float64`, `bool`, and `decimal128`.
3. Explicit conversions and checked arithmetic.
4. Pass-by-value scalars plus `ref` and `ref mut` parameters.
5. Functions, conditions, loops, arrays, and `Series<T>`.
6. Historical bar data and a deterministic event-driven backtest.
7. Basic performance statistics and transaction-cost modeling.

Types such as `int128`, `uint128`, and `float128` can follow once the type checker and runtime are stable. They are useful, but they should not delay the smaller set needed for realistic strategy research.

## Implemented Lexer Design

The lexer in `main.py` is implemented with PLY (`ply.lex`). Its responsibility is limited to converting source text into tokens. It recognizes valid words, literals, operators, delimiters, comments, and whitespace, but it does not decide whether those tokens form a valid program.

The current source pipeline is:

```text
.uedge source -> PLY lexer -> token stream -> PLY/YACC parser -> AST
```

### Reserved Words and Types

The lexer reserves the common language keywords `let`, `func`, `if`, `else`, `while`, `for`, `return`, and `print`. It also reserves `ref` and `mut` for explicit reference parameters.

Precision types are emitted as distinct tokens rather than ordinary identifiers:

- Signed integers: `int8`, `int16`, `int32`, `int64`, and `int128`.
- Unsigned integers: `uint8`, `uint16`, `uint32`, `uint64`, and `uint128`.
- Floating point: `float16`, `float32`, `float64`, and `float128`.
- Decimal: `decimal64` and `decimal128`.
- Logical: `bool`.

The identifier rule matches a complete name before consulting the reserved-word dictionary. As a result, names such as `float16_signal`, `letter`, and `return_rate` remain identifiers instead of being split into keywords.

### Literal Tokens

The lexer converts literal text into useful Python values for the future AST:

| Source | Token | Stored Value |
|---|---|---|
| `42` | `INT_LITERAL` | Python `int` |
| `1.25`, `2e-4`, `1f32` | `FLOAT_LITERAL` | Python `float` |
| `184.12d128` | `DECIMAL_LITERAL` | Python `Decimal` |
| `true`, `false` | `BOOL_LITERAL` | Python `bool` |
| `"AAPL"` | `STRING_LITERAL` | Decoded Python `str` |

The suffix on a numeric literal communicates the requested source precision. The parser should preserve this information in the AST in a later lexer revision; converting directly to a Python `float` currently loses whether the user wrote `f16`, `f32`, or `f64`. A practical change is to store both the numeric value and optional suffix in a small literal object.

Negative numbers are deliberately tokenized as `MINUS` followed by a positive literal. This allows the parser to treat negation as a unary operator and avoids ambiguity in expressions such as `portfolio_return-1.0`.

### Operators, Delimiters, and Access

The lexer supports arithmetic (`+`, `-`, `*`, `/`, `%`), comparisons (`==`, `!=`, `<`, `>`, `<=`, `>=`), assignment (`=`), grouping, blocks, indexing, commas, semicolons, type colons, and member-access dots. These tokens are enough for scalar formulas, function calls, arrays, and expressions such as `context.portfolio.cash`.

Comments begin with `//` and continue to the end of the line. The string rule runs independently, so `"https://data.example"` remains a complete string rather than starting a comment. Spaces, tabs, and carriage returns are ignored, while newline tokens update the source line number.

### Lexer Diagnostics

Lexical failures stop processing immediately. The current command-line messages follow the expected course-test format:

```text
Error: unexpected token '$' at line 4
Error: malformed string at line 3
```

The lexer must report malformed characters and strings. Missing semicolons, closing braces, or closing parentheses are parser errors because every individual character may still be a valid token.

### Lexer Entry Points

`build_lexer()` creates a fresh PLY lexer so line-number state is not shared between files. `tokenize_source(source)` yields tokens for testing or parser input. Both `main.py` and the course-compatible `input.py` command currently run lexical validation before exiting.

## Proposed PLY/YACC Parser Structure

The parser should use `ply.yacc` and construct an abstract syntax tree rather than execute code inside grammar functions. Separating parsing from execution makes it possible to add type checking, precision analysis, backtesting, and future compilation without rewriting the grammar.

The complete front end should follow this structure:

```text
source
  -> lexer
  -> parser
  -> abstract syntax tree
  -> type and precision checker
  -> finance-specific semantic checks
  -> interpreter/backtesting engine
```

### Parser Module Layout

The first implementation may remain in `main.py` for the class project, but its sections should have clear boundaries:

1. Reserved words and token contract.
2. Lexer rules and lexical errors.
3. AST node definitions.
4. Operator precedence.
5. Common grammar productions.
6. Precision-type and reference productions.
7. Parser diagnostics and `parse_source`.
8. Command-line entry point.

If the project grows, these sections can move into `lexer.py`, `parser.py`, `ast_nodes.py`, `type_checker.py`, and `runtime.py` without changing the language syntax.

### AST Nodes

Dataclasses provide a readable first AST representation. Every node should include at least its source line so later type and runtime errors can identify their origin.

Recommended nodes include:

- `Program(statements)` and `Block(statements)`.
- `VariableDeclaration(name, declared_type, initializer)`.
- `Assignment(target, value)`.
- `FunctionDeclaration(name, parameters, return_type, body)`.
- `Parameter(name, declared_type, reference_kind)`.
- `IfStatement`, `WhileStatement`, and `ForStatement`.
- `ReturnStatement` and `PrintStatement`.
- `BinaryExpression`, `UnaryExpression`, and `GroupingExpression`.
- `Literal`, `Identifier`, `CallExpression`, `MemberAccess`, and `IndexExpression`.
- `TypeName(name, generic_arguments)`.

Finance concepts such as `Series`, `Bar`, `Order`, and `Portfolio` should initially be ordinary named types and runtime values, not special grammar nodes. This keeps the core language reusable and places domain behavior in the type checker and backtesting library.

### Program and Statement Grammar

The parser start symbol should be `program`. A program contains zero or more statements and must consume the complete token stream.

```text
program               -> statement_list
statement_list        -> statement_list statement | empty
statement             -> variable_declaration
                       | assignment_statement
                       | function_declaration
                       | if_statement
                       | while_statement
                       | for_statement
                       | return_statement
                       | print_statement
                       | expression_statement
block                 -> LBRACE statement_list RBRACE
variable_declaration  -> LET ID COLON type_specifier ASSIGN expression SEMICOLON
assignment_statement  -> assignment_target ASSIGN expression SEMICOLON
```

Version one should require a declared type and initializer on every `let`. Requiring both produces predictable precision behavior. Type inference can be added later as an explicit extension.

### Type and Reference Grammar

Types should support built-in scalar types, user-defined finance types, and generic collection types:

```text
type_specifier        -> precision_type
                       | BOOL
                       | ID
                       | ID LT type_arguments GT
type_arguments        -> type_specifier
                       | type_arguments COMMA type_specifier
parameter             -> ID COLON parameter_mode type_specifier
parameter_mode        -> REF
                       | REF MUT
                       | empty
```

This grammar accepts `price: decimal128`, `bar: ref Bar`, `context: ref mut Context`, and `prices: ref Series<float64>`. The parser records the reference mode; the semantic checker later verifies that mutation and aliasing are legal.

### Function Grammar

The proposed function syntax matches the examples already used in this design:

```text
function_declaration  -> FUNC ID LPAREN parameter_list RPAREN return_annotation block
parameter_list        -> parameters | empty
parameters            -> parameter | parameters COMMA parameter
return_annotation     -> COLON type_specifier | empty
return_statement      -> RETURN expression SEMICOLON
```

An omitted return annotation should mean no returned value in version one. Inference of function return types can be considered later. A bare `return;` will require a separate production if void functions need early exits.

### Control-Flow Grammar

Conditions should require parentheses for simple and predictable diagnostics:

```text
if_statement          -> IF LPAREN expression RPAREN block optional_else
optional_else         -> ELSE block | ELSE if_statement | empty
while_statement       -> WHILE LPAREN expression RPAREN block
for_statement         -> FOR LPAREN for_init SEMICOLON optional_expression
                         SEMICOLON optional_expression RPAREN block
```

The type checker must require `bool` conditions. A future Julia-style iteration form such as `for bar in bars` would be useful for research code, but it requires new `in` and iterator semantics and should follow the basic C-style loop.

### Expression Grammar and Precedence

PLY precedence should be declared from lowest to highest:

```python
precedence = (
    ("left", "EQ", "NE"),
    ("left", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MODULO"),
    ("right", "UMINUS"),
)
```

Expressions should support:

```text
expression             -> expression binary_operator expression
                        | MINUS expression %prec UMINUS
                        | LPAREN expression RPAREN
                        | literal
                        | ID
                        | function_call
                        | member_access
                        | index_expression
function_call          -> postfix_expression LPAREN argument_list RPAREN
member_access          -> postfix_expression DOT ID
index_expression       -> postfix_expression LBRACKET expression RBRACKET
```

Calls, member access, and indexing should bind more tightly than unary and binary operators. This is necessary for quantitative expressions such as `returns[i] * portfolio.weights[i]` and `context.order("AAPL", 100)`.

Type names followed by parentheses should parse as ordinary calls. The semantic checker can then recognize `int8(value)` or `float16(value)` as explicit casts instead of creating special cast grammar.

### Quantitative Research Semantics

The parser should remain domain-light, while the semantic and runtime layers provide Julia-like numerical behavior:

- Generic `Series<T>`, `Array<T>`, and `Matrix<T>` values.
- Element indexing and member access.
- Vectorized finance functions such as `returns`, `sma`, `variance`, and `correlation`.
- Explicit precision conversions through type-call syntax.
- Deterministic `on_bar` callbacks for event-driven backtests.
- Runtime values for `Context`, `Bar`, `Order`, `Fill`, `Position`, and `Portfolio`.
- Prevention of future-data access in the backtesting engine.

Vectorized syntax does not need a separate parser rule in version one. Library functions can operate on `Series<T>` and return new series. Julia-style broadcasting operators may be considered only after ordinary arithmetic and collection semantics are stable.

### Syntax Diagnostics

The parser must distinguish lexical and structural errors. Required course cases include:

```text
Error: expected ';' at line 3
Error: missing closing '}'
Error: missing closing ')' at line 3
```

`p_error(token)` can report a general unexpected-token error, but useful missing-delimiter messages require context. Small targeted productions such as a variable declaration missing `SEMICOLON`, or tracking unmatched opening delimiters, can produce the required diagnostics. Unexpected end-of-file should inspect unmatched delimiters before reporting a generic incomplete program.

The parser must never accept a valid prefix while ignoring trailing tokens. Successful parsing means the complete file produced one `Program` AST.

### Parser Entry Point

The final parser API should create fresh lexer and parser state for each source file:

```python
def parse_source(source: str):
    lexer = build_lexer()
    parser = yacc.yacc(start="program", write_tables=False)
    return parser.parse(source, lexer=lexer, tracking=True)
```

The command-line program should print `Parsed successfully` only after `parse_source` returns a complete AST. Lexing alone is not enough, because a token stream can still contain missing semicolons or unbalanced delimiters.

### Recommended Parser Implementation Order

1. Add AST dataclasses and `program`, `statement_list`, and `block` rules.
2. Parse literals, identifiers, grouping, unary operators, and binary operators.
3. Add typed variable declarations, assignments, and print statements.
4. Add conditions and loops with missing-delimiter diagnostics.
5. Add functions, parameters, return types, calls, `ref`, and `ref mut`.
6. Add member access, indexing, and generic collection types.
7. Add the semantic type checker and explicit precision conversions.
8. Connect the AST to a deterministic backtesting runtime.

## Suggested Development Roadmap

### Phase 1: Language Core

- Finish the lexer, parser, and abstract syntax tree.
- Implement declarations, expressions, functions, conditions, and loops.
- Define the complete numeric type set and conversion rules.
- Produce clear errors for invalid syntax and unsafe conversions.

### Phase 2: Safe Financial Arithmetic

- Add decimal or fixed-point values.
- Add checked arithmetic and configurable rounding.
- Implement basic financial units and timestamp support.
- Test boundary values and precision-loss cases.

### Phase 3: Research and Backtesting

- Add arrays, time series, historical-data loading, and statistics.
- Build a small event-driven backtesting engine.
- Model fees, spread, slippage, and latency.
- Generate performance and risk reports.

### Phase 4: Optimization

- Benchmark numeric operations and larger strategies.
- Add vectorization or compiled numeric functions.
- Create tools for comparing precision, speed, and memory use.
- Define a restricted execution-safe subset.

### Phase 5: Experimental Live Execution

- Compile restricted functions to native code.
- Add deterministic memory and concurrency rules.
- Integrate a simulated exchange before any real broker connection.
- Require strict risk limits, testing, and audit logging.

## Main Design Principle

Precision should communicate intent, not merely save memory. UPRM-Edge should help programmers answer three questions for every important calculation:

1. How accurate must this value be?
2. What performance cost is acceptable?
3. What should happen if the value cannot be represented safely?

For an academic project, a precision-aware research and backtesting language provides the strongest balance of originality, usefulness, and achievable scope. HFT can remain a motivating long-term target, supported through a smaller compiled subset after the language has reliable numeric semantics.
