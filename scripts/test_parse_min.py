import sys
from pathlib import Path
# garantir que o diretório do projeto esteja no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parser import make_parser, TokenTracker
from lexer import lexer

samples = [
    "program p; var x : integer; begin end.",
    "program p; begin x := 1; end.",
    "program p; var x : integer; begin x := 1; end."
]

for s in samples:
    print('\n--- TEST ---')
    print(s)
    tk = TokenTracker(lexer)
    tk.input(s)
    parser = make_parser()
    ast = parser.parse(s, lexer=tk)
    print('AST:', ast)

print('\n--- TEST FILE input/sintatico07.ras ---')
with open('input/sintatico07.ras', 'r', encoding='utf-8') as f:
    data = f.read()
    print('\n-- Emulando main.py: listagem de tokens antes do parse --')
    tk = TokenTracker(lexer)
    tk.input(data)
    # listar tokens (consumir)
    while True:
        tok = tk.token()
        if not tok:
            break
        print(tok)
    # re-input e parse (igual ao main.py)
    tk.input(data)
    parser = make_parser()
    ast = parser.parse(data, lexer=tk)
    print('AST for file (after listing):', ast)
