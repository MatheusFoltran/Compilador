from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import sys

class No:
    """Classe base para todos os nós da AST"""
    pass

@dataclass
class Program(No):
    name: str
    block: Block

@dataclass
class Block(No):
    var_decls: List[VarDecl]
    subr_decls: List  # Para procedures e functions (não implementado ainda)
    compound: Compound

@dataclass
class VarDecl(No):
    ids: List[str]
    tipo: str  # 'integer' ou 'boolean'

@dataclass
class Compound(No):
    commands: List[No]  # Lista de comandos

@dataclass
class Assign(No):
    id: str
    expr: No

@dataclass
class Write(No):
    exprs: List[No]

@dataclass
class Read(No):
    ids: List[str]

@dataclass
class If(No):
    cond: No
    then_cmd: No
    else_cmd: Optional[No] = None

@dataclass
class While(No):
    cond: No
    body: No

@dataclass
class ProcCall(No):
    name: str
    args: List[No]

@dataclass
class FuncCall(No):
    name: str
    args: List[No]

@dataclass
class BinOp(No):
    op: str
    left: No
    right: No

@dataclass
class UnOp(No):
    op: str
    expr: No

@dataclass
class Var(No):
    name: str

@dataclass
class Num(No):
    value: int

@dataclass
class Bool(No):
    value: str  # 'true' ou 'false'


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
        # Subrotinas (vazio por enquanto)
        if no.subr_decls:
            out.write("  " * (indent + 1) + "(subrs ...)\n")
        # Comando composto
        out.write("  " * (indent + 1))
        write_ast(no.compound, out, indent + 1)
        out.write("\n" + "  " * indent + ")")
        return
    
    if isinstance(no, VarDecl):
        ids_str = " ".join(no.ids)
        out.write(f"(var-decl ({ids_str}) {no.tipo})")
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