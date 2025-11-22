from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import analyze_semantics


def parse_and_analyze(src):
    tracked = TokenTracker(lexer)
    tracked.input(src)
    parser = make_parser()
    ast = parser.parse(src, lexer=tracked)
    assert ast is not None
    return analyze_semantics(ast)


def test_if_else_returns_ok():
    src = (
        "program P;\n"
        "function f(a: integer): integer;\n"
        "begin\n"
        "  if a > 0 then\n"
        "    f := 1\n"
        "  else\n"
        "    f := 2\n"
        "end;\n"
        "begin\n"
        "  write(0)\n"
        "end.\n"
    )

    assert parse_and_analyze(src)


def test_if_without_else_fails():
    src = (
        "program P;\n"
        "function f(a: integer): integer;\n"
        "begin\n"
        "  if a > 0 then\n"
        "    f := 1\n"
        "end;\n"
        "begin\n"
        "  write(0)\n"
        "end.\n"
    )

    assert not parse_and_analyze(src)


def test_sequential_multiple_assignments_fails():
    src = (
        "program P;\n"
        "function f(): integer;\n"
        "begin\n"
        "  f := 1;\n"
        "  f := 2\n"
        "end;\n"
        "begin\n"
        "  write(0)\n"
        "end.\n"
    )

    assert not parse_and_analyze(src)


def test_while_assignment_fails():
    src = (
        "program P;\n"
        "function f(n: integer): integer;\n"
        "begin\n"
        "  while n > 0 do\n"
        "    f := 1\n"
        "end;\n"
        "begin\n"
        "  write(0)\n"
        "end.\n"
    )

    assert not parse_and_analyze(src)


def test_nested_if_returns_ok():
    src = (
        "program P;\n"
        "function f(a,b: integer): integer;\n"
        "begin\n"
        "  if a > b then\n"
        "    if a > 0 then\n"
        "      f := 1\n"
        "    else\n"
        "      f := 2\n"
        "  else\n"
        "    f := 3\n"
        "end;\n"
        "begin\n"
        "  write(0)\n"
        "end.\n"
    )

    assert parse_and_analyze(src)
