#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import SemanticAnalyzer
from mepa_codegen import emit_mepa_file

# Processa todos os arquivos input/correto*.ras e escreve em output_mepa/
IN_DIR = Path('input')
GLOB = 'correto*.ras'
OUT_DIR = Path('output_mepa')
OUT_DIR.mkdir(exist_ok=True)

files = sorted(IN_DIR.glob(GLOB))
if not files:
    print(f"Nenhum arquivo encontrado em {IN_DIR}/{GLOB}")
    sys.exit(0)

summary = []
for src in files:
    print(f"Processando: {src}")
    text = src.read_text(encoding='utf-8')

    # lex + parse
    tracked = TokenTracker(lexer)
    tracked.input(text)
    parser = make_parser()
    try:
        ast = parser.parse(text, lexer=tracked)
    except Exception as e:
        print(f"Erro ao parsear {src}: {e}")
        summary.append((src.name, 'parse-error'))
        continue
    if ast is None:
        print(f"Parser retornou None para {src}")
        summary.append((src.name, 'no-ast'))
        continue

    # semantic
    an = SemanticAnalyzer()
    ok = an.analyze(ast)
    if not ok:
        print(f"Análise semântica falhou para {src}")
        summary.append((src.name, 'semantic-error'))
        continue

    out_path = OUT_DIR / (src.stem + '.mepa')
    mp = emit_mepa_file(ast, an.symbol_table, str(out_path))

    # escrever saída compacta no console
    print(f"  -> escrito: {out_path} ({len(mp)} linhas)")
    summary.append((src.name, 'ok', len(mp)))

print('\nResumo:')
for item in summary:
    print(' -', item)

print('\nArquivos gerados em:', OUT_DIR)
