import sys
from pathlib import Path

from lexer import lexer
from parser import make_parser, TokenTracker
from interpreter import SemanticAnalyzer
from mepa_codegen import emit_mepa_file
from ast_nodes import write_ast_verbose
from pathlib import Path
import os


def process_file(path: Path) -> bool:
    """Processa um arquivo: lex, parse, semantic e gera .mepa.
    Retorna True se tudo OK, False caso contrário.
    """
    print(f"\n=== Processando: {path} ===")

    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"Erro: arquivo '{path}' nao encontrado")
        return False

    # --- fase léxica: listar tokens (usar lexer rastreado para não perder o stream) ---
    print("\n--- Tokens ---")
    tk = TokenTracker(lexer)
    tk.input(text)
    while True:
        tok = tk.token()
        if not tok:
            break
        print(f"{tok.type:<12} {tok.value!r:<12} (linha {tok.lineno})")

    # --- fase sintática ---
    print("\n--- Parser ---")
    tracked = TokenTracker(lexer)
    tracked.input(text)
    parser = make_parser()
    try:
        ast = parser.parse(text, lexer=tracked)
    except Exception as e:
        print(f"Erro de parsing: {e}")
        return False

    if not ast:
        print("Parsing nao produziu AST")
        return False

    print("\n--- AST (verbose) ---")
    try:
        write_ast_verbose(ast)
    except Exception:
        # fallback: simple print
        print(ast)

    # --- análise semântica ---
    print("\n--- Analise semantica ---")
    analyzer = SemanticAnalyzer()
    ok = analyzer.analyze(ast)
    if not ok:
        print(f"Analise semantica falhou para {path}")
        return False

    # --- gerar pasta de saída e geracao MEPA ---
    out_dir = Path('output_main')
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / (path.stem + '.mepa')
    try:
        mp = emit_mepa_file(ast, analyzer.symbol_table, str(out_path))
    except Exception as e:
        print(f"Erro ao gerar MEPA: {e}")
        return False

    print(f"MEPA gerado: {out_path} ({len(mp)} linhas)")

    # imprimir tabela de simbolos
    print("\n--- Tabela de Simbolos ---")
    try:
        analyzer.print_symbol_table()
    except Exception as e:
        print(f"Erro ao imprimir tabela de simbolos: {e}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo1.ras> [<arquivo2.ras> ...]")
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    overall_ok = True
    for p in paths:
        ok = process_file(p)
        overall_ok = overall_ok and ok

    sys.exit(0 if overall_ok else 1)


if __name__ == '__main__':
    main()
