from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer


def test_duplicate_variable_declaration_warns():
    data = (
        "program P;\n"
        "var x: integer;\n"
        "    x: integer;\n"
        "begin\n"
        "    x := 1;\n"
        "end.\n"
    )

    tracked = TokenTracker(lexer)
    tracked.input(data)
    parser = make_parser()
    ast = parser.parse(data, lexer=tracked)
    assert ast is not None

    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    # análise deve passar (não é erro), mas deve registrar um alerta
    assert ok
    assert any('nova declaração ignorada' in w or 'já foi declarada' in w for w in analyzer.warnings)


def test_duplicate_procedure_declaration_warns():
    data = (
        "program P;\n"
        "procedure p;\n"
        "begin\n"
        "    write(0);\n"
        "end;\n"
        "procedure p;\n"
        "begin\n"
        "    write(0);\n"
        "end;\n"
        "begin\n"
        "    write(0);\n"
        "end.\n"
    )

    tracked = TokenTracker(lexer)
    tracked.input(data)
    parser = make_parser()
    ast = parser.parse(data, lexer=tracked)
    assert ast is not None

    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    # análise deve passar mas deve haver alerta sobre duplicidade
    assert ok
    assert any('nova declaração ignorada' in w or 'já foi declarada' in w for w in analyzer.warnings)
