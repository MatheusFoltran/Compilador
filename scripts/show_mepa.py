#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer
from mepa_codegen import emit_mepa_file

INPUT = Path('input') / 'correto01.ras'

if not INPUT.exists():
    print(f"Arquivo de exemplo não encontrado: {INPUT}")
    sys.exit(1)

text = INPUT.read_text(encoding='utf-8')

# lex + parse
tracked = TokenTracker(lexer)
tracked.input(text)
parser = make_parser()
ast = parser.parse(text, lexer=tracked)
if ast is None:
    print('Parser retornou None')
    sys.exit(1)

# semantic
an = SemanticAnalyzer()
ok = an.analyze(ast)
if not ok:
    print('Análise semântica falhou')
    sys.exit(1)

out_path = Path('out_program.mepa')
mp = emit_mepa_file(ast, an.symbol_table, str(out_path))

print('# MEPA gerado:')
for i, line in enumerate(mp):
    print(f"{i:03}: {line}")

print('\n# Arquivo escrito em:', out_path)
