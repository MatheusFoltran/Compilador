"""Auxiliares de geração MEPA — passagem 1: cálculo de offsets

Este módulo calcula os deslocamentos (offsets) para parâmetros e
variáveis locais de cada escopo (global e sub-rotinas). Anota
`VarSymbol.offset` e também preenche nós AST `Var` com `offset` quando
possível (os nós devem já ter `scope_level` definido pelo analisador
semântico).

Convenções:
- offsets de parâmetros: 0 .. P-1 (na ordem de declaração)
- offsets de locais: P .. P+L-1

A função `compute_offsets(program_ast, symbol_table)` espera que a
análise semântica já tenha sido executada (para que `symbol_table`
tenha snapshots arquivados e nós AST contenham informação de nível).
"""
import re
from typing import Dict, List, Optional


INSTR_MNEMONICS = {
    'main': 'MAIN',
    'halt': 'STOP',
    'nop': 'NOOP',
    'ldct': 'LDCT',
    'ldvl': 'LDVL',
    'stvl': 'STVL',
    'add': 'ADDD',
    'subt': 'SUBT',
    'mult': 'MULT',
    'divi': 'DIVI',
    'inv': 'NEGT',
    'andd': 'LAND',
    'orr': 'LORR',
    'nott': 'LNOT',
    'read': 'READ',
    'writ': 'PRNT',
    'jmp': 'JUMP',
    'jmpf': 'JMPF',
    'call': 'CFUN',
    'entproc': 'ENFN',
    'retproc': 'RTRN',
    'alloc': 'ALOC',
    'dealloc': 'DLOC',
    'less': 'LESS',
    'grt': 'GRTR',
    'eql': 'EQUA',
    'dif': 'DIFF',
    'leq': 'LEQU',
    'geq': 'GEQU',
}
from ast_nodes import Program, ProcDecl, FuncDecl, VarDecl, ParamDecl, Var


def compute_offsets(ast_root: Program, symbol_table) -> None:
    """Calcula e anota offsets para todos os escopos.

    Modifica os snapshots arquivados em `symbol_table` e os campos
    `VarSymbol.offset`, e anota nós AST `Var` com `offset` quando o
    símbolo puder ser resolvido por nível de escopo e nome.
    """

    # Auxiliar: mapear snapshots arquivados por (owner, level)
    archived_by_owner = {}
    for snap in symbol_table.archived_scopes:
        owner = snap.get('owner')
        level = snap.get('level')
        key = (owner, level)
        archived_by_owner[key] = snap

    # 1) Escopo global: topo de `scope_stack` no nível 0
    # calcular offsets para variáveis globais seguindo a ordem de
    # declaração no programa
    global_scope = symbol_table.scope_stack[0]
    P = 0
    # parameters none for global; locals are program-level vars
    if ast_root and isinstance(ast_root, Program):
        glob_block = ast_root.block
        # assign offsets for globals in declaration order
        offset = 0
        for var_decl in glob_block.var_decls:
            for vid in var_decl.ids:
                sym = global_scope.get(vid)
                if sym is not None:
                    setattr(sym, 'offset', offset)
                offset += 1

    # 2) Para cada escopo arquivado (procedimentos/funções), usar a AST
    # para determinar a ordem de declaração de modo que os offsets
    # coincidam com a ordem no código-fonte.
    def process_subroutine(node, level_expected):
        # `node` é ProcDecl ou FuncDecl
        owner = node.name
        key = (owner, level_expected)
        snap = archived_by_owner.get(key)

        # encontrar dicionário de símbolos deste escopo
        symbols = None
        if snap:
            symbols = snap.get('symbols', {})

        # contar parâmetros e atribuir offsets na ordem de declaração
        param_count = 0
        offset = 0
        # parâmetros: node.params é uma lista de ParamDecl
        for param_decl in node.params:
            for pid in param_decl.ids:
                # atualizar símbolo arquivado, se presente
                if symbols and pid in symbols:
                    sym = symbols[pid]
                    setattr(sym, 'offset', offset)
                else:
                    # como fallback, tentar localizar o símbolo nas
                    # tabelas de escopo ativas e atualizar o objeto
                    for sc in symbol_table.scope_stack:
                        if pid in sc:
                            setattr(sc[pid], 'offset', offset)
                            break
                offset += 1
                param_count += 1

        # Locais: percorrer `node.block.var_decls` na ordem de declaração
        local_count = 0
        for var_decl in node.block.var_decls:
            for vid in var_decl.ids:
                if symbols and vid in symbols:
                    sym = symbols[vid]
                    setattr(sym, 'offset', offset)
                else:
                    for sc in symbol_table.scope_stack:
                        if vid in sc:
                            setattr(sc[vid], 'offset', offset)
                            break
                offset += 1
                local_count += 1

        # Armazenar contagens no objeto símbolo, se o símbolo declarador
        # estiver disponível no escopo pai (enclosing).
        # O símbolo do procedimento declarado normalmente vive no escopo
        # pai — tentamos localizá-lo em snapshots arquivados ou nas
        # tabelas ativas.
        proc_symbol = None
        # search in archived snapshots
        for snap2 in symbol_table.archived_scopes:
            if snap2.get('owner') == owner:
                # parent snapshot contains the symbol? usually declaring scope
                # is the parent meta; try to find in parent scope dict
                parent_level = snap2.get('parent_level')
                # find the scope dict at parent_level
                if parent_level is not None and parent_level < len(symbol_table.scope_stack):
                    parent_scope = symbol_table.scope_stack[parent_level]
                    if owner in parent_scope:
                        proc_symbol = parent_scope[owner]
                        break

        # fallback: procurar em todos os escopos ativos
        if not proc_symbol:
            for sc in symbol_table.scope_stack:
                if owner in sc:
                    proc_symbol = sc[owner]
                    break

        if proc_symbol is not None:
            setattr(proc_symbol, 'param_count', param_count)
            setattr(proc_symbol, 'local_count', local_count)

    # Percorre a AST para encontrar ProcDecl e FuncDecl e processá-los.
    def walk(node, current_level=0):
        if isinstance(node, ProcDecl):
            # snapshots arquivados registram nível; assumimos nível 1 para
            # sub-rotinas declaradas no mesmo nível do programa
            process_subroutine(node, 1)
            # não descer para sub-rotinas internas (linguagem não permite)
            return
        if isinstance(node, FuncDecl):
            process_subroutine(node, 1)
            return
        # recurse
        for attr in getattr(node, '__dict__', {}):
            child = getattr(node, attr)
            if isinstance(child, list):
                for c in child:
                    if hasattr(c, '__dict__'):
                        walk(c, current_level)
            elif hasattr(child, '__dict__'):
                walk(child, current_level)

    walk(ast_root)

    # 3) Finalmente, anotar nós AST `Var` com `offset` usando
    # `node.scope_level` e o nome do símbolo
    def annotate_vars(node):
        if isinstance(node, Var):
            lvl = getattr(node, 'scope_level', None)
            name = node.name
            offset = None
            if lvl == 0:
                sym = symbol_table.scope_stack[0].get(name)
                if sym:
                    offset = getattr(sym, 'offset', None)
            else:
                # localizar snapshot arquivado com level == lvl
                for snap in symbol_table.archived_scopes:
                    if snap.get('level') == lvl:
                        sym = snap.get('symbols', {}).get(name)
                        if sym:
                            offset = getattr(sym, 'offset', None)
                            break
            if offset is not None:
                setattr(node, 'offset', offset)
        # recurse
        for attr in getattr(node, '__dict__', {}):
            child = getattr(node, attr)
            if isinstance(child, list):
                for c in child:
                    if hasattr(c, '__dict__'):
                        annotate_vars(c)
            elif hasattr(child, '__dict__'):
                annotate_vars(child)

    annotate_vars(ast_root)

    return


class MepaEmitter:
    """Emissor MEPA básico (gera código textual aceito por `mepa.py`)."""

    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.MP: List[str] = []  # linhas de assembly (já prontas)
        self.label_counter = 0
        self.pending_label: Optional[str] = None
        self.proc_labels: Dict[str, str] = {}
        self.proc_levels: Dict[str, int] = {}
        self.global_var_count = 0
        self._collect_proc_metadata()

    def new_label(self, prefix='L') -> str:
        """Gera novo rótulo no formato exigido (ex.: L1)."""
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"

    def _sanitize_label(self, name: str) -> str:
        """Sanitiza um nome para formar um rótulo válido: só A-Z0-9, começa com letra."""
        s = re.sub(r'[^0-9A-Za-z]', '_', name).upper()
        if not s or not s[0].isalpha():
            s = 'L' + s
        return s

    def _collect_proc_metadata(self):
        """Mapeia labels/níveis para cada sub-rotina conhecida."""
        used = set()

        def register(name: str, level: Optional[int]):
            base = self._sanitize_label(name)
            label = base
            i = 1
            while label in used:
                i += 1
                label = f"{base}{i}"
            used.add(label)
            self.proc_labels[name] = label
            if level is not None:
                self.proc_levels[name] = level

        for snap in self.symbol_table.archived_scopes:
            owner = snap.get('owner')
            if not owner:
                continue
            level = snap.get('level') or 1
            register(owner, level)

        for scope in self.symbol_table.scope_stack:
            for name, sym in scope.items():
                if getattr(sym, 'category', None) in ('proc', 'func') and name not in self.proc_labels:
                    level = getattr(sym, 'scope_level', 0) + 1
                    register(name, level)

    def emit(self, instr: str):
        """Adiciona uma linha de assembly textual (uppercase, com label se houver)."""
        line = instr.strip()
        if not line:
            return
        parts = line.split(None, 1)
        op_raw = parts[0].lower()
        mnemonic = INSTR_MNEMONICS.get(op_raw, op_raw.upper())
        rest = parts[1] if len(parts) > 1 else ''
        formatted = mnemonic if not rest else f"{mnemonic} {rest}"
        if self.pending_label:
            formatted = f"{self.pending_label}: {formatted}"
            self.pending_label = None
        self.MP.append(formatted)

    def emit_label(self, label: str):
        sanitized = self._sanitize_label(label)
        if self.pending_label is not None:
            # evitar rótulo sem instrução explícita
            self.emit('nop')
        self.pending_label = sanitized

    def finalize(self):
        """Garante que não haja rótulo pendente e adiciona 'END'."""
        if self.pending_label is not None:
            self.emit('nop')
        if not self.MP or self.MP[-1].strip().upper() != 'END':
            self.MP.append('END')

    # ----------------- helpers para instruções -----------------
    def ldct(self, k):
        self.emit(f"ldct {k}")

    def ldvl(self, level, offset):
        self.emit(f"ldvl {level},{offset}")

    def stvl(self, level, offset):
        self.emit(f"stvl {level},{offset}")

    def add(self):
        self.emit("add")

    def subt(self):
        self.emit("subt")

    def mult(self):
        self.emit("mult")

    def divi(self):
        self.emit("divi")

    def inv(self):
        self.emit("inv")

    def andd(self):
        self.emit("andd")

    def orr(self):
        self.emit("orr")

    def nott(self):
        self.emit("nott")

    def read(self):
        self.emit("read")

    def writ(self):
        self.emit("writ")

    def jmp(self, label):
        self.emit(f"jmp {label}")

    def jmpf(self, label):
        self.emit(f"jmpf {label}")

    def call(self, label, level):
        self.emit(f"call {label},{level}")

    def entproc(self, k):
        self.emit(f"entproc {k}")

    def retproc(self, n):
        self.emit(f"retproc {n}")

    def alloc(self, n):
        self.emit(f"alloc {n}")

    def dealloc(self, n):
        self.emit(f"dealloc {n}")

    # ----------------- geração por nós AST -----------------
    def gen_Program(self, node: Program):
        self.global_var_count = sum(len(vd.ids) for vd in node.block.var_decls)
        main_label = self._sanitize_label(node.name or 'main')
        self.emit_label(main_label)
        self.emit('main')  # inicializa D[0]
        if self.global_var_count:
            self.alloc(self.global_var_count)

        self.gen_Compound(node.block.compound)

        if self.global_var_count:
            self.dealloc(self.global_var_count)
        self.emit('halt')

        # gerar código das subrotinas após o corpo principal
        for subr in node.block.subr_decls:
            self.gen_Node(subr)

    def gen_Block(self, node):
        self.gen_Compound(node.compound)

    def gen_Compound(self, node):
        for cmd in node.commands:
            self.gen_Node(cmd)

    def gen_Node(self, node):
        # dispatcher simples
        tname = type(node).__name__
        meth = getattr(self, f'gen_{tname}', None)
        if meth:
            return meth(node)
        # nós sem geração direta (ou já processados)

    def gen_Assign(self, node):
        # gerar expressão e depois armazenar no identificador
        self.gen_Node(node.expr)
        # buscar símbolo para id
        sym = self._find_symbol(node.id, getattr(node, 'scope_level', None))
        if sym is None:
            # fallback: armazenar em global
            level = 0
            offset = 0
        else:
            level = sym.scope_level
            offset = getattr(sym, 'offset', 0)
        self.stvl(level, offset)

    def gen_Write(self, node):
        for expr in node.exprs:
            self.gen_Node(expr)
            self.writ()

    def gen_Read(self, node):
        # lê cada id e armazena
        for var_name in node.ids:
            self.read()
            # find symbol (level)
            sym = self._find_symbol(var_name, None)
            if sym:
                self.stvl(sym.scope_level, getattr(sym, 'offset', 0))
            else:
                # store to global 0,0 as fallback
                self.stvl(0, 0)

    def gen_If(self, node):
        else_label = self.new_label('L')
        end_label = self.new_label('L')
        self.gen_Node(node.cond)
        self.jmpf(else_label)
        self.gen_Node(node.then_cmd)
        self.jmp(end_label)
        self.emit_label(else_label)
        if node.else_cmd:
            self.gen_Node(node.else_cmd)
        self.emit_label(end_label)

    def gen_While(self, node):
        start = self.new_label('L')
        end = self.new_label('L')
        self.emit_label(start)
        self.gen_Node(node.cond)
        self.jmpf(end)
        self.gen_Node(node.body)
        self.jmp(start)
        self.emit_label(end)

    def gen_ProcCall(self, node):
        # empilha argumentos left-to-right
        for arg in node.args:
            self.gen_Node(arg)
        # encontrar símbolo da procedure
        sym = self._find_symbol(node.name, None)
        level = self.proc_levels.get(node.name, 1)
        label = self.proc_labels.get(node.name, node.name.upper())
        self.call(label, level)

    def gen_FuncCall(self, node):
        # empilha argumentos e chama, o valor retornado ficará no topo
        for arg in node.args:
            self.gen_Node(arg)
        sym = self._find_symbol(node.name, None)
        level = self.proc_levels.get(node.name, 1)
        label = self.proc_labels.get(node.name, node.name.upper())
        self.call(label, level)

    def gen_ProcDecl(self, node: ProcDecl):
        # Emitir rótulo da procedure e prologue/epilogue simples
        label = self.proc_labels.get(node.name, self._sanitize_label(node.name))
        self.emit_label(label)

        # tentar localizar símbolo declarador para obter counts/level
        proc_sym = None
        try:
            proc_sym = self._find_symbol(node.name, None)
        except Exception:
            proc_sym = None

        level = self.proc_levels.get(node.name, getattr(proc_sym, 'scope_level', 0) + 1)
        param_count = getattr(proc_sym, 'param_count', 0)
        local_count = getattr(proc_sym, 'local_count', 0)

        # prologue: preparar display/ativação e alocar locais
        self.entproc(level)
        if local_count:
            self.alloc(local_count)

        # Inicializar variáveis locais (zerar). Muitos exercícios esperam
        # que tipos escalares comecem com 0/false. Aqui buscamos o
        # snapshot arquivado que contém os símbolos do escopo e, para
        # cada variável local (não parâmetro), emitimos "ldct 0; stvl",
        # usando o nível léxico e o offset já calculados em compute_offsets.
        snap = None
        for s in self.symbol_table.archived_scopes:
            if s.get('owner') == node.name:
                snap = s
                break
        if snap:
            symbols = snap.get('symbols', {})
            # ordenar por offset para emitir em ordem (opcional)
            locals_to_init = []
            for nm, sym in symbols.items():
                # VarSymbol instances representam variáveis/params
                if getattr(sym, 'category', None) == 'var' and not getattr(sym, 'is_param', False):
                    off = getattr(sym, 'offset', None)
                    lvl = getattr(sym, 'scope_level', level)
                    if off is not None and lvl is not None:
                        locals_to_init.append((lvl, off))
            locals_to_init.sort(key=lambda t: t[1])
            for lvl, off in locals_to_init:
                self.ldct(0)
                self.stvl(lvl, off)

        # corpo
        self.gen_Block(node.block)

        # epílogo: desalocar locais e retornar
        if local_count:
            self.dealloc(local_count)
        self.retproc(param_count)

    def gen_FuncDecl(self, node: FuncDecl):
        # Similar a procedure, com suporte a valor de retorno pelo topo da pilha
        label = self.proc_labels.get(node.name, self._sanitize_label(node.name))
        self.emit_label(label)

        proc_sym = None
        try:
            proc_sym = self._find_symbol(node.name, None)
        except Exception:
            proc_sym = None

        level = self.proc_levels.get(node.name, getattr(proc_sym, 'scope_level', 0) + 1)
        param_count = getattr(proc_sym, 'param_count', 0)
        local_count = getattr(proc_sym, 'local_count', 0)

        # prologue
        self.entproc(level)
        if local_count:
            self.alloc(local_count)

        # Inicializar locais (mesma lógica que em procedures)
        snap = None
        for s in self.symbol_table.archived_scopes:
            if s.get('owner') == node.name:
                snap = s
                break
        if snap:
            symbols = snap.get('symbols', {})
            locals_to_init = []
            for nm, sym in symbols.items():
                if getattr(sym, 'category', None) == 'var' and not getattr(sym, 'is_param', False):
                    off = getattr(sym, 'offset', None)
                    lvl = getattr(sym, 'scope_level', level)
                    if off is not None and lvl is not None:
                        locals_to_init.append((lvl, off))
            locals_to_init.sort(key=lambda t: t[1])
            for lvl, off in locals_to_init:
                self.ldct(0)
                self.stvl(lvl, off)

        # corpo
        self.gen_Block(node.block)

        # epílogo
        if local_count:
            self.dealloc(local_count)
        self.retproc(param_count)

    def gen_BinOp(self, node):
        self.gen_Node(node.left)
        self.gen_Node(node.right)
        op = node.op
        if op == '+':
            self.add()
        elif op == '-':
            self.subt()
        elif op == '*':
            self.mult()
        elif op == 'div':
            self.divi()
        elif op in ['=', '==']:
            self.emit('eql')
        elif op == '<>':
            self.emit('dif')
        elif op == '<':
            self.emit('less')
        elif op == '>':
            self.emit('grt')
        elif op == '<=':
            self.emit('leq')
        elif op == '>=':
            self.emit('geq')
        elif op == 'and':
            self.andd()
        elif op == 'or':
            self.orr()
        else:
            # operador desconhecido: nenhum emit
            pass

    def gen_UnOp(self, node):
        self.gen_Node(node.expr)
        if node.op == '-':
            self.inv()
        elif node.op == 'not':
            self.nott()

    def gen_Num(self, node):
        self.ldct(node.value)

    def gen_Bool(self, node):
        # assumir 'true'/'false' mapeados para 1/0
        val = 1 if str(node.value).lower() in ('true','1') else 0
        self.ldct(val)

    def gen_Var(self, node):
        # carregar variável no topo usando offset anotado quando disponível
        lvl = getattr(node, 'scope_level', None)
        off = getattr(node, 'offset', None)
        if off is not None and lvl is not None:
            self.ldvl(lvl, off)
        else:
            # tentar resolver por símbolo
            sym = self._find_symbol(node.name, lvl)
            if sym:
                self.ldvl(sym.scope_level, getattr(sym, 'offset', 0))
            else:
                # fallback: 0
                self.ldct(0)

    # ----------------- utilitários -----------------
    def _find_symbol(self, name, level_hint):
        """Tenta localizar símbolo pelo nome e nível (procura em archived
        snapshots caso level_hint seja fornecido).
        """
        # procurar no escopo global
        if level_hint == 0:
            return self.symbol_table.scope_stack[0].get(name)

        # procurar em snapshots por level
        if level_hint is not None:
            for snap in self.symbol_table.archived_scopes:
                if snap.get('level') == level_hint:
                    symbols = snap.get('symbols', {})
                    if name in symbols:
                        return symbols[name]

        # fallback: procurar em scope_stack (do topo para a base)
        for sc in reversed(self.symbol_table.scope_stack):
            if name in sc:
                return sc[name]

        # fallback: procurar em archived scopes by owner name
        for snap in self.symbol_table.archived_scopes:
            symbols = snap.get('symbols', {})
            if name in symbols:
                return symbols[name]

        return None


def emit_mepa_file(ast_root: Program, symbol_table, out_path: str):
    """Convenience: calcula offsets, emite e escreve arquivo MEPA.

    O arquivo conterá uma instrução por linha (formato interno, minúsculo).
    """
    # garantir offsets
    compute_offsets(ast_root, symbol_table)

    emitter = MepaEmitter(symbol_table)
    emitter.gen_Program(ast_root)
    emitter.finalize()

    # escrever arquivo
    with open(out_path, 'w', encoding='utf-8') as f:
        for line in emitter.MP:
            f.write(line + '\n')

    return emitter.MP
