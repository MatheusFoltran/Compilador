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


def test_relational_integers_ok():
    src = (
        "program P;\n"
        "var x: boolean;\n"
        "begin\n"
        "  x := (1 < 2);\n"
        "  write(0)\n"
        "end.\n"
    )
    assert parse_and_analyze(src)


def test_relational_with_booleans_fails():
    src = (
        "program P;\n"
        "var x: boolean;\n"
        "begin\n"
        "  x := (true < false);\n"
        "  write(0)\n"
        "end.\n"
    )
    assert not parse_and_analyze(src)


def test_equality_different_types_fails():
    src = (
        "program P;\n"
        "var x: boolean;\n"
        "begin\n"
        "  x := (1 = true);\n"
        "  write(0)\n"
        "end.\n"
    )
    assert not parse_and_analyze(src)


def test_equality_same_type_ok():
    src = (
        "program P;\n"
        "var x: boolean; y: boolean;\n"
        "begin\n"
        "  x := (true = false);\n"
        "  y := (1 = 2);\n"
        "  write(0)\n"
        "end.\n"
    )
    # Note: second assignment compares integers; its result is boolean assigned to y (ok)
    assert parse_and_analyze(src)
