"""
Analisador Semântico para Rascal
- Verifica declaração de variáveis
- Verifica tipos
- Detecta erros semânticos
"""

import sys
from ast_nodes import *

class SemanticError(Exception):
    """Exceção para erros semânticos"""
    pass

class SymbolTable:
    """Tabela de símbolos para armazenar variáveis e seus tipos"""
    
    def __init__(self):
        self.symbols = {}  # {nome: tipo}
    
    def declare(self, name, tipo):
        """Declara uma variável"""
        if name in self.symbols:
            raise SemanticError(f"Variável '{name}' já foi declarada")
        self.symbols[name] = tipo
    
    def lookup(self, name):
        """Busca uma variável na tabela"""
        if name not in self.symbols:
            raise SemanticError(f"Variável '{name}' não foi declarada")
        return self.symbols[name]
    
    def exists(self, name):
        """Verifica se uma variável existe"""
        return name in self.symbols
    
    def __repr__(self):
        return f"SymbolTable({self.symbols})"


class SemanticAnalyzer:
    """Analisador semântico - percorre a AST verificando regras semânticas"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.has_errors = False
    
    def error(self, message):
        """Registra um erro semântico"""
        self.errors.append(f"ERRO SEMÂNTICO: {message}")
        self.has_errors = True
        print(f"ERRO SEMÂNTICO: {message}")
    
    def analyze(self, node):
        """Inicia a análise semântica"""
        try:
            self.visit(node)
            return not self.has_errors
        except SemanticError as e:
            self.error(str(e))
            return False
    
    def visit(self, node):
        """Despacha para o método apropriado baseado no tipo do nó"""
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node):
        """Método genérico para nós não tratados"""
        raise Exception(f"Nenhum método visit_{type(node).__name__} definido")
    
    # ========== VISITADORES ==========
    
    def visit_Program(self, node):
        """Visita o nó Program"""
        print(f"\n→ Analisando programa '{node.name}'...")
        self.visit(node.block)
    
    def visit_Block(self, node):
        """Visita o nó Block"""
        # 1. Processar declarações de variáveis
        for var_decl in node.var_decls:
            self.visit(var_decl)
        
        # 2. Processar declarações de subrotinas (futuro)
        # for subr in node.subr_decls:
        #     self.visit(subr)
        
        # 3. Processar comando composto
        self.visit(node.compound)
    
    def visit_VarDecl(self, node):
        """Visita o nó VarDecl - declara variáveis na tabela"""
        for var_name in node.ids:
            try:
                self.symbol_table.declare(var_name, node.tipo)
                print(f"  ✓ Variável '{var_name}' declarada como {node.tipo}")
            except SemanticError as e:
                self.error(str(e))
    
    def visit_Compound(self, node):
        """Visita o nó Compound - processa lista de comandos"""
        for cmd in node.commands:
            self.visit(cmd)
    
    def visit_Assign(self, node):
        """Visita o nó Assign - verifica atribuição"""
        # Verificar se variável foi declarada
        if not self.symbol_table.exists(node.id):
            self.error(f"Variável '{node.id}' não foi declarada")
            return
        
        # Obter tipo da variável
        var_type = self.symbol_table.lookup(node.id)
        
        # Verificar tipo da expressão
        expr_type = self.visit(node.expr)
        
        # Verificar compatibilidade
        if expr_type != var_type:
            self.error(f"Atribuição incompatível: '{node.id}' é {var_type}, "
                      f"mas expressão é {expr_type}")
    
    def visit_Write(self, node):
        """Visita o nó Write - verifica escrita"""
        for expr in node.exprs:
            self.visit(expr)
    
    def visit_Read(self, node):
        """Visita o nó Read - verifica leitura"""
        for var_name in node.ids:
            if not self.symbol_table.exists(var_name):
                self.error(f"Tentativa de ler variável não declarada '{var_name}'")
    
    def visit_If(self, node):
        """Visita o nó If - verifica condicional"""
        # Condição deve ser booleana
        cond_type = self.visit(node.cond)
        if cond_type != 'boolean':
            self.error(f"Condição do 'if' deve ser boolean, mas é {cond_type}")
        
        # Visitar comandos
        self.visit(node.then_cmd)
        if node.else_cmd:
            self.visit(node.else_cmd)
    
    def visit_While(self, node):
        """Visita o nó While - verifica repetição"""
        # Condição deve ser booleana
        cond_type = self.visit(node.cond)
        if cond_type != 'boolean':
            self.error(f"Condição do 'while' deve ser boolean, mas é {cond_type}")
        
        # Visitar corpo
        self.visit(node.body)
    
    def visit_ProcCall(self, node):
        """Visita o nó ProcCall - verifica chamada de procedimento"""
        # Por enquanto, apenas visita argumentos
        for arg in node.args:
            self.visit(arg)
    
    def visit_BinOp(self, node):
        """Visita o nó BinOp - verifica operação binária"""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        # Operadores aritméticos: +, -, *, div
        if node.op in ['+', '-', '*', 'div']:
            if left_type != 'integer' or right_type != 'integer':
                self.error(f"Operador '{node.op}' requer operandos integer, "
                          f"mas recebeu {left_type} e {right_type}")
            return 'integer'
        
        # Operadores relacionais: =, <>, <, <=, >, >=
        elif node.op in ['=', '<>', '<', '<=', '>', '>=']:
            if left_type != right_type:
                self.error(f"Operador '{node.op}' requer operandos do mesmo tipo, "
                          f"mas recebeu {left_type} e {right_type}")
            return 'boolean'
        
        # Operadores lógicos: and, or
        elif node.op in ['and', 'or']:
            if left_type != 'boolean' or right_type != 'boolean':
                self.error(f"Operador '{node.op}' requer operandos boolean, "
                          f"mas recebeu {left_type} e {right_type}")
            return 'boolean'
        
        else:
            self.error(f"Operador desconhecido: '{node.op}'")
            return 'unknown'
    
    def visit_UnOp(self, node):
        """Visita o nó UnOp - verifica operação unária"""
        expr_type = self.visit(node.expr)
        
        if node.op == '-':
            # Menos unário requer integer
            if expr_type != 'integer':
                self.error(f"Operador unário '-' requer operando integer, "
                          f"mas recebeu {expr_type}")
            return 'integer'
        
        elif node.op == 'not':
            # Not requer boolean
            if expr_type != 'boolean':
                self.error(f"Operador 'not' requer operando boolean, "
                          f"mas recebeu {expr_type}")
            return 'boolean'
        
        else:
            self.error(f"Operador unário desconhecido: '{node.op}'")
            return 'unknown'
    
    def visit_Var(self, node):
        """Visita o nó Var - retorna tipo da variável"""
        if not self.symbol_table.exists(node.name):
            self.error(f"Variável '{node.name}' não foi declarada")
            return 'unknown'
        return self.symbol_table.lookup(node.name)
    
    def visit_Num(self, node):
        """Visita o nó Num - retorna tipo integer"""
        return 'integer'
    
    def visit_Bool(self, node):
        """Visita o nó Bool - retorna tipo boolean"""
        return 'boolean'
    
    def visit_FuncCall(self, node):
        """Visita o nó FuncCall - verifica chamada de função"""
        # Por enquanto, apenas visita argumentos
        for arg in node.args:
            self.visit(arg)
        # Retornar tipo desconhecido (funções serão implementadas depois)
        return 'unknown'
    
    def print_symbol_table(self):
        """Imprime a tabela de símbolos"""
        print("\n" + "=" * 60)
        print("TABELA DE SÍMBOLOS")
        print("=" * 60)
        if self.symbol_table.symbols:
            for name, tipo in sorted(self.symbol_table.symbols.items()):
                print(f"  {name:15} : {tipo}")
        else:
            print("  (vazia)")
        print("=" * 60)


def analyze_semantics(ast_root):
    """Função principal para análise semântica"""
    analyzer = SemanticAnalyzer()
    success = analyzer.analyze(ast_root)
    analyzer.print_symbol_table()
    return success


# Teste do analisador semântico
if __name__ == '__main__':
    print("Analisador semântico - use o parser.py para testar")