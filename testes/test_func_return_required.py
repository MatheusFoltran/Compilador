from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer


def test_function_without_return_is_error():
    """Função que não atribui ao próprio identificador deve gerar erro semântico."""
    data = (
        "program P;\n"
        "function f: integer;\n"
        "var\n"
        "    x: integer;\n"
        "begin\n"
        "    x := 1\n"
        "end;\n"
        "begin\n"
        "    write(1)\n"
        "end.\n"
    )

    tracked = TokenTracker(lexer)
    tracked.input(data)
    parser = make_parser()
    ast = parser.parse(data, lexer=tracked)
    assert ast is not None

    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    assert not ok, "Esperava erro sem retorno da função"
    assert any('nao retorna valor' in msg for msg in analyzer.errors)
