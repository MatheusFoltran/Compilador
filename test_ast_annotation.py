#!/usr/bin/env python3
"""
Script para testar a anotação da AST durante a análise semântica
"""

import sys
from parser_erros import make_parser
from interpreter import analyze_semantics

def print_ast_annotations(node, indent=0):
    """Imprime recursivamente as anotações da AST"""
    prefix = "  " * indent
    node_type = type(node).__name__
    
    # Imprimir informações do nó
    print(f"{prefix}{node_type}:", end="")
    
    # Verificar anotações específicas por tipo de nó
    annotations = []
    
    if hasattr(node, 'tipo') and node.tipo is not None:
        annotations.append(f"tipo={node.tipo}")
    if hasattr(node, 'scope_level') and node.scope_level is not None:
        annotations.append(f"scope_level={node.scope_level}")
    if hasattr(node, 'result_type') and node.result_type is not None:
        annotations.append(f"result_type={node.result_type}")
    if hasattr(node, 'var_type') and node.var_type is not None:
        annotations.append(f"var_type={node.var_type}")
    if hasattr(node, 'var_scope_level') and node.var_scope_level is not None:
        annotations.append(f"var_scope_level={node.var_scope_level}")
    if hasattr(node, 'return_type') and node.return_type is not None:
        annotations.append(f"return_type={node.return_type}")
    if hasattr(node, 'param_types') and node.param_types is not None:
        annotations.append(f"param_types={node.param_types}")
    if hasattr(node, 'cond_type') and node.cond_type is not None:
        annotations.append(f"cond_type={node.cond_type}")
    if hasattr(node, 'expr_types') and node.expr_types is not None:
        annotations.append(f"expr_types={node.expr_types}")
    if hasattr(node, 'var_types') and node.var_types is not None:
        annotations.append(f"var_types={node.var_types}")
    
    if annotations:
        print(f" [{', '.join(annotations)}]")
    else:
        print()
    
    # Recursivamente visitar filhos
    if hasattr(node, '__dict__'):
        for attr_name, attr_value in node.__dict__.items():
            if attr_name.startswith('_'):
                continue
            
            if isinstance(attr_value, list):
                for item in attr_value:
                    if hasattr(item, '__dict__'):
                        print_ast_annotations(item, indent + 1)
            elif hasattr(attr_value, '__dict__') and not isinstance(attr_value, str):
                print_ast_annotations(attr_value, indent + 1)


def test_file(filename):
    """Testa análise semântica e mostra anotações da AST"""
    print("=" * 80)
    print(f"TESTANDO ANOTAÇÃO DA AST: {filename}")
    print("=" * 80)
    
    try:
        # Ler arquivo
        with open(filename, 'r', encoding='utf-8') as f:
            codigo = f.read()
        
        # Parser
        parser = make_parser()
        ast = parser.parse(codigo)
        
        if not ast:
            print("❌ Erro no parsing")
            return False
        
        print("\n✅ Parsing bem-sucedido!")
        
        # Análise semântica (que anota a AST)
        print("\n" + "─" * 80)
        print("EXECUTANDO ANÁLISE SEMÂNTICA (com anotação da AST)")
        print("─" * 80 + "\n")
        
        success = analyze_semantics(ast)
        
        if not success:
            print("\n❌ ERROS SEMÂNTICOS ENCONTRADOS")
            return False
        
        print("✅ Análise semântica concluída sem erros")
        
        # Mostrar anotações da AST
        print("\n" + "=" * 80)
        print("ANOTAÇÕES NA AST")
        print("=" * 80 + "\n")
        
        print_ast_annotations(ast)
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {filename}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python test_ast_annotation.py <arquivo.ras>")
        sys.exit(1)
    
    filename = sys.argv[1]
    success = test_file(filename)
    sys.exit(0 if success else 1)
