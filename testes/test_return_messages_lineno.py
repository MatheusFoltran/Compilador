from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer


def test_return_error_includes_lineno():
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

    tracked = TokenTracker(lexer)
    tracked.input(src)
    parser = make_parser()
    ast = parser.parse(src, lexer=tracked)
    assert ast is not None

    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    assert not ok, "Esperava erro semântico por caminhos sem retorno"

    msgs = [m for m in analyzer.errors if 'atribuições encontradas nas linhas' in m]
    assert msgs, f"Esperava mensagem com linhas de atribuição, mensagens: {analyzer.errors}"
    # Verifica que a mensagem contenha pelo menos um dígito (número de linha)
    assert any(ch.isdigit() for ch in msgs[0])
