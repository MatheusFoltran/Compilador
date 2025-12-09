import glob
import pytest
from pathlib import Path
from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import analyze_semantics


def _data_files(pattern: str):
    base = Path(__file__).resolve().parent.parent / 'input'
    return sorted(map(str, base.glob(pattern)))


@pytest.mark.parametrize('path', _data_files('correto*.ras'))
def test_ast_annotation_for_correct_files(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()

    tracked = TokenTracker(lexer)
    parser = make_parser()
    ast = parser.parse(data, lexer=tracked)
    assert ast is not None, f"Parsing failed for {path}"

    # Semantically-correct files should finish analysis successfully
    ok = analyze_semantics(ast)
    assert ok, f"Semantic analysis failed for {path}"
