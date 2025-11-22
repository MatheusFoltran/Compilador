from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer, ProgramSymbol


def test_program_symbol_present():
    """Verifica que o identificador do programa é declarado como ProgramSymbol."""
    with open('input/correto01.ras', 'r', encoding='utf-8') as f:
        data = f.read()

    tracked = TokenTracker(lexer)
    tracked.input(data)
    parser = make_parser()
    ast = parser.parse(data, lexer=tracked)
    assert ast is not None

    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    assert ok

    # programa declarado no escopo global
    assert analyzer.symbol_table.exists(ast.name)
    sym = analyzer.symbol_table.lookup(ast.name)
    assert isinstance(sym, ProgramSymbol)
    assert sym.category == 'program'
