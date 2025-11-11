"""
Analisador Semântico para Rascal
- Verifica declaração de variáveis, procedures e functions
- Verifica tipos e compatibilidade
- Implementa controle de escopo estático (léxico)
- Detecta erros semânticos

Estrutura da Tabela de Símbolos:
- Hash table (dicionário Python) para busca O(1)
- Pilha de escopos para escopo léxico
- Cada símbolo tem: nome, categoria (var/proc/func), tipo, parâmetros, escopo
"""

import sys
from ast_nodes import *
from dataclasses import dataclass
from typing import List, Optional, Dict

class SemanticError(Exception):
    """Exceção para erros semânticos"""
    pass

@dataclass
class Symbol:
    """
    Representa um símbolo na tabela de símbolos
    
    Atributos:
    - name: nome do identificador
    - category: 'var', 'proc' ou 'func'
    - tipo: tipo do símbolo ('integer', 'boolean', ou tipo de retorno para funções)
    - params: lista de parâmetros (para proc/func) como lista de (nome, tipo)
    - scope_level: nível de escopo (0 = global, 1+ = local)
    """
    name: str
    category: str  # 'var', 'proc', 'func'
    tipo: str  # tipo da variável ou tipo de retorno (para funções)
    params: Optional[List[tuple]] = None  # [(nome, tipo), ...] para proc/func
    scope_level: int = 0
    
    def __repr__(self):
        if self.category == 'var':
            return f"Symbol(var {self.name}: {self.tipo}, level={self.scope_level})"
        elif self.category in ['proc', 'func']:
            params_str = ", ".join(f"{n}: {t}" for n, t in (self.params or []))
            ret = f" -> {self.tipo}" if self.category == 'func' else ""
            return f"Symbol({self.category} {self.name}({params_str}){ret}, level={self.scope_level})"
        return f"Symbol({self.name})"


class SymbolTable:
    """
    Tabela de símbolos com suporte a escopo estático/léxico
    
    Implementação:
    - Hash table (dicionário) para cada escopo
    - Pilha de escopos (scope_stack) para controle de aninhamento
    - Regra: contexto envolvente mais próximo (busca de dentro para fora)
    
    Estrutura de dados escolhida: Hash table (dicionário Python)
    - Inserção: O(1)
    - Busca: O(1) 
    - Remoção: O(1)
    - Dinâmica (cresce conforme necessário)
    """
    
    def __init__(self):
        # Pilha de escopos: cada escopo é um dicionário {nome: Symbol}
        self.scope_stack: List[Dict[str, Symbol]] = [{}]  # Começa com escopo global
        self.current_scope_level = 0
    
    def enter_scope(self):
        """Entra em um novo escopo (procedure, function, bloco)"""
        self.scope_stack.append({})
        self.current_scope_level += 1
        
    def exit_scope(self):
        """Sai do escopo atual (remove/torna inacessível símbolos locais)"""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            self.current_scope_level -= 1
    
    def declare(self, name: str, category: str, tipo: str, params: Optional[List[tuple]] = None):
        """
        Declara um símbolo no escopo atual
        
        Verifica duplicação apenas no escopo atual (permite shadowing)
        """
        current_scope = self.scope_stack[-1]
        
        if name in current_scope:
            raise SemanticError(
                f"{category.capitalize()} '{name}' já foi declarada neste escopo"
            )
        
        symbol = Symbol(
            name=name,
            category=category,
            tipo=tipo,
            params=params,
            scope_level=self.current_scope_level
        )
        current_scope[name] = symbol
    
    def lookup(self, name: str) -> Symbol:
        """
        Busca um símbolo na tabela (do escopo atual para o global)
        
        Implementa a regra do contexto envolvente mais próximo:
        busca no escopo atual, depois no pai, depois no avô, etc.
        """
        # Busca de dentro para fora (escopo mais interno primeiro)
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        
        raise SemanticError(f"Identificador '{name}' não foi declarado")
    
    def exists(self, name: str) -> bool:
        """Verifica se um símbolo existe em qualquer escopo acessível"""
        for scope in reversed(self.scope_stack):
            if name in scope:
                return True
        return False
    
    def get_all_symbols(self) -> List[Symbol]:
        """Retorna todos os símbolos de todos os escopos (para debug/impressão)"""
        symbols = []
        for scope in self.scope_stack:
            symbols.extend(scope.values())
        return sorted(symbols, key=lambda s: (s.scope_level, s.name))
    
    def __repr__(self):
        return f"SymbolTable(scopes={len(self.scope_stack)}, level={self.current_scope_level})"


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
        
        # 2. Processar declarações de subrotinas (procedures e functions)
        for subr in node.subr_decls:
            self.visit(subr)
        
        # 3. Processar comando composto
        self.visit(node.compound)
    
    def visit_VarDecl(self, node):
        """Visita o nó VarDecl - declara variáveis na tabela"""
        for var_name in node.ids:
            try:
                self.symbol_table.declare(var_name, 'var', node.tipo)
                print(f"  ✓ Variável '{var_name}' declarada como {node.tipo} (nível {self.symbol_table.current_scope_level})")
            except SemanticError as e:
                self.error(str(e))
    
    def visit_ProcDecl(self, node):
        """Visita o nó ProcDecl - declara procedure e processa seu corpo"""
        # Extrair lista de parâmetros
        params = []
        for param_decl in node.params:
            for param_name in param_decl.ids:
                params.append((param_name, param_decl.tipo))
        
        # Declarar procedure no escopo atual
        try:
            self.symbol_table.declare(node.name, 'proc', 'void', params)
            print(f"  ✓ Procedure '{node.name}' declarada com {len(params)} parâmetro(s)")
        except SemanticError as e:
            self.error(str(e))
            return
        
        # Entrar no escopo da procedure
        self.symbol_table.enter_scope()
        
        # Declarar parâmetros como variáveis locais
        for param_name, param_type in params:
            try:
                self.symbol_table.declare(param_name, 'var', param_type)
                print(f"    • Parâmetro '{param_name}' : {param_type}")
            except SemanticError as e:
                self.error(str(e))
        
        # Processar bloco da procedure
        self.visit(node.block)
        
        # Sair do escopo
        self.symbol_table.exit_scope()
    
    def visit_FuncDecl(self, node):
        """Visita o nó FuncDecl - declara function e processa seu corpo"""
        # Extrair lista de parâmetros
        params = []
        for param_decl in node.params:
            for param_name in param_decl.ids:
                params.append((param_name, param_decl.tipo))
        
        # Declarar function no escopo atual
        try:
            self.symbol_table.declare(node.name, 'func', node.return_type, params)
            print(f"  ✓ Function '{node.name}' declarada: {len(params)} parâmetro(s) -> {node.return_type}")
        except SemanticError as e:
            self.error(str(e))
            return
        
        # Entrar no escopo da function
        self.symbol_table.enter_scope()
        
        # Declarar parâmetros como variáveis locais
        for param_name, param_type in params:
            try:
                self.symbol_table.declare(param_name, 'var', param_type)
                print(f"    • Parâmetro '{param_name}' : {param_type}")
            except SemanticError as e:
                self.error(str(e))
        
        # Processar bloco da function
        self.visit(node.block)
        
        # Sair do escopo
        self.symbol_table.exit_scope()
    
    def visit_Compound(self, node):
        """Visita o nó Compound - processa lista de comandos"""
        for cmd in node.commands:
            self.visit(cmd)
    
    def visit_Assign(self, node):
        """Visita o nó Assign - verifica atribuição e anota AST"""
        # Verificar se identificador foi declarado
        if not self.symbol_table.exists(node.id):
            self.error(f"Variável '{node.id}' não foi declarada")
            return
        
        # Obter símbolo
        symbol = self.symbol_table.lookup(node.id)
        
        # Verificar se é uma variável OU função (em Pascal, atribui ao nome da função para retornar valor)
        if symbol.category not in ['var', 'func']:
            self.error(f"'{node.id}' não pode receber atribuição (é {symbol.category})")
            return
        
        # ANOTAR AST com informações
        node.var_type = symbol.tipo
        node.var_scope_level = symbol.scope_level
        # offset será calculado posteriormente na geração de código
        
        # Verificar tipo da expressão
        expr_type = self.visit(node.expr)
        
        # Verificar compatibilidade de tipos
        if expr_type != symbol.tipo and expr_type != 'unknown':
            self.error(f"Atribuição incompatível: '{node.id}' é {symbol.tipo}, "
                      f"mas expressão é {expr_type}")
    
    def visit_Write(self, node):
        """Visita o nó Write - verifica escrita e anota AST"""
        expr_types = []
        for expr in node.exprs:
            expr_type = self.visit(expr)
            expr_types.append(expr_type)
        
        # ANOTAR AST com tipos das expressões sendo escritas
        node.expr_types = expr_types
    
    def visit_Read(self, node):
        """Visita o nó Read - verifica leitura e anota AST"""
        var_types = []
        for var_name in node.ids:
            if not self.symbol_table.exists(var_name):
                self.error(f"Tentativa de ler variável não declarada '{var_name}'")
                var_types.append('unknown')
            else:
                symbol = self.symbol_table.lookup(var_name)
                var_types.append(symbol.tipo)
        
        # ANOTAR AST com tipos das variáveis sendo lidas
        node.var_types = var_types
    
    def visit_If(self, node):
        """Visita o nó If - verifica condicional e anota AST"""
        # Condição deve ser booleana
        cond_type = self.visit(node.cond)
        if cond_type != 'boolean':
            self.error(f"Condição do 'if' deve ser boolean, mas é {cond_type}")
        
        # ANOTAR AST com tipo da condição
        node.cond_type = cond_type
        
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
        """Visita o nó ProcCall - verifica chamada de procedimento e anota AST"""
        # Verificar se procedure existe
        if not self.symbol_table.exists(node.name):
            self.error(f"Procedure '{node.name}' não foi declarada")
            return
        
        # Obter símbolo da procedure
        symbol = self.symbol_table.lookup(node.name)
        
        # Verificar se é realmente uma procedure
        if symbol.category != 'proc':
            self.error(f"'{node.name}' não é uma procedure (é {symbol.category})")
            return
        
        # ANOTAR AST com informações do procedure
        if symbol.params:
            node.param_types = [param_type for _, param_type in symbol.params]
        
        # Verificar número de argumentos
        expected_params = len(symbol.params) if symbol.params else 0
        actual_args = len(node.args)
        
        if actual_args != expected_params:
            self.error(
                f"Procedure '{node.name}' espera {expected_params} argumento(s), "
                f"mas recebeu {actual_args}"
            )
            return
        
        # Verificar tipos dos argumentos
        if symbol.params:
            for i, (arg, (param_name, param_type)) in enumerate(zip(node.args, symbol.params)):
                arg_type = self.visit(arg)
                if arg_type != param_type:
                    self.error(
                        f"Argumento {i+1} da procedure '{node.name}': "
                        f"esperado {param_type}, recebido {arg_type}"
                    )
    
    def visit_FuncCall(self, node):
        """Visita o nó FuncCall - verifica chamada de função e anota AST"""
        # Verificar se function existe
        if not self.symbol_table.exists(node.name):
            self.error(f"Function '{node.name}' não foi declarada")
            return 'unknown'
        
        # Obter símbolo da function
        symbol = self.symbol_table.lookup(node.name)
        
        # Verificar se é realmente uma function
        if symbol.category != 'func':
            self.error(f"'{node.name}' não é uma function (é {symbol.category})")
            return 'unknown'
        
        # ANOTAR AST com informações da function
        node.return_type = symbol.tipo
        if symbol.params:
            node.param_types = [param_type for _, param_type in symbol.params]
        
        # Verificar número de argumentos
        expected_params = len(symbol.params) if symbol.params else 0
        actual_args = len(node.args)
        
        if actual_args != expected_params:
            self.error(
                f"Function '{node.name}' espera {expected_params} argumento(s), "
                f"mas recebeu {actual_args}"
            )
            return symbol.tipo  # Retorna tipo esperado mesmo com erro
        
        # Verificar tipos dos argumentos
        if symbol.params:
            for i, (arg, (param_name, param_type)) in enumerate(zip(node.args, symbol.params)):
                arg_type = self.visit(arg)
                if arg_type != param_type:
                    self.error(
                        f"Argumento {i+1} da function '{node.name}': "
                        f"esperado {param_type}, recebido {arg_type}"
                    )
        
        # Retornar tipo de retorno da function
        return symbol.tipo
    
    def visit_BinOp(self, node):
        """Visita o nó BinOp - verifica operação binária e anota AST"""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        result_type = 'unknown'
        
        # Operadores aritméticos: +, -, *, div
        if node.op in ['+', '-', '*', 'div']:
            if left_type != 'integer' or right_type != 'integer':
                self.error(f"Operador '{node.op}' requer operandos integer, "
                          f"mas recebeu {left_type} e {right_type}")
            result_type = 'integer'
        
        # Operadores relacionais: =, <>, <, <=, >, >=
        elif node.op in ['=', '<>', '<', '<=', '>', '>=']:
            if left_type != right_type:
                self.error(f"Operador '{node.op}' requer operandos do mesmo tipo, "
                          f"mas recebeu {left_type} e {right_type}")
            result_type = 'boolean'
        
        # Operadores lógicos: and, or
        elif node.op in ['and', 'or']:
            if left_type != 'boolean' or right_type != 'boolean':
                self.error(f"Operador '{node.op}' requer operandos boolean, "
                          f"mas recebeu {left_type} e {right_type}")
            result_type = 'boolean'
        
        else:
            self.error(f"Operador desconhecido: '{node.op}'")
        
        # ANOTAR AST com tipo do resultado
        node.result_type = result_type
        
        return result_type
    
    def visit_UnOp(self, node):
        """Visita o nó UnOp - verifica operação unária e anota AST"""
        expr_type = self.visit(node.expr)
        
        result_type = 'unknown'
        
        if node.op == '-':
            # Menos unário requer integer
            if expr_type != 'integer':
                self.error(f"Operador unário '-' requer operando integer, "
                          f"mas recebeu {expr_type}")
            result_type = 'integer'
        
        elif node.op == 'not':
            # Not requer boolean
            if expr_type != 'boolean':
                self.error(f"Operador 'not' requer operando boolean, "
                          f"mas recebeu {expr_type}")
            result_type = 'boolean'
        
        else:
            self.error(f"Operador unário desconhecido: '{node.op}'")
        
        # ANOTAR AST com tipo do resultado
        node.result_type = result_type
        
        return result_type
    
    def visit_Var(self, node):
        """Visita o nó Var - retorna tipo da variável e anota AST"""
        if not self.symbol_table.exists(node.name):
            self.error(f"Variável '{node.name}' não foi declarada")
            return 'unknown'
        
        symbol = self.symbol_table.lookup(node.name)
        
        # Verificar se é uma variável (não pode usar proc/func como variável)
        if symbol.category != 'var':
            self.error(f"'{node.name}' não é uma variável (é {symbol.category})")
            return 'unknown'
        
        # ANOTAR AST com informações semânticas
        node.tipo = symbol.tipo
        node.scope_level = symbol.scope_level
        # offset será calculado posteriormente
        
        return symbol.tipo
    
    def visit_Num(self, node):
        """Visita o nó Num - retorna tipo integer"""
        return 'integer'
    
    def visit_Bool(self, node):
        """Visita o nó Bool - retorna tipo boolean"""
        return 'boolean'
    
    def print_symbol_table(self):
        """Imprime a tabela de símbolos de forma organizada"""
        print("\n" + "=" * 80)
        print("TABELA DE SÍMBOLOS (Escopo Estático/Léxico)")
        print("=" * 80)
        
        symbols = self.symbol_table.get_all_symbols()
        
        if not symbols:
            print("  (vazia)")
        else:
            # Agrupar por nível de escopo
            by_level = {}
            for sym in symbols:
                if sym.scope_level not in by_level:
                    by_level[sym.scope_level] = []
                by_level[sym.scope_level].append(sym)
            
            # Imprimir por nível
            for level in sorted(by_level.keys()):
                scope_name = "Global" if level == 0 else f"Local (nível {level})"
                print(f"\n  ┌─ Escopo {scope_name} ─")
                
                for sym in by_level[level]:
                    if sym.category == 'var':
                        print(f"  │  {sym.name:20} : {sym.tipo:10} (variável)")
                    elif sym.category == 'proc':
                        params_str = ", ".join(f"{n}: {t}" for n, t in (sym.params or []))
                        print(f"  │  {sym.name:20} ({params_str}) (procedure)")
                    elif sym.category == 'func':
                        params_str = ", ".join(f"{n}: {t}" for n, t in (sym.params or []))
                        print(f"  │  {sym.name:20} ({params_str}) -> {sym.tipo} (function)")
        
        print("=" * 80)


def analyze_semantics(ast_root):
    """Função principal para análise semântica"""
    analyzer = SemanticAnalyzer()
    success = analyzer.analyze(ast_root)
    analyzer.print_symbol_table()
    return success


# Teste do analisador semântico
if __name__ == '__main__':
    print("Analisador semântico - use o parser.py para testar")