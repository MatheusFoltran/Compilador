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


def test_read_variable_ok():
    src = (
        "program P;\n"
        "var x: integer;\n"
        "begin\n"
        "  read(x)\n"
        "end.\n"
    )

    assert parse_and_analyze(src)


def test_read_proc_fails():
    src = (
        "program P;\n"
        "procedure p;\n"
        "begin\n"
        "  write(0)\n"
        "end;\n"
        "begin\n"
        "  read(p)\n"
        "end.\n"
    )

    assert not parse_and_analyze(src)


def test_read_func_fails():
    src = (
        "program P;\n"
        "function f(): integer;\n"
        "begin\n"
        "  f := 1\n"
        "end;\n"
        "begin\n"
        "  read(f)\n"
        "end.\n"
    )

    assert not parse_and_analyze(src)


def test_read_undeclared_fails():
    src = (
        "program P;\n"
        "begin\n"
        "  read(y)\n"
        "end.\n"
    )

    assert not parse_and_analyze(src)
