import glob
from pathlib import Path
import pytest

from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import analyze_semantics


# Discover files under input/ (user uses `input/` for test examples)
FILES = sorted(str(p) for p in Path('input').glob('correto*.ras'))

if not FILES:
    # If there are no example files, create a skipped test so suite doesn't fail
    def test_no_correct_examples():
        pytest.skip("No input/correto*.ras files found")


@pytest.mark.parametrize('path', FILES)
def test_correct_example_full_pipeline(path):
    """Lex -> Parse -> Semantic for each input/correto*.ras file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()

    # 1) Lexical pass: ensure tokenization completes without raising
    tracked = TokenTracker(lexer)
    tracked.input(data)
    try:
        while True:
            tok = tracked.token()
            if not tok:
                break
    except Exception as e:
        pytest.fail(f"Lexical analysis failed for {path}: {e}")

    # Reset tracked lexer input before parsing
    tracked.input(data)

    # 2) Parsing
    parser = make_parser()
    try:
        ast = parser.parse(data, lexer=tracked)
    except Exception as e:
        pytest.fail(f"Parsing raised exception for {path}: {e}")

    assert ast is not None, f"Parsing produced no AST for {path}"

    # 3) Semantic analysis
    ok = analyze_semantics(ast)
    assert ok, f"Semantic analysis failed for {path}"
