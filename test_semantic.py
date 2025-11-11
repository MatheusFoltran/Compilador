#!/usr/bin/env python3
"""
Script para testar o analisador semântico
"""

import sys
from parser_erros import make_parser
from lexer import lexer
from interpreter import analyze_semantics

def test_file(filename):
    """Testa análise semântica de um arquivo"""
    print("=" * 80)
    print(f"TESTANDO: {filename}")
    print("=" * 80)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Erro: arquivo '{filename}' não encontrado.")
        return False
    
    # Parser
    parser = make_parser()
    resultado = parser.parse(data, lexer=lexer)
    
    if resultado is None:
        print("\n❌ Erro no parsing - não é possível fazer análise semântica")
        return False
    
    print("\n✅ Parsing bem-sucedido!")
    
    # Análise semântica
    print("\n" + "─" * 80)
    print("INICIANDO ANÁLISE SEMÂNTICA")
    print("─" * 80)
    
    success = analyze_semantics(resultado)
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ANÁLISE SEMÂNTICA CONCLUÍDA SEM ERROS")
    else:
        print("❌ ANÁLISE SEMÂNTICA CONCLUÍDA COM ERROS")
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_file(sys.argv[1])
    else:
        # Testar todos os arquivos semânticos
        test_files = [
            'teste/semantico01.ras',
            'teste/semantico02.ras',
            'teste/semantico03.ras',
        ]
        
        print("\n🔬 SUITE DE TESTES SEMÂNTICOS\n")
        
        results = []
        for test_file_name in test_files:
            result = test_file(test_file_name)
            results.append((test_file_name, result))
            print("\n\n")
        
        # Resumo
        print("\n" + "=" * 80)
        print("RESUMO DOS TESTES")
        print("=" * 80)
        for filename, success in results:
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"{status} - {filename}")
        print("=" * 80)
