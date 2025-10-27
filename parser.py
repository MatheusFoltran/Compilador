import sys
import ply.yacc as yacc
from lexer import tokens, lexer
from ast_nodes import *

# Precedência e associatividade
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
    p[0] = p[1] if p[1] is not None else []

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
    '''comando : atribuicao
               | chamada_procedimento
               | condicional
               | repeticao
               | leitura
               | escrita
               | comando_composto'''
    p[0] = p[1]

# <atribuição> ::= <identificador> ':=' <expressão>
def p_atribuicao(p):
    'atribuicao : ID ASSIGN expressao'
    p[0] = Assign(p[1], p[3])

# <chamada_procedimento> ::= <identificador> '(' [ <lista_expressões> ] ')'
# IMPORTANTE: Segundo a gramática, chamada de procedimento DEVE ter parênteses!
def p_chamada_procedimento(p):
    '''chamada_procedimento : ID LPAREN lista_expressoes RPAREN
                            | ID LPAREN RPAREN'''
    if len(p) == 5:
        p[0] = ProcCall(p[1], p[3])
    else:
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

# <fator> ::= <variável> | <número> | <lógico> | <chamada_função> 
#           | '(' <expressão> ')' | 'not' <fator> | '-' <fator>
# NOTA: Unificamos ID (variável) e ID(...) (função) aqui para evitar conflito shift/reduce
def p_fator(p):
    '''fator : ID
             | ID LPAREN lista_expressoes RPAREN
             | ID LPAREN RPAREN
             | NUM
             | logico
             | LPAREN expressao RPAREN
             | NOT fator
             | MINUS fator %prec UMINUS'''
    if len(p) == 2:
        if isinstance(p[1], str):
            # ID sozinho = variável
            p[0] = Var(p[1])
        else:
            # NUM ou logico já processado
            p[0] = p[1]
    elif len(p) == 5:
        # ID LPAREN lista_expressoes RPAREN = chamada de função
        p[0] = FuncCall(p[1], p[3])
    elif len(p) == 4:
        if p[1] == '(':
            # LPAREN expressao RPAREN
            p[0] = p[2]
        else:
            # ID LPAREN RPAREN = chamada de função sem args
            p[0] = FuncCall(p[1], [])
    else:
        # NOT fator ou MINUS fator
        p[0] = UnOp(p[1], p[2])

# Removemos as regras separadas de variavel e chamada_funcao
# pois causavam conflito shift/reduce

# <lógico> ::= 'false' | 'true'
def p_logico(p):
    '''logico : FALSE
              | TRUE'''
    p[0] = Bool(p[1])

# Produção vazia
def p_empty(p):
    'empty :'
    pass

# Tratamento de erros
def p_error(p):
    if p:
        print(f"ERRO SINTÁTICO na linha {p.lineno}: token inesperado '{p.value}'")
        # Abortar parsing imediatamente
        raise SyntaxError(f"Erro sintático na linha {p.lineno}")
    else:
        print("ERRO SINTÁTICO: fim de arquivo inesperado (EOF)")
        raise SyntaxError("Fim de arquivo inesperado")

# Construir parser
def make_parser():
    return yacc.yacc(start='program')

# Teste do parser
if __name__ == '__main__':
    # Ler entrada do stdin ou arquivo
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                data = f.read()
        except FileNotFoundError:
            print(f"Erro: arquivo '{sys.argv[1]}' não encontrado.")
            sys.exit(1)
    else:
        data = sys.stdin.read()
    
    if not data.strip():
        print("Erro: entrada vazia.")
        sys.exit(1)
    
    # Criar parser e fazer análise
    parser = make_parser()
    
    try:
        resultado = parser.parse(data, lexer=lexer)
        
        if resultado:
            print("\n" + "=" * 60)
            print("ANÁLISE SINTÁTICA BEM-SUCEDIDA")
            print("=" * 60)
            print("\nÁRVORE SINTÁTICA ABSTRATA (AST):\n")
            
            # Escolha o formato:
            # write_ast(resultado)           # Formato S-expression (compacto)
            write_ast_verbose(resultado)     # Formato detalhado e legível
            
            print("\n" + "=" * 60)
        else:
            print("\n" + "=" * 60)
            print("ANÁLISE SINTÁTICA FALHOU")
            print("=" * 60)
            sys.exit(1)
    except SyntaxError:
        print("\n" + "=" * 60)
        print("ANÁLISE SINTÁTICA ABORTADA")
        print("=" * 60)
        sys.exit(1)