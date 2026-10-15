# PL-Project
new precision-aware language 

Run the command-line entry point with exactly one source file:

```sh
python main.py program.uedge
```

The entry point reads the supplied file without prompting. Missing or extra
arguments and unreadable files produce an error and a nonzero exit status.
`main.py` contains a collaboration template with owner blanks and TODO sections
for tokens, the lexer, the common-core PLY.yacc grammar, precision-aware syntax,
AST/errors, and validation. Only command-line file loading is implemented;
a successful exit currently means the file was read, not that its syntax is valid.
