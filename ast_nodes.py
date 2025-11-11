from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import sys

class No:
    """Classe base para todos os nós da AST"""
    pass

class Cmd:
    """Classe base para comandos"""
    pass

class Expr:
    """Classe base para expressões"""
    pass

@dataclass
class Program(No):
    name: str
    block: 'Block'

@dataclass
class Block(No):
    var_decls: List['VarDecl']
    subr_decls: List  # Para procedures e functions
    compound: 'Compound'

@dataclass
class VarDecl(No):
    ids: List[str]
    tipo: str  # 'integer' ou 'boolean'

@dataclass
class ProcDecl(No):
    """Declaração de procedure"""
    name: str
    params: List['ParamDecl']
    block: 'Block'

@dataclass
class FuncDecl(No):
    """Declaração de function"""
    name: str
    params: List['ParamDecl']
    return_type: str  # 'integer' ou 'boolean'
    block: 'Block'

@dataclass
class ParamDecl(No):
    """Declaração de parâmetro"""
    ids: List[str]
    tipo: str  # 'integer' ou 'boolean'

@dataclass
class Compound(No):
    commands: List[Cmd]  # Lista de comandos

@dataclass
class Assign(Cmd):
    id: str
    expr: Expr
    # Anotações semânticas
    var_type: Optional[str] = None       # Tipo da variável
    var_scope_level: Optional[int] = None  # Nível léxico
    var_offset: Optional[int] = None       # Offset na pilha

@dataclass
class Write(Cmd):
    exprs: List[Expr]
    # Anotações semânticas
    expr_types: Optional[List[str]] = None  # Tipos das expressões a escrever

@dataclass
class Read(Cmd):
    ids: List[str]
    # Anotações semânticas
    var_types: Optional[List[str]] = None  # Tipos das variáveis sendo lidas

@dataclass
class If(Cmd):
    cond: Expr
    then_cmd: Cmd
    else_cmd: Optional[Cmd] = None
    # Anotações semânticas
    cond_type: Optional[str] = None  # Tipo da condição (deve ser boolean)

@dataclass
class While(Cmd):
    cond: Expr
    body: Cmd
    # Anotações semânticas
    cond_type: Optional[str] = None  # Tipo da condição (deve ser boolean)

@dataclass
class ProcCall(Cmd):
    name: str
    args: List[Expr]
    # Anotações semânticas
    param_types: Optional[List[str]] = None  # Tipos dos parâmetros (para verificação)

@dataclass
class FuncCall(Expr):
    name: str
    args: List[Expr]
    # Anotações semânticas
    return_type: Optional[str] = None        # Tipo de retorno
    param_types: Optional[List[str]] = None  # Tipos dos parâmetros (para verificação)

@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr
    # Anotação semântica: tipo do resultado
    result_type: Optional[str] = None

@dataclass
class UnOp(Expr):
    op: str
    expr: Expr
    # Anotação semântica: tipo do resultado
    result_type: Optional[str] = None

@dataclass
class Var(Expr):
    name: str
    # Anotações semânticas (preenchidas durante análise semântica)
    tipo: Optional[str] = None          # Tipo da variável
    scope_level: Optional[int] = None   # Nível léxico (0=global, 1+=local)
    offset: Optional[int] = None        # Offset na pilha (para geração de código)

@dataclass
class Num(Expr):
    value: int
    # Tipo é sempre 'integer', mas anotamos para uniformidade
    tipo: str = 'integer'

@dataclass
class Bool(Expr):
    value: str  # 'true' ou 'false'
    # Tipo é sempre 'boolean'
    tipo: str = 'boolean'


def write_ast_verbose(no, out=sys.stdout, indent=0):
    """Escreve a AST em formato mais detalhado e legível"""
    prefix = "  " * indent
    
    if isinstance(no, Program):
        out.write(f"{prefix}PROGRAMA: {no.name}\n")
        out.write(f"{prefix}├─ BLOCO:\n")
        write_ast_verbose(no.block, out, indent + 1)
        return
    
    if isinstance(no, Block):
        has_vars = bool(no.var_decls)
        has_subrs = bool(no.subr_decls)
        
        if has_vars:
            out.write(f"{prefix}├─ VARIÁVEIS:\n")
            for vd in no.var_decls:
                write_ast_verbose(vd, out, indent + 1)
        
        if has_subrs:
            out.write(f"{prefix}├─ SUBROTINAS:\n")
            for subr in no.subr_decls:
                write_ast_verbose(subr, out, indent + 1)
        
        symbol = "└─" if has_vars or has_subrs else "├─"
        out.write(f"{prefix}{symbol} COMANDOS:\n")
        write_ast_verbose(no.compound, out, indent + 1)
        return
    
    if isinstance(no, VarDecl):
        ids_str = ", ".join(no.ids)
        out.write(f"{prefix}├─ {ids_str} : {no.tipo}\n")
        return
    
    if isinstance(no, ProcDecl):
        out.write(f"{prefix}├─ PROCEDURE {no.name}")
        if no.params:
            out.write("(")
            for i, param in enumerate(no.params):
                if i > 0:
                    out.write("; ")
                ids_str = ", ".join(param.ids)
                out.write(f"{ids_str}: {param.tipo}")
            out.write(")")
        out.write("\n")
        write_ast_verbose(no.block, out, indent + 1)
        return
    
    if isinstance(no, FuncDecl):
        out.write(f"{prefix}├─ FUNCTION {no.name}")
        if no.params:
            out.write("(")
            for i, param in enumerate(no.params):
                if i > 0:
                    out.write("; ")
                ids_str = ", ".join(param.ids)
                out.write(f"{ids_str}: {param.tipo}")
            out.write(")")
        out.write(f" : {no.return_type}\n")
        write_ast_verbose(no.block, out, indent + 1)
        return
    
    if isinstance(no, Compound):
        for i, cmd in enumerate(no.commands):
            is_last = i == len(no.commands) - 1
            symbol = "└─" if is_last else "├─"
            out.write(f"{prefix}{symbol} ")
            write_ast_verbose(cmd, out, indent + 1)
        return
    
    if isinstance(no, Assign):
        out.write(f"ATRIBUIÇÃO: {no.id} := ")
        write_ast_verbose(no.expr, out, 0)
        out.write("\n")
        return
    
    if isinstance(no, Write):
        out.write("ESCREVER: ")
        for i, expr in enumerate(no.exprs):
            if i > 0:
                out.write(", ")
            write_ast_verbose(expr, out, 0)
        out.write("\n")
        return
    
    if isinstance(no, Read):
        ids_str = ", ".join(no.ids)
        out.write(f"LER: {ids_str}\n")
        return
    
    if isinstance(no, If):
        out.write("SE ")
        write_ast_verbose(no.cond, out, 0)
        out.write(" ENTÃO:\n")
        write_ast_verbose(no.then_cmd, out, indent + 1)
        if no.else_cmd:
            out.write(f"{prefix}SENÃO:\n")
            write_ast_verbose(no.else_cmd, out, indent + 1)
        return
    
    if isinstance(no, While):
        out.write("ENQUANTO ")
        write_ast_verbose(no.cond, out, 0)
        out.write(" FAÇA:\n")
        write_ast_verbose(no.body, out, indent + 1)
        return
    
    if isinstance(no, ProcCall):
        out.write(f"CHAMAR_PROC {no.name}(")
        for i, arg in enumerate(no.args):
            if i > 0:
                out.write(", ")
            write_ast_verbose(arg, out, 0)
        out.write(")")
        return
    
    if isinstance(no, FuncCall):
        out.write(f"{no.name}(")
        for i, arg in enumerate(no.args):
            if i > 0:
                out.write(", ")
            write_ast_verbose(arg, out, 0)
        out.write(")")
        return
    
    if isinstance(no, BinOp):
        out.write("(")
        write_ast_verbose(no.left, out, 0)
        out.write(f" {no.op} ")
        write_ast_verbose(no.right, out, 0)
        out.write(")")
        return
    
    if isinstance(no, UnOp):
        out.write(f"({no.op}")
        write_ast_verbose(no.expr, out, 0)
        out.write(")")
        return
    
    if isinstance(no, Num):
        out.write(str(no.value))
        return
    
    if isinstance(no, Bool):
        out.write(no.value)
        return
    
    if isinstance(no, Var):
        out.write(no.name)
        return
    
    out.write(f"<{type(no).__name__}>")

def write_ast(no, out=sys.stdout, indent=0):
    """Escreve a AST em formato S-expression (Lisp-like)"""
    
    if isinstance(no, Program):
        out.write(f"(program {no.name}\n")
        out.write("  " * (indent + 1))
        write_ast(no.block, out, indent + 1)
        out.write(")")
        return
    
    if isinstance(no, Block):
        out.write("(block\n")
        # Variáveis
        if no.var_decls:
            out.write("  " * (indent + 1) + "(vars\n")
            for vd in no.var_decls:
                out.write("  " * (indent + 2))
                write_ast(vd, out, indent + 2)
                out.write("\n")
            out.write("  " * (indent + 1) + ")\n")
        # Subrotinas
        if no.subr_decls:
            out.write("  " * (indent + 1) + "(subrs\n")
            for subr in no.subr_decls:
                out.write("  " * (indent + 2))
                write_ast(subr, out, indent + 2)
                out.write("\n")
            out.write("  " * (indent + 1) + ")\n")
        # Comando composto
        out.write("  " * (indent + 1))
        write_ast(no.compound, out, indent + 1)
        out.write("\n" + "  " * indent + ")")
        return
    
    if isinstance(no, VarDecl):
        ids_str = " ".join(no.ids)
        out.write(f"(var-decl ({ids_str}) {no.tipo})")
        return
    
    if isinstance(no, ProcDecl):
        out.write(f"(proc-decl {no.name}")
        if no.params:
            out.write(" (params")
            for param in no.params:
                out.write(" ")
                write_ast(param, out, indent)
            out.write(")")
        out.write("\n" + "  " * (indent + 1))
        write_ast(no.block, out, indent + 1)
        out.write(")")
        return
    
    if isinstance(no, FuncDecl):
        out.write(f"(func-decl {no.name}")
        if no.params:
            out.write(" (params")
            for param in no.params:
                out.write(" ")
                write_ast(param, out, indent)
            out.write(")")
        out.write(f" {no.return_type}\n" + "  " * (indent + 1))
        write_ast(no.block, out, indent + 1)
        out.write(")")
        return
    
    if isinstance(no, ParamDecl):
        ids_str = " ".join(no.ids)
        out.write(f"(param ({ids_str}) {no.tipo})")
        return
    
    if isinstance(no, Compound):
        out.write("(compound")
        for cmd in no.commands:
            out.write("\n" + "  " * (indent + 1))
            write_ast(cmd, out, indent + 1)
        out.write(")")
        return
    
    if isinstance(no, Assign):
        out.write(f"(assign {no.id} ")
        write_ast(no.expr, out, indent)
        out.write(")")
        return
    
    if isinstance(no, Write):
        out.write("(write")
        for expr in no.exprs:
            out.write(" ")
            write_ast(expr, out, indent)
        out.write(")")
        return
    
    if isinstance(no, Read):
        ids_str = " ".join(no.ids)
        out.write(f"(read {ids_str})")
        return
    
    if isinstance(no, If):
        out.write("(if ")
        write_ast(no.cond, out, indent)
        out.write("\n" + "  " * (indent + 1) + "(then ")
        write_ast(no.then_cmd, out, indent + 1)
        out.write(")")
        if no.else_cmd:
            out.write("\n" + "  " * (indent + 1) + "(else ")
            write_ast(no.else_cmd, out, indent + 1)
            out.write(")")
        out.write(")")
        return
    
    if isinstance(no, While):
        out.write("(while ")
        write_ast(no.cond, out, indent)
        out.write("\n" + "  " * (indent + 1))
        write_ast(no.body, out, indent + 1)
        out.write(")")
        return
    
    if isinstance(no, ProcCall):
        out.write(f"(proc-call {no.name}")
        if no.args:
            for arg in no.args:
                out.write(" ")
                write_ast(arg, out, indent)
        out.write(")")
        return
    
    if isinstance(no, FuncCall):
        out.write(f"(func-call {no.name}")
        if no.args:
            for arg in no.args:
                out.write(" ")
                write_ast(arg, out, indent)
        out.write(")")
        return
    
    if isinstance(no, BinOp):
        out.write(f"({no.op} ")
        write_ast(no.left, out, indent)
        out.write(" ")
        write_ast(no.right, out, indent)
        out.write(")")
        return
    
    if isinstance(no, UnOp):
        out.write(f"({no.op} ")
        write_ast(no.expr, out, indent)
        out.write(")")
        return
    
    if isinstance(no, Num):
        out.write(str(no.value))
        return
    
    if isinstance(no, Bool):
        out.write(no.value)
        return
    
    if isinstance(no, Var):
        out.write(no.name)
        return
    
    # Fallback
    out.write(f"(unknown {type(no).__name__})")