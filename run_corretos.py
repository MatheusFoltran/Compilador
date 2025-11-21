#!/usr/bin/env python3
import glob
import sys
from parser import make_parser, TokenTracker
from lexer import lexer
from interpreter import analyze_semantics


def run():
    files = sorted(glob.glob('teste/correto*.ras'))
    if not files:
        print('Nenhum arquivo correto encontrado em teste/ (padrao correto*.ras)')
        return 2

    results = []
    for path in files:
        print('\n' + '=' * 80)
        print(f'TESTANDO: {path}')
        print('=' * 80)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
        except Exception as e:
            print(f'ERRO ao abrir {path}: {e}')
            results.append((path, False, 'open'))
            continue

        tracked = TokenTracker(lexer)
        parser = make_parser()
        resultado = parser.parse(data, lexer=tracked)

        if resultado is None:
            print('\nPARSING FALHOU - nao foi possivel construir AST')
            results.append((path, False, 'parse'))
            continue

        print('\nParsing OK')
        print('\nIniciando analise semantica...')
        ok = analyze_semantics(resultado)
        results.append((path, ok, 'semantics' if ok else 'errors'))

    print('\n' + '=' * 80)
    print('RESUMO DOS TESTES')
    print('=' * 80)
    all_ok = True
    for path, ok, why in results:
        status = 'PASS' if ok else 'FAIL'
        print(f'{status} - {path} ({why})')
        if not ok:
            all_ok = False

    print('=' * 80)
    return 0 if all_ok else 1


if __name__ == '__main__':
    rc = run()
    sys.exit(rc)
