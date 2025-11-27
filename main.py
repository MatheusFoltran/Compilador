import sys
from pathlib import Path

import parser
from parser import make_parser, TokenTracker
import importlib
import ply.lex as _plylex
import lexer as lexer_module
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

    # --- fase léxica: listar tokens (tokenizar apenas UMA vez) ---
    print("\n--- Tokens ---")
    # Usar um lexer independente apenas para listagem de tokens (sem afetar parser)
    list_lex = _plylex.lex(module=lexer_module)
    tk_list = TokenTracker(list_lex)
    tk_list.input(text)
    while True:
        tok = tk_list.token()
        if not tok:
            break
        tokens.append(tok)
        print(f"{tok.type:<12} {tok.value!r:<12} (linha {tok.lineno})")

    # --- fase sintática ---
    print("\n--- Parser ---")
    # Criar um lexer separado para o parser, garantindo estado limpo
    parse_lex = _plylex.lex(module=lexer_module)
    tk_parse = TokenTracker(parse_lex)
    tk_parse.input(text)
    parser_obj = make_parser()
    try:
        ast = parser_obj.parse(text, lexer=tk_parse)
    except Exception as e:
        print(f"Erro de parsing: {e}")
        return False

    if not ast:
        print("Parsing nao produziu AST")
        return False

    # Se houve erro(s) sintáticos reportados pelo parser, não rodar
    # a análise semântica para evitar mensagens em cascata.
    if getattr(parser, 'error_count', 0) > 0:
        print(f"ANÁLISE SINTÁTICA COMPLETADA COM {parser.error_count} ERRO(S). Pulando análise semântica.")
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
    # imprimir tabela de símbolos independentemente do resultado
    print("\n--- Tabela de Simbolos ---")
    try:
        analyzer.print_symbol_table()
    except Exception as e:
        print(f"Erro ao imprimir tabela de simbolos: {e}")

    # Erro não é mais tratado aqui
    # if not ok:
    #     print(f"Analise semantica falhou para {path}")
    #     return False

    # --- gerar pasta de saída e geracao MEPA ---
    out_dir = Path('output_main')
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / (path.stem + '.mepa')
    try:
        mp = emit_mepa_file(ast, analyzer.symbol_table, str(out_path), analyzer=analyzer)
    except Exception as e:
        print(f"Erro ao gerar MEPA: {e}")
        return False

    print(f"MEPA gerado: {out_path} ({len(mp)} linhas)")
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
