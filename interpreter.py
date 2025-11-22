"""
Analisador Semântico para Rascal - Versão com Estrutura Híbrida
- Estrutura interna: Tudo junto no mesmo dicionário (eficiente)
- Visualização: Separado por categoria ao imprimir (organizado)
- Pilha de escopos para controle léxico
"""

import sys
from ast_nodes import *
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

class SemanticError(Exception):
    """Exceção para erros semânticos"""
    pass


class SemanticWarning(Exception):
    """Exceção leve usada para sinalizar alertas semânticos (não fatais)."""
    pass

ParamList = List[Tuple[str, str]]


@dataclass
class Symbol:
    """Classe base para qualquer símbolo"""
    name: str
    scope_level: int

    @property
    def category(self) -> str:
        raise NotImplementedError

    @property
    def tipo(self) -> Optional[str]:
        return None

    @property
    def params(self) -> Optional[ParamList]:
        return None

    def __repr__(self) -> str:
        return f"Symbol({self.category} {self.name}, level={self.scope_level})"


@dataclass
class VarSymbol(Symbol):
    """Símbolo para variáveis (inclui parâmetros)"""
    var_type: str
    is_param: bool = False

    @property
    def category(self) -> str:
        return 'var'

    @property
    def tipo(self) -> str:
        return self.var_type

    def __repr__(self) -> str:
        kind = 'param' if self.is_param else 'var'
        return f"Symbol({kind} {self.name}: {self.var_type}, level={self.scope_level})"


@dataclass
class ProcSymbol(Symbol):
    """Símbolo para procedures"""
    param_list: ParamList = field(default_factory=list)

    @property
    def category(self) -> str:
        return 'proc'

    @property
    def params(self) -> ParamList:
        return self.param_list

    def __repr__(self) -> str:
        params_str = ", ".join(f"{n}: {t}" for n, t in self.param_list)
        return f"Symbol(proc {self.name}({params_str}), level={self.scope_level})"


@dataclass
class FuncSymbol(ProcSymbol):
    """Símbolo para functions (herda lista de parâmetros)"""
    return_type: str = 'void'

    @property
    def category(self) -> str:
        return 'func'

    @property
    def tipo(self) -> str:
        return self.return_type

    def __repr__(self) -> str:
        params_str = ", ".join(f"{n}: {t}" for n, t in self.param_list)
        return (
            f"Symbol(func {self.name}({params_str}) -> {self.return_type}, "
            f"level={self.scope_level})"
        )


@dataclass
class ProgramSymbol(Symbol):
    """Símbolo para o identificador do programa (categoria 'program')."""

    @property
    def category(self) -> str:
        return 'program'

    def __repr__(self) -> str:
        return f"Symbol(program {self.name}, level={self.scope_level})"


class SymbolTable:
    """
    Tabela de símbolos com pilha de escopos
    
    Estrutura INTERNA: 
    - scope_stack: List[Dict[str, Symbol]] 
    - Cada dicionário contém TODOS os tipos misturados (var, proc, func)
    - Busca eficiente O(1)
    
    Visualização EXTERNA:
    - Separa por categoria ao imprimir
    - Organiza hierarquia de escopos
    """
    
    def __init__(self):
        # Pilha de escopos: cada escopo é um dicionário {nome: Symbol}
        # TUDO junto: vars, procs e funcs no mesmo dict
        self.scope_stack: List[Dict[str, Symbol]] = [{}]  # [0] = Global
        self.current_scope_level = 0
        self.scope_sequence = 0
        self.scope_stack_meta: List[Dict[str, Any]] = [
            {
                'level': 0,
                'owner': 'global',
                'category': 'global',
                'label': 'GLOBAL',
                'parent_level': None,
                'parent_label': None,
                'order': 0,
                'status': 'active',
            }
        ]
        # Escopos já removidos (guardados somente para visualização/debug)
        self.archived_scopes: List[Dict[str, Any]] = []
    
    def enter_scope(self, owner: Optional[str] = None, category: str = 'local'):
        """Entra em um novo escopo (procedure, function)"""
        parent_meta = self.scope_stack_meta[-1]
        self.scope_stack.append({})
        self.current_scope_level += 1
        self.scope_sequence += 1
        label = owner or f"{category.upper()}_{self.scope_sequence}"
        self.scope_stack_meta.append(
            {
                'level': self.current_scope_level,
                'owner': owner,
                'category': category,
                'label': label,
                'parent_level': parent_meta['level'],
                'parent_label': parent_meta['label'],
                'order': self.scope_sequence,
                'status': 'active',
            }
        )
        
    def exit_scope(self):
        """Sai do escopo atual, arquivando símbolos para debug/impressão"""
        if len(self.scope_stack) > 1:
            popped_scope = self.scope_stack.pop()
            meta = dict(self.scope_stack_meta.pop())
            meta['status'] = 'archived'
            meta['symbols'] = dict(popped_scope)
            # Guardar cópia para evitar dependência do dict original
            self.archived_scopes.append(meta)
            self.current_scope_level -= 1
    
    def declare(
        self,
        name: str,
        category: str,
        tipo: Optional[str] = None,
        params: Optional[ParamList] = None,
        *,
        is_param: bool = False,
    ) -> Symbol:
        """Declara um símbolo no escopo atual"""
        current_scope = self.scope_stack[-1]

        # Verifica duplicação APENAS no escopo atual
        if name in current_scope:
            raise SemanticWarning(
                f"{category.capitalize()} '{name}' já foi declarada neste escopo; nova declaração ignorada"
            )

        # Criar o símbolo apropriado
        if category == 'var':
            if not tipo:
                raise SemanticError(f"Tipo não informado para variável '{name}'")
            symbol = VarSymbol(
                name=name,
                scope_level=self.current_scope_level,
                var_type=tipo,
                is_param=is_param,
            )
        elif category == 'proc':
            symbol = ProcSymbol(
                name=name,
                scope_level=self.current_scope_level,
                param_list=params or [],
            )
        elif category == 'func':
            if not tipo:
                raise SemanticError(f"Tipo de retorno não informado para função '{name}'")
            symbol = FuncSymbol(
                name=name,
                scope_level=self.current_scope_level,
                param_list=params or [],
                return_type=tipo,
            )
        else:
            if category == 'program':
                # Declarar identificador do programa (sem parâmetros)
                symbol = ProgramSymbol(
                    name=name, scope_level=self.current_scope_level
                )
            else:
                raise SemanticError(f"Categoria desconhecida: {category}")

        # Inserir no dicionário do escopo atual
        current_scope[name] = symbol
        return symbol
    
    def lookup(self, name: str) -> Symbol:
        """
        Busca símbolo (do escopo atual para o global)
        Implementa: contexto envolvente mais próximo
        """
        # Busca de dentro para fora (topo da pilha → base)
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
    
    def get_symbols_by_category(self, level: int) -> Dict[str, List[Symbol]]:
        """
        Separa símbolos de um escopo por categoria
        
        Returns:
            {'vars': [...], 'procs': [...], 'funcs': [...]}
        """
        if level >= len(self.scope_stack):
            return {'vars': [], 'procs': [], 'funcs': []}
        return self._group_scope(self.scope_stack[level])

    @staticmethod
    def _group_scope(scope: Dict[str, Symbol]) -> Dict[str, List[Symbol]]:
        """Separa um escopo (ativo ou arquivado) por categoria."""
        grouped = {'programs': [], 'vars': [], 'procs': [], 'funcs': []}

        for sym in scope.values():
            if isinstance(sym, FuncSymbol):
                grouped['funcs'].append(sym)
            elif isinstance(sym, ProcSymbol):
                grouped['procs'].append(sym)
            elif isinstance(sym, VarSymbol):
                grouped['vars'].append(sym)
            elif isinstance(sym, ProgramSymbol):
                grouped['programs'].append(sym)

        for key in grouped:
            grouped[key].sort(key=lambda s: s.name)

        return grouped
    
    def __repr__(self):
        return f"SymbolTable(scopes={len(self.scope_stack)}, level={self.current_scope_level})"


class SemanticAnalyzer:
    """Analisador semântico - percorre a AST verificando regras semânticas"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.has_errors = False
        self.warnings: List[str] = []
        # pilha para rastrear atribuições ao identificador da função
        # cada item: {'name': str, 'count': int}
        self._func_return_stack: List[Dict[str, int]] = []
    
    def error(self, message):
        """Registra um erro semântico"""
        self.errors.append(f"ERRO SEMÂNTICO: {message}")
        self.has_errors = True
        print(f"ERRO SEMÂNTICO: {message}")

    def warning(self, message):
        """Registra um alerta semântico (não interrompe a análise)."""
        note = f"ALERTA SEMÂNTICO: {message}"
        self.warnings.append(note)
        print(note)
    
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
        # Declarar identificador do programa no escopo global
        try:
            self.symbol_table.declare(node.name, 'program')
        except SemanticWarning as w:
            self.warning(str(w))
        except SemanticError as e:
            # já registrado erro de duplicação se houver
            self.error(str(e))

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
            except SemanticWarning as w:
                self.warning(str(w))
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
            self.symbol_table.declare(node.name, 'proc', params=params)
            print(f"  ✓ Procedure '{node.name}' declarada com {len(params)} parâmetro(s)")
        except SemanticWarning as w:
            self.warning(str(w))
            return
        except SemanticError as e:
            self.error(str(e))
            return
        
        # Entrar no escopo da procedure
        self.symbol_table.enter_scope(owner=node.name, category='proc')
        
        # Declarar parâmetros como variáveis locais
        for param_name, param_type in params:
            try:
                self.symbol_table.declare(param_name, 'var', param_type, is_param=True)
                print(f"    • Parâmetro '{param_name}' : {param_type}")
            except SemanticWarning as w:
                self.warning(str(w))
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
        except SemanticWarning as w:
            self.warning(str(w))
            return
        except SemanticError as e:
            self.error(str(e))
            return
        
        # Entrar no escopo da function
        self.symbol_table.enter_scope(owner=node.name, category='func')
        
        # Declarar parâmetros como variáveis locais
        for param_name, param_type in params:
            try:
                self.symbol_table.declare(param_name, 'var', param_type, is_param=True)
                print(f"    • Parâmetro '{param_name}' : {param_type}")
            except SemanticWarning as w:
                self.warning(str(w))
            except SemanticError as e:
                self.error(str(e))
        
        # Processar bloco da function (checagem semântica normal)
        self.visit(node.block)

        # Verificação flow-sensitive: calcular número mínimo/máximo de atribuições
        # ao identificador da função que podem ocorrer em tempo de execução.
        def compute_return_range(cmd_node):
            """
            Retorna tupla (min_count, max_count) onde max_count=None significa ilimitado (>1).
            """
            # Assign to function identifier
            if isinstance(cmd_node, Assign):
                if cmd_node.id == node.name:
                    return (1, 1)
                else:
                    return (0, 0)

            # Compound (sequence)
            if isinstance(cmd_node, Compound):
                min_sum = 0
                max_sum = 0
                for c in cmd_node.commands:
                    mn, mx = compute_return_range(c)
                    min_sum += mn
                    if max_sum is None or mx is None:
                        max_sum = None
                    else:
                        max_sum += mx
                return (min_sum, max_sum)

            # If: choose one branch
            if isinstance(cmd_node, If):
                then_range = compute_return_range(cmd_node.then_cmd)
                else_range = compute_return_range(cmd_node.else_cmd) if cmd_node.else_cmd else (0, 0)
                min_count = min(then_range[0], else_range[0])
                # max is the more permissive branch
                if then_range[1] is None or else_range[1] is None:
                    max_count = None
                else:
                    max_count = max(then_range[1], else_range[1])
                return (min_count, max_count)

            # While: can execute 0..N times; conservative
            if isinstance(cmd_node, While):
                body_min, body_max = compute_return_range(cmd_node.body)
                # min can be 0 (loop may not execute)
                if body_max is None or body_max > 0:
                    return (0, None)
                return (0, 0)

            # For other commands (Read, Write, ProcCall, FuncCall, Var, etc.)
            # they do not directly assign to the function identifier
            return (0, 0)

        # Compute range for the function body (compound command inside block)
        try:
            compound_cmd = node.block.compound
        except Exception:
            compound_cmd = None

        if compound_cmd is None:
            self.error(f"Function '{node.name}' sem corpo válido para verificação de retorno")
        else:
            mn, mx = compute_return_range(compound_cmd)
            # Interpret max=None as >1 (unbounded)
            if mn == 0:
                self.error(f"Function '{node.name}' nao retorna valor")
            elif mx is None or mx > 1:
                self.error(
                    f"Function '{node.name}' pode atribuir ao identificador mais de uma vez; deve haver exatamente uma atribuição por execução"
                )

        # Sair do escopo
        self.symbol_table.exit_scope()
    
    def visit_Compound(self, node):
        """Visita o nó Compound - processa lista de comandos"""
        for cmd in node.commands:
            self.visit(cmd)
    
    def visit_Assign(self, node):
        """Visita o nó Assign - verifica atribuição e anota AST"""
        if not self.symbol_table.exists(node.id):
            self.error(f"Variável '{node.id}' não foi declarada")
            return
        
        symbol = self.symbol_table.lookup(node.id)
        
        if symbol.category not in ['var', 'func']:
            self.error(f"'{node.id}' não pode receber atribuição (é {symbol.category})")
            return
        
        # ANOTAR AST
        node.var_type = symbol.tipo
        node.var_scope_level = symbol.scope_level
        
        # Verificar tipo da expressão
        expr_type = self.visit(node.expr)
        
        if expr_type != symbol.tipo and expr_type != 'unknown':
            self.error(f"Atribuição incompatível: '{node.id}' é {symbol.tipo}, "
                      f"mas expressão é {expr_type}")
        # Note: counting of function-return assignments is now done via
        # a flow-sensitive helper (compute_return_range) in visit_FuncDecl.
        # We keep this method focused on type checking only.
    
    def visit_Write(self, node):
        """Visita o nó Write"""
        expr_types = []
        for expr in node.exprs:
            expr_type = self.visit(expr)
            expr_types.append(expr_type)
        node.expr_types = expr_types
    
    def visit_Read(self, node):
        """Visita o nó Read"""
        var_types = []
        for var_name in node.ids:
            if not self.symbol_table.exists(var_name):
                self.error(f"Tentativa de ler variável não declarada '{var_name}'")
                var_types.append('unknown')
            else:
                symbol = self.symbol_table.lookup(var_name)
                var_types.append(symbol.tipo)
        node.var_types = var_types
    
    def visit_If(self, node):
        """Visita o nó If"""
        cond_type = self.visit(node.cond)
        if cond_type != 'boolean':
            self.error(f"Condição do 'if' deve ser boolean, mas é {cond_type}")
        node.cond_type = cond_type
        
        self.visit(node.then_cmd)
        if node.else_cmd:
            self.visit(node.else_cmd)
    
    def visit_While(self, node):
        """Visita o nó While"""
        cond_type = self.visit(node.cond)
        if cond_type != 'boolean':
            self.error(f"Condição do 'while' deve ser boolean, mas é {cond_type}")
        self.visit(node.body)
    
    def visit_ProcCall(self, node):
        """Visita o nó ProcCall"""
        if not self.symbol_table.exists(node.name):
            self.error(f"Procedure '{node.name}' não foi declarada")
            return
        
        symbol = self.symbol_table.lookup(node.name)
        
        if symbol.category != 'proc':
            self.error(f"'{node.name}' não é uma procedure (é {symbol.category})")
            return
        
        if symbol.params:
            node.param_types = [param_type for _, param_type in symbol.params]
        
        expected_params = len(symbol.params) if symbol.params else 0
        actual_args = len(node.args)
        
        if actual_args != expected_params:
            self.error(
                f"Procedure '{node.name}' espera {expected_params} argumento(s), "
                f"mas recebeu {actual_args}"
            )
            return
        
        if symbol.params:
            for i, (arg, (param_name, param_type)) in enumerate(zip(node.args, symbol.params)):
                arg_type = self.visit(arg)
                if arg_type != param_type:
                    self.error(
                        f"Argumento {i+1} da procedure '{node.name}': "
                        f"esperado {param_type}, recebido {arg_type}"
                    )
    
    def visit_FuncCall(self, node):
        """Visita o nó FuncCall"""
        if not self.symbol_table.exists(node.name):
            self.error(f"Function '{node.name}' não foi declarada")
            return 'unknown'
        
        symbol = self.symbol_table.lookup(node.name)
        
        if symbol.category != 'func':
            self.error(f"'{node.name}' não é uma function (é {symbol.category})")
            return 'unknown'
        
        node.return_type = symbol.tipo
        if symbol.params:
            node.param_types = [param_type for _, param_type in symbol.params]
        
        expected_params = len(symbol.params) if symbol.params else 0
        actual_args = len(node.args)
        
        if actual_args != expected_params:
            self.error(
                f"Function '{node.name}' espera {expected_params} argumento(s), "
                f"mas recebeu {actual_args}"
            )
            return symbol.tipo
        
        if symbol.params:
            for i, (arg, (param_name, param_type)) in enumerate(zip(node.args, symbol.params)):
                arg_type = self.visit(arg)
                if arg_type != param_type:
                    self.error(
                        f"Argumento {i+1} da function '{node.name}': "
                        f"esperado {param_type}, recebido {arg_type}"
                    )
        
        return symbol.tipo
    
    def visit_BinOp(self, node):
        """Visita o nó BinOp"""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        result_type = 'unknown'
        
        if node.op in ['+', '-', '*', 'div']:
            if left_type != 'integer' or right_type != 'integer':
                self.error(f"Operador '{node.op}' requer operandos integer, "
                          f"mas recebeu {left_type} e {right_type}")
            result_type = 'integer'
        
        elif node.op in ['=', '<>', '<', '<=', '>', '>=']:
            if left_type != right_type:
                self.error(f"Operador '{node.op}' requer operandos do mesmo tipo, "
                          f"mas recebeu {left_type} e {right_type}")
            result_type = 'boolean'
        
        elif node.op in ['and', 'or']:
            if left_type != 'boolean' or right_type != 'boolean':
                self.error(f"Operador '{node.op}' requer operandos boolean, "
                          f"mas recebeu {left_type} e {right_type}")
            result_type = 'boolean'
        
        else:
            self.error(f"Operador desconhecido: '{node.op}'")
        
        node.result_type = result_type
        return result_type
    
    def visit_UnOp(self, node):
        """Visita o nó UnOp"""
        expr_type = self.visit(node.expr)
        
        result_type = 'unknown'
        
        if node.op == '-':
            if expr_type != 'integer':
                self.error(f"Operador unário '-' requer operando integer, "
                          f"mas recebeu {expr_type}")
            result_type = 'integer'
        
        elif node.op == 'not':
            if expr_type != 'boolean':
                self.error(f"Operador 'not' requer operando boolean, "
                          f"mas recebeu {expr_type}")
            result_type = 'boolean'
        
        else:
            self.error(f"Operador unário desconhecido: '{node.op}'")
        
        node.result_type = result_type
        return result_type
    
    def visit_Var(self, node):
        """Visita o nó Var"""
        if not self.symbol_table.exists(node.name):
            self.error(f"Variável '{node.name}' não foi declarada")
            return 'unknown'
        
        symbol = self.symbol_table.lookup(node.name)
        
        if symbol.category != 'var':
            self.error(f"'{node.name}' não é uma variável (é {symbol.category})")
            return 'unknown'
        
        node.tipo = symbol.tipo
        node.scope_level = symbol.scope_level
        
        return symbol.tipo
    
    def visit_Num(self, node):
        """Visita o nó Num"""
        return 'integer'
    
    def visit_Bool(self, node):
        """Visita o nó Bool"""
        return 'boolean'
    
    # ========== IMPRESSÃO DA TABELA ==========
    
    def print_symbol_table(self):
        """Imprime tabela de símbolos considerando escopos ativos e arquivados."""
        print("\n" + "=" * 80)
        print("TABELA DE SIMBOLOS (escopos ativos + arquivados)")
        print("=" * 80)

        scopes = self._collect_scopes_for_print()

        if not scopes:
            print("(tabela vazia)")
            print("=" * 80)
            return

        total_symbols = 0
        for scope_info in scopes:
            total_symbols += sum(len(scope_info['grouped'][cat]) for cat in ('programs','vars', 'procs', 'funcs'))
            self._print_scope(scope_info)

        print("-" * 80)
        print(f"Resumo: {total_symbols} simbolo(s) distribuidos em {len(scopes)} escopo(s) impressos.")
        print("=" * 80)

    def _collect_scopes_for_print(self) -> List[Dict[str, Any]]:
        """Retorna lista de escopos com metadados e símbolos agrupados."""
        scopes: List[Dict[str, Any]] = []
        table = self.symbol_table

        for scope_dict, meta in zip(table.scope_stack, table.scope_stack_meta):
            meta_copy = dict(meta)
            meta_copy['status'] = 'active'
            scopes.append(
                {
                    'meta': meta_copy,
                    'grouped': table._group_scope(scope_dict),
                }
            )

        archived_sorted = sorted(table.archived_scopes, key=lambda item: item['order'])
        for snapshot in archived_sorted:
            meta_copy = dict(snapshot)
            symbols_dict = meta_copy.pop('symbols', {})
            meta_copy['status'] = 'archived'
            scopes.append(
                {
                    'meta': meta_copy,
                    'grouped': table._group_scope(symbols_dict),
                }
            )

        return scopes

    def _print_scope(self, scope_info: Dict[str, Any]):
        """Imprime um escopo específico separado por categoria."""
        meta = scope_info['meta']
        grouped = scope_info['grouped']
        header = self._format_scope_header(meta)

        print("\n" + "-" * 80)
        print(header)
        print("-" * 80)

        has_content = any(grouped[cat] for cat in ('programs','vars', 'procs', 'funcs'))
        if not has_content:
            print("  (escopo vazio)")
            return

        # imprimir programa (se existir), variáveis, procedures e functions
        self._print_program_table(grouped.get('programs', []))
        self._print_variables_table(grouped['vars'])
        self._print_procedures_table(grouped['procs'])
        self._print_functions_table(grouped['funcs'])

    def _format_scope_header(self, meta: Dict[str, Any]) -> str:
        label = meta.get('label') or f"NIVEL {meta.get('level', '?')}"
        level = meta.get('level')
        category = meta.get('category', 'local')
        parent = meta.get('parent_label') or "-"
        status = meta.get('status', 'active')
        owner = meta.get('owner')
        owner_part = f" | dono={owner}" if owner else ""
        return (
            f"Escopo {label} (nivel={level} | tipo={category} | pai={parent} | status={status}{owner_part})"
        )

    def _print_variables_table(self, vars_list: List[VarSymbol]):
        """Imprime tabela de variáveis em ASCII simples."""
        print("  Variaveis:")
        if not vars_list:
            print("    (nenhuma variavel)")
            return

        print("    {0:<18} {1:<12} {2:<10}".format("Nome", "Tipo", "Parametro"))
        print("    {0:<18} {1:<12} {2:<10}".format('-'*18, '-'*12, '-'*10))
        for var in vars_list:
            is_param = 'sim' if var.is_param else 'nao'
            print(f"    {var.name:<18} {var.tipo:<12} {is_param:<10}")

    def _print_procedures_table(self, procs_list: List[ProcSymbol]):
        """Imprime tabela de procedures em ASCII simples."""
        print("  Procedures:")
        if not procs_list:
            print("    (nenhuma procedure)")
            return

        print("    {0:<18} {1}".format("Nome", "Parâmetros"))
        print("    {0:<18} {1}".format('-'*18, '-'*40))
        for proc in procs_list:
            params_str = ", ".join(f"{n}:{t}" for n, t in proc.params) if proc.params else "(sem parametros)"
            print(f"    {proc.name:<18} {params_str}")

    def _print_program_table(self, prog_list: List[ProgramSymbol]):
        """Imprime o identificador do programa, se presente."""
        print("  Programa:")
        if not prog_list:
            print("    (nenhum programa declarado)")
            return
        print("    {0:<18} {1}".format("Nome", "Nivel"))
        print("    {0:<18} {1}".format('-'*18, '-'*5))
        for prog in prog_list:
            print(f"    {prog.name:<18} {prog.scope_level}")

    def _print_functions_table(self, funcs_list: List[FuncSymbol]):
        """Imprime tabela de functions em ASCII simples."""
        print("  Functions:")
        if not funcs_list:
            print("    (nenhuma funcao)")
            return

        print("    {0:<18} {1:<26} {2}".format("Nome", "Parâmetros", "Retorno"))
        print("    {0:<18} {1:<26} {2}".format('-'*18, '-'*26, '-'*10))
        for func in funcs_list:
            params_str = ", ".join(f"{n}:{t}" for n, t in func.params) if func.params else "()"
            print(f"    {func.name:<18} {params_str:<26} {func.tipo}")


def analyze_semantics(ast_root):
    """Função principal para análise semântica"""
    analyzer = SemanticAnalyzer()
    success = analyzer.analyze(ast_root)
    analyzer.print_symbol_table()
    return success


if __name__ == '__main__':
    print("Analisador semântico - use o parser.py para testar")