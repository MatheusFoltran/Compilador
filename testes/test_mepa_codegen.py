import io
from pathlib import Path
import pytest

from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer
from mepa_codegen import emit_mepa_file

import mepa.mepa_defs as mepa_defs
import mepa.mepa_interp as mepa_interp


EXAMPLE = Path('input') / 'correto01.ras'


def test_compile_and_run_example(tmp_path):
    if not EXAMPLE.exists():
        pytest.skip("No input/correto01.ras example available")

    data = EXAMPLE.read_text(encoding='utf-8')

    # Lex & parse
    tracked = TokenTracker(lexer)
    tracked.input(data)
    try:
        while tracked.token():
            pass
    except Exception as exc:
        pytest.fail(f"Falha léxica ao tokenizar {EXAMPLE}: {exc}")

    tracked.input(data)
    parser = make_parser()
    ast = parser.parse(data, lexer=tracked)
    assert ast is not None

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    assert ok

    # Emit MEPA assembly to file
    out_path = tmp_path / 'program.mepa'
    emit_mepa_file(ast, analyzer.symbol_table, str(out_path))

    # Run MEPA interpreter on emitted file
    with open(out_path, 'r', encoding='utf-8') as prog_file:
        mepa_defs.PROG_FILE = prog_file
        P, L = mepa_defs.inputProgram()
        mepa_defs.fixArgs(P, L)
        MP = mepa_defs.makeMepa(P)

    msfile = io.StringIO()
    infile = io.StringIO('0\n' * 32)
    outfile = io.StringIO()

    # execute deve retornar -1 quando o programa termina normalmente
    res = mepa_interp.execute(MP, P, L, msfile, infile, outfile)
    assert res == -1
