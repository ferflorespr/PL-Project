# PL-Project
new precision-aware language 

Run the command-line entry point with exactly one source file:

```sh
python main.py program.uedge
```

The course-grader-compatible entry point is also available:

```sh
python3 input.py program.uedge
```

Install the lexer dependency with:

```sh
python3 -m pip install -r requirements.txt
```

The entry point reads and tokenizes the supplied file without prompting.
Missing or extra arguments, unreadable files, and lexical errors produce a
nonzero exit status. Parsing and syntax validation are still under development.
