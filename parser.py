import ply.yacc as yacc
from lexer import tokens, lexer

# AST nodes
class Program:
    def __init__(self, name, block):
        self.name = name
        self.block = block
    def __repr__(self):
        return f"Program({self.name}, {self.block})"

class Block:
    def __init__(self, var_decls, subr_decls, compound):
        self.var_decls = var_decls or []
        self.subr_decls = subr_decls or []
        self.compound = compound
    def __repr__(self):
        return f"Block(vars={self.var_decls}, subrs={self.subr_decls}, compound={self.compound})"

class VarDecl:
    def __init__(self, ids, tipo):
        self.ids = ids
        self.tipo = tipo
    def __repr__(self):
        return f"VarDecl({self.ids}:{self.tipo})"

class Compound:
    def __init__(self, commands):
        self.commands = commands
    def __repr__(self):
        return f"Compound({self.commands})"

class Assign:
    def __init__(self, id, expr):
        self.id = id
        self.expr = expr
    def __repr__(self):
        return f"Assign({self.id} := {self.expr})"

class Write:
    def __init__(self, exprs):
        self.exprs = exprs
    def __repr__(self):
        return f"Write({self.exprs})"

class Read:
    def __init__(self, ids):
        self.ids = ids
    def __repr__(self):
        return f"Read({self.ids})"

class If:
    def __init__(self, cond, then_cmd, else_cmd=None):
        self.cond = cond
        self.then_cmd = then_cmd
        self.else_cmd = else_cmd
    def __repr__(self):
        return f"If({self.cond}, then={self.then_cmd}, else={self.else_cmd})"

class While:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body
    def __repr__(self):
        return f"While({self.cond}, {self.body})"

class ProcCall:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or []
    def __repr__(self):
        return f"ProcCall({self.name}, {self.args})"

class FuncCall:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or []
    def __repr__(self):
        return f"FuncCall({self.name}, {self.args})"

class BinOp:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class UnOp:
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr
    def __repr__(self):
        return f"({self.op}{self.expr})"

class Var:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"{self.name}"

class Num:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"{self.value}"

class Bool:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"{self.value}"

# Precedência
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIV'),
    ('right', 'NOT', 'UMINUS'),
)

# <programa> ::= 'program' <identificador> ';' <bloco> '.'
def p_program(p):
    'program : PROGRAM ID SEMI bloco DOT'
    p[0] = Program(p[2], p[4])

# <bloco> ::= [<seção_declaração_variáveis>] [<seção_declaração_subrotinas>] <comando_composto>
def p_bloco(p):
    'bloco : opt_var_section opt_subr_section comando_composto'
    p[0] = Block(p[1], p[2], p[3])

# [<seção_declaração_variáveis>]
def p_opt_var_section(p):
    '''opt_var_section : var_section
                       | empty'''
    p[0] = p[1]

# <seção_declaração_variáveis> ::= 'var' <declaração_variáveis> ';' { <declaração_variáveis> ';' }
def p_var_section(p):
    'var_section : VAR decl_vars SEMI var_decl_list'
    p[0] = [p[2]] + p[4]

def p_var_decl_list(p):
    '''var_decl_list : decl_vars SEMI var_decl_list
                     | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[1]] + p[3]

# <declaração_variáveis> ::= <lista_identificadores> ':' <tipo>
def p_decl_vars(p):
    'decl_vars : lista_identificadores COLON tipo'
    p[0] = VarDecl(p[1], p[3])

# <lista_identificadores> ::= <identificador> { ',' <identificador> }
def p_lista_identificadores(p):
    'lista_identificadores : ID id_list_tail'
    p[0] = [p[1]] + p[2]

def p_id_list_tail(p):
    '''id_list_tail : COMMA ID id_list_tail
                    | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]

# <tipo> ::= 'boolean' | 'integer'
def p_tipo(p):
    '''tipo : INTEGER
            | BOOLEAN'''
    p[0] = p[1]

# [<seção_declaração_subrotinas>] - placeholder
def p_opt_subr_section(p):
    'opt_subr_section : empty'
    p[0] = []

# <comando_composto> ::= 'begin' <comando> { ';' <comando> } 'end'
# IMPORTANTE: deve ter pelo menos um comando!
def p_comando_composto(p):
    'comando_composto : BEGIN comando cmd_list_tail END'
    p[0] = Compound([p[2]] + p[3])

def p_cmd_list_tail(p):
    '''cmd_list_tail : SEMI comando cmd_list_tail
                     | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]

# <comando> ::= <atribuição> | <chamada_procedimento> | ...
def p_comando(p):
    '''comando : comando_id
               | condicional
               | repeticao
               | leitura
               | escrita
               | comando_composto'''
    p[0] = p[1]

# Unifica atribuição e chamada de procedimento (ambos começam com ID)
def p_comando_id(p):
    '''comando_id : ID ASSIGN expressao
                  | ID LPAREN lista_expressoes RPAREN
                  | ID LPAREN RPAREN
                  | ID'''
    if len(p) == 4 and p[2] == ':=':
        # atribuição
        p[0] = Assign(p[1], p[3])
    elif len(p) == 5:
        # chamada com argumentos
        p[0] = ProcCall(p[1], p[3])
    elif len(p) == 4:
        # chamada sem argumentos (com parênteses vazios)
        p[0] = ProcCall(p[1], [])
    else:
        # ID sozinho - chamada sem parênteses
        p[0] = ProcCall(p[1], [])

# <condicional> ::= 'if' <expressão> 'then' <comando> [ 'else' <comando> ]
def p_condicional(p):
    '''condicional : IF expressao THEN comando
                   | IF expressao THEN comando ELSE comando'''
    if len(p) == 5:
        p[0] = If(p[2], p[4])
    else:
        p[0] = If(p[2], p[4], p[6])

# <repetição> ::= 'while' <expressão> 'do' <comando>
def p_repeticao(p):
    'repeticao : WHILE expressao DO comando'
    p[0] = While(p[2], p[4])

# <leitura> ::= 'read' '(' <lista_identificadores> ')'
def p_leitura(p):
    'leitura : READ LPAREN lista_identificadores RPAREN'
    p[0] = Read(p[3])

# <escrita> ::= 'write' '(' <lista_expressões> ')'
def p_escrita(p):
    'escrita : WRITE LPAREN lista_expressoes RPAREN'
    p[0] = Write(p[3])

# <lista_expressões> ::= <expressão> { ',' <expressão> }
def p_lista_expressoes(p):
    'lista_expressoes : expressao expr_list_tail'
    p[0] = [p[1]] + p[2]

def p_expr_list_tail(p):
    '''expr_list_tail : COMMA expressao expr_list_tail
                      | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]

# <expressão> ::= <expressão_simples> [ <relação> <expressão_simples> ]
def p_expressao(p):
    '''expressao : expressao_simples
                 | expressao_simples relacao expressao_simples'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinOp(p[2], p[1], p[3])

# <relação> ::= '=' | '<>' | '<' | '<=' | '>' | '>='
def p_relacao(p):
    '''relacao : EQ
               | NEQ
               | LT
               | LE
               | GT
               | GE'''
    p[0] = p[1]

# <expressão_simples> ::= <termo> { ( '+' | '-' | 'or' ) <termo> }
def p_expressao_simples(p):
    '''expressao_simples : termo
                         | expressao_simples PLUS termo
                         | expressao_simples MINUS termo
                         | expressao_simples OR termo'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinOp(p[2], p[1], p[3])

# <termo> ::= <fator> { ( '*' | 'div' | 'and' ) <fator> }
def p_termo(p):
    '''termo : fator
             | termo TIMES fator
             | termo DIV fator
             | termo AND fator'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinOp(p[2], p[1], p[3])

# <fator> ::= <variável> | <número> | <lógico> | <chamada_função> | '(' <expressão> ')' | 'not' <fator> | '-' <fator>
# PROBLEMA: <variável> e <chamada_função> ambos começam com ID
# Solução: unificar em uma regra
def p_fator(p):
    '''fator : ID
             | ID LPAREN lista_expressoes RPAREN
             | ID LPAREN RPAREN
             | NUM
             | FALSE
             | TRUE
             | LPAREN expressao RPAREN
             | NOT fator
             | MINUS fator %prec UMINUS'''
    if len(p) == 2:
        if isinstance(p[1], int):
            p[0] = Num(p[1])
        elif p[1] in ('false', 'true'):
            p[0] = Bool(p[1])
        else:
            # ID sozinho = variável
            p[0] = Var(p[1])
    elif len(p) == 5:
        # ID LPAREN lista_expressoes RPAREN = chamada de função
        p[0] = FuncCall(p[1], p[3])
    elif len(p) == 4:
        # ID LPAREN RPAREN = chamada de função sem args
        p[0] = FuncCall(p[1], [])
    elif p[1] == '(':
        # LPAREN expressao RPAREN
        p[0] = p[2]
    elif p[1] == 'not':
        # NOT fator
        p[0] = UnOp('not', p[2])
    else:
        # MINUS fator
        p[0] = UnOp('-', p[2])

def p_empty(p):
    'empty :'
    p[0] = []

def p_error(p):
    if p:
        print(f"Erro sintático: token inesperado '{p.value}' na linha {p.lineno}")
    else:
        print("Erro sintático: fim de arquivo inesperado")

# Construir parser
parser = yacc.yacc()