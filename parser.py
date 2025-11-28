import sys
import ply.yacc as yacc
from lexer import tokens, lexer
from ast_nodes import *

"""
ESTRATÉGIA DE TRATAMENTO DE ERROS:

1. REGRAS DE ERRO ESPECÍFICAS (p_xxx_error):
   - Capturam erros em contextos específicos da gramática
   - Fornecem mensagens de erro detalhadas e contextuais
   - Constroem AST parcial sempre que possível
   - Exemplos: falta de ';', '(' vazio em functions, etc.

2. FUNÇÃO p_error (GENÉRICA):
   - Último recurso quando nenhuma regra específica casa
   - Mensagem genérica: "token inesperado"
   - EXCEÇÃO: Operadores seguidos (ex: a + * b) caem aqui por limitação do PLY
     - PLY não consegue prever que operador é inválido até tentar todas as regras
     - Para operadores, damos mensagem contextual sobre o que era esperado
   - Faz sincronização (modo pânico) em pontos seguros

3. FLAG 'recovering':
   - Evita mensagens de erro em cascata
   - Resetada quando parsing volta ao normal
   - Importante para não poluir a saída com erros duplicados
"""

# Contador de erros
error_count = 0
# Flag para evitar erros em cascata
recovering = False
# Rastreamento do último token para mensagens contextuais
last_token = None
tracked_lexer = None
# Último parser construído (usado por p_error para evitar NameError)
_active_parser = None

# Precedência e associatividade
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIV'),
    ('right', 'NOT', 'UMINUS'),
)

# Wrapper para rastrear tokens (mantém histórico de 2 tokens)
class TokenTracker:
    def __init__(self, lexer):
        self.lexer = lexer
        self.prev_token = None
        self.last_token = None
    
    def token(self):
        global last_token
        tok = self.lexer.token()
        if tok:
            self.prev_token = self.last_token
            self.last_token = tok
            last_token = tok
        return tok
    
    def input(self, data):
        self.lexer.input(data)
        self.prev_token = None
        self.last_token = None
        # Garantir que o contador de linhas do lexer seja reiniciado
        # Ao reutilizar o mesmo objeto lexer entre duas varreduras (lista de tokens
        # e parsing) o atributo `lineno` permanece no valor final da passada
        # anterior, produzindo números de linha incorretos nas mensagens de erro.
        try:
            self.lexer.lineno = 1
        except Exception:
            pass

# <programa> ::= 'program' <identificador> ';' <bloco> '.'
def p_program(p):
    'program : PROGRAM ID SEMI bloco DOT'
    p[0] = Program(p[2], p[4])

# Erro: identificador faltando ou ponto-e-vírgula faltando ou ponto final faltando
def p_program_error(p):
    '''program : PROGRAM error SEMI bloco DOT
               | PROGRAM ID error bloco DOT
               | PROGRAM ID SEMI bloco error
               | PROGRAM ID VAR bloco DOT'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        
        if len(p) == 5:
            # PROGRAM ID SEMI bloco (sem o ponto final)
            print(f"ERRO SINTÁTICO: fim de arquivo inesperado (EOF). O parser esperava o token '.' para finalizar o programa. Linha {p.lineno(4)}")
            p[0] = Program(p[2], p[4])
        elif p[2] == 'error':
            print(f"ERRO SINTÁTICO na linha {p.lineno(2)}: identificador esperado após 'program'")
            p[0] = Program('error_program', p[4])
        elif p[3] == 'error':
            print(f"ERRO SINTÁTICO na linha {p.lineno(3)}: ';' esperado após o identificador do programa")
            p[0] = Program(p[2], p[4])
        elif len(p) > 3 and hasattr(p.slice[3], 'type') and p.slice[3].type == 'VAR':
            # Caso comum: encontrou 'var' em vez de ';' após PROGRAM ID
            # Mensagem formatada para bater com a planilha de testes
            print(f"Palavra-chave 'var' inesperada. O parser esperava o token ';' para finalizar a declaração do programa. Linha {p.lineno(3)}")
            p[0] = Program(p[2], p[4])
        elif p[5] == 'error':
            print(f"ERRO SINTÁTICO: fim de arquivo inesperado (EOF). O parser esperava o token '.' para finalizar o programa. Linha {p.lineno(4)}")
            p[0] = Program(p[2], p[4])
        else:
            p[0] = Program(p[2] if p[2] != 'error' else 'error_program', p[4])
    else:
        # Já estamos recuperando, apenas construir AST parcial
        p[0] = Program(p[2] if len(p) > 2 and p[2] != 'error' else 'error_program', 
                      p[4] if len(p) > 4 else Block([], [], Compound([])))

# <bloco> ::= [<seção_declaração_variáveis>] [<seção_declaração_subrotinas>] <comando_composto>
def p_bloco(p):
    'bloco : opt_var_section opt_subr_section comando_composto'
    p[0] = Block(p[1], p[2], p[3])
    

# [<seção_declaração_variáveis>]
def p_opt_var_section(p):
    '''opt_var_section : var_section
                       | empty'''
    # debug
    p0 = None
    p[0] = p[1] if p[1] is not None else []

# <seção_declaração_variáveis> ::= 'var' <declaração_variáveis> ';' { <declaração_variáveis> ';' }
def p_var_section(p):
    'var_section : VAR decl_vars SEMI var_decl_list'
    global recovering
    recovering = False  # Resetar flag após seção completa
    p[0] = [p[2]] + p[4]

def p_var_decl_list(p):
    '''var_decl_list : decl_vars SEMI var_decl_list
                     | empty'''
    global recovering
    if len(p) == 2:
        p[0] = []
        recovering = False  # Resetar quando terminar lista
    else:
        p[0] = [p[1]] + p[3]

# Erro: 'var' duplicado no meio das declarações
def p_var_decl_list_error(p):
    '''var_decl_list : VAR decl_vars SEMI
                     | VAR error SEMI'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO SINTÁTICO: palavra-chave 'var' inesperada. A gramática só permite uma <seção_declaração_variáveis>. Linha {p.lineno(1)}")
    p[0] = []

# <declaração_variáveis> ::= <lista_identificadores> ':' <tipo>
def p_decl_vars(p):
    'decl_vars : lista_identificadores COLON tipo'
    p[0] = VarDecl(p[1], p[3])

# Erros em declaração de variáveis
def p_decl_vars_error(p):
    '''decl_vars : lista_identificadores error tipo
                 | lista_identificadores COLON error
                 | error COLON tipo'''
    global error_count
    error_count += 1
    if p[2] == 'error':
        print(f"ERRO SINTÁTICO na linha {p.lineno(2)}: ':' esperado na declaração de variáveis")
    elif p[3] == 'error':
        print(f"ERRO SINTÁTICO na linha {p.lineno(3)}: tipo esperado (integer ou boolean)")
    else:
        print(f"ERRO SINTÁTICO na linha {p.lineno(1)}: lista de identificadores inválida")
    p[0] = VarDecl(['error'], 'integer')

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

# ============ SEÇÃO DE SUBROTINAS ============

# [<seção_declaração_subrotinas>] ::= { ( <declaração_procedimento> | <declaração_função> ) ';' }
def p_opt_subr_section(p):
    '''opt_subr_section : subr_section
                        | empty'''
    p[0] = p[1] if p[1] is not None else []

def p_subr_section(p):
    'subr_section : subr_decl_list'
    p[0] = p[1]

def p_subr_decl_list(p):
    '''subr_decl_list : subr_decl SEMI subr_decl_list
                      | subr_decl SEMI'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_subr_decl(p):
    '''subr_decl : proc_decl
                 | func_decl'''
    p[0] = p[1]

# <declaração_procedimento> ::= 'procedure' <identificador> [ <parâmetros_formais> ] ';' <bloco_subrot>
def p_proc_decl(p):
    '''proc_decl : PROCEDURE ID opt_params SEMI bloco_subrot
                 | PROCEDURE ID SEMI bloco_subrot'''
    if len(p) == 6:
        p[0] = ProcDecl(p[2], p[3], p[5])
    else:
        p[0] = ProcDecl(p[2], [], p[4])

# <declaração_função> ::= 'function' <identificador> [ <parâmetros_formais> ] ':' <tipo> ';' <bloco_subrot>
def p_func_decl(p):
    '''func_decl : FUNCTION ID opt_params COLON tipo SEMI bloco_subrot
                 | FUNCTION ID COLON tipo SEMI bloco_subrot'''
    if len(p) == 8:
        p[0] = FuncDecl(p[2], p[3], p[5], p[7])
    else:
        p[0] = FuncDecl(p[2], [], p[4], p[6])

# Erro: () vazio em função (quando não há parâmetros, não deve ter parênteses)
def p_func_decl_error_empty_params(p):
    '''func_decl : FUNCTION ID LPAREN RPAREN COLON tipo SEMI bloco_subrot'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO SINTÁTICO: token ')' inesperado. Não deveria ter () em function sem parâmetros. Linha {p.lineno(4)}")
    p[0] = FuncDecl(p[2], [], p[6], p[8])
    
# Erro: tipo de retorno faltando em função
def p_func_decl_error_missing_type(p):
    '''func_decl : FUNCTION ID opt_params SEMI bloco_subrot'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO: Funções devem ter tipo de retorno (ex: : integer). Linha {p.lineno(1)}")
    # Constrói um nó dummy ou assume integer
    p[0] = FuncDecl(p[2], p[3], 'error', p[5])

# Erro: () vazio em procedure (quando não há parâmetros, não deve ter parênteses)  
def p_proc_decl_error_empty_params(p):
    '''proc_decl : PROCEDURE ID LPAREN RPAREN SEMI bloco_subrot'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO SINTÁTICO: token ')' inesperado. Não deveria ter () em procedure sem parâmetros. Linha {p.lineno(4)}")
    p[0] = ProcDecl(p[2], [], p[6])

# [<parâmetros_formais>]
def p_opt_params(p):
    '''opt_params : params
                  | empty'''
    p[0] = p[1] if p[1] is not None else []

# <parâmetros_formais> ::= '(' <declaração_parâmetros> { ';' <declaração_parâmetros> } ')'
def p_params(p):
    'params : LPAREN param_decl param_decl_list RPAREN'
    p[0] = [p[2]] + p[3]

def p_param_decl_list(p):
    '''param_decl_list : SEMI param_decl param_decl_list
                       | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]

# <declaração_parâmetros> ::= <lista_identificadores> ':' <tipo>
def p_param_decl(p):
    'param_decl : lista_identificadores COLON tipo'
    p[0] = ParamDecl(p[1], p[3])
    
# Erros em declaração de parâmetros
def p_param_decl_error(p):
    '''param_decl : lista_identificadores tipo
                  | lista_identificadores COLON error'''
    print("ERRO: Declaração de parâmetros malformada.")
    p[0] = ParamDecl(['error'], 'integer')

# <bloco_subrot> ::= [<seção_declaração_variáveis>] <comando_composto>
# IMPORTANTE: NÃO permite <seção_declaração_subrotinas> (sem aninhamento!)
def p_bloco_subrot(p):
    'bloco_subrot : opt_var_section comando_composto'
    global recovering
    recovering = False  # Resetar flag ao completar bloco de subrotina
    p[0] = Block(p[1], [], p[2])  # Sem subrotinas aninhadas!
    


# ERRO MELHORADO: Tentativa de aninhar subrotinas
# Esta regra consome a subrotina inválida inteira e continua processando
def p_bloco_subrot_error_nested(p):
    '''bloco_subrot : opt_var_section nested_subr_error comando_composto'''
    global error_count, recovering
    # O erro já foi reportado em nested_subr_error
    # Aqui apenas montamos o bloco ignorando a subrotina aninhada
    p[0] = Block(p[1], [], p[3])

# Captura e descarta subrotina aninhada completa
def p_nested_subr_error(p):
    '''nested_subr_error : FUNCTION ID opt_params COLON tipo SEMI nested_block SEMI
                         | FUNCTION ID COLON tipo SEMI nested_block SEMI
                         | PROCEDURE ID opt_params SEMI nested_block SEMI
                         | PROCEDURE ID SEMI nested_block SEMI'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        keyword = 'function' if p[1] == 'function' else 'procedure'
        print(f"ERRO SINTÁTICO: palavra-chave '{keyword}' inesperada. A regra <bloco_subrot> não permite aninhamento de sub-rotinas. Linha {p.lineno(1)}")
    # Retorna None para descartar esta subrotina
    pass

# Bloco aninhado (usado apenas para consumir a estrutura completa da subrotina aninhada)
def p_nested_block(p):
    '''nested_block : opt_var_section BEGIN nested_cmd_list END
                    | opt_var_section BEGIN END'''
    # Apenas consome tokens, não retorna nada útil
    pass

def p_nested_cmd_list(p):
    '''nested_cmd_list : nested_cmd
                       | nested_cmd SEMI nested_cmd_list'''
    # Apenas consome tokens
    pass

def p_nested_cmd(p):
    '''nested_cmd : ID ASSIGN expressao
                  | ID LPAREN lista_expressoes RPAREN
                  | ID LPAREN RPAREN
                  | IF expressao THEN nested_cmd
                  | IF expressao THEN nested_cmd ELSE nested_cmd
                  | WHILE expressao DO nested_cmd
                  | READ LPAREN lista_identificadores RPAREN
                  | WRITE LPAREN lista_expressoes RPAREN
                  | BEGIN nested_cmd_list END
                  | BEGIN END'''
    # Apenas consome tokens
    pass

# ============ COMANDOS ============

# <comando_composto> ::= 'begin' <comando> { ';' <comando> } 'end'
def p_comando_composto(p):
    'comando_composto : BEGIN comando cmd_list_tail END'
    p[0] = Compound([p[2]] + p[3])

# Erro: ';' antes de 'end' (último comando não deve ter ';')
def p_comando_composto_error_semi_before_end(p):
    '''comando_composto : BEGIN comando cmd_list_tail SEMI END
                        | BEGIN comando SEMI END'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO SINTÁTICO: token 'end' inesperado. Não deveria haver o ';' no último comando. Linha {p.lineno(len(p)-1)}")
    if len(p) == 6:
        p[0] = Compound([p[2]] + p[3])
    else:
        p[0] = Compound([p[2]])
       
# Erro: comando faltando entre 'begin' e 'end' 
def p_comando_composto_error_missing_comando(p):
    '''comando_composto : BEGIN cmd_list_tail END'''
    print(f"ERRO SINTÁTICO: comando esperado entre 'begin' e 'end'. Linha {p.lineno(1)}")
    p[0] = Compound([])

def p_cmd_list_tail(p):
    '''cmd_list_tail : SEMI comando cmd_list_tail
                     | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]
        



# Erro em lista de comandos - captura erro e sincroniza
def p_cmd_list_tail_error(p):
    'cmd_list_tail : SEMI error'
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
    p[0] = []

# <comando> ::= <atribuição> | <chamada_procedimento> | ...
def p_comando(p):
    '''comando : atribuicao
               | chamada_procedimento
               | condicional
               | repeticao
               | leitura
               | escrita
               | comando_composto'''
    global recovering
    recovering = False  # Resetar flag ao completar comando com sucesso
    p[0] = p[1]

# <atribuição> ::= <identificador> ':=' <expressão>
def p_atribuicao(p):
    'atribuicao : ID ASSIGN expressao'
    # Anexar número da linha de origem para diagnósticos
    p[0] = Assign(p[1], p[3], lineno=p.lineno(1))


# Erro: atribuição incompleta
def p_atribuicao_error(p):
    '''atribuicao : ID ASSIGN error
                  | ID error'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        if len(p) == 4 and p[2] == 'error':
            print(f"ERRO SINTÁTICO na linha {p.lineno(2)}: ':=' esperado para atribuição")
        else:
            print(f"ERRO SINTÁTICO: expressão inválida na atribuição")
    p[0] = Assign(p[1], Num(0))
    # Garantir que lineno esteja presente mesmo em casos de erro
    try:
        p[0].lineno = p.lineno(1)
    except Exception:
        pass

# <chamada_procedimento> ::= <identificador> '(' [ <lista_expressões> ] ')'
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

# Erros em condicional
def p_condicional_error(p):
    '''condicional : IF error THEN comando
                   | IF expressao error comando
                   | IF expressao THEN error'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        if p[2] == 'error':
            print(f"ERRO SINTÁTICO: expressão inválida após 'if'")
        elif p[3] == 'error':
            print(f"ERRO SINTÁTICO na linha {p.lineno(3)}: 'then' esperado após expressão do 'if'")
        else:
            print(f"ERRO SINTÁTICO: comando inválido após 'then'")
    p[0] = If(Bool('true'), Compound([]))

# <repetição> ::= 'while' <expressão> 'do' <comando>
def p_repeticao(p):
    'repeticao : WHILE expressao DO comando'
    p[0] = While(p[2], p[4])

# Erros em repetição
def p_repeticao_error(p):
    '''repeticao : WHILE error DO comando
                 | WHILE expressao error comando'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        if p[2] == 'error':
            print(f"ERRO SINTÁTICO: expressão inválida após 'while'")
        else:
            print(f"ERRO SINTÁTICO na linha {p.lineno(3)}: 'do' esperado após expressão do 'while'")
    p[0] = While(Bool('true'), Compound([]))

# <leitura> ::= 'read' '(' <lista_identificadores> ')'
def p_leitura(p):
    'leitura : READ LPAREN lista_identificadores RPAREN'
    p[0] = Read(p[3])
    

# <escrita> ::= 'write' '(' <lista_expressões> ')'
def p_escrita(p):
    'escrita : WRITE LPAREN lista_expressoes RPAREN'
    p[0] = Write(p[3])

# ============ EXPRESSÕES ============

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

# Erro em expressão com relação
def p_expressao_error(p):
    'expressao : expressao_simples relacao error'
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO SINTÁTICO: expressão inválida após operador relacional '{p[2]}'")
    p[0] = BinOp(p[2], p[1], Num(0))

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
        elif isinstance(p[1], int):
            # NUM = número literal
            p[0] = Num(p[1])
        else:
            # logico já processado (Bool)
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

# Erro: expressão entre parênteses incompleta
def p_fator_error(p):
    '''fator : LPAREN error RPAREN
             | LPAREN expressao error
             | NOT error
             | MINUS error'''
    global error_count, recovering
    if not recovering:
        error_count += 1
        recovering = True
        print(f"ERRO SINTÁTICO: expressão inválida")
    p[0] = Num(0)

# <lógico> ::= 'false' | 'true'
def p_logico(p):
    '''logico : FALSE
              | TRUE'''
    p[0] = Bool(p[1])

# Produção vazia
def p_empty(p):
    'empty :'
    pass

# Tratamento de erros genérico (último recurso)
# Esta função só é chamada quando NENHUMA regra de erro específica casa
def p_error(p):
    global error_count, recovering, _active_parser
    
    # Evitar mensagens de erro em cascata
    parser_obj = _active_parser

    if recovering:
        if p and parser_obj:
            parser_obj.errok()
        return
    
    error_count += 1
    recovering = True
    
    if p:
        # NOTA: Operadores seguidos (ex: a + * b) caem aqui porque o PLY não consegue
        # prever que um operador é inválido nesse contexto até tentar todas as regras.
        # Damos mensagem contextual APENAS para operadores para melhorar a experiência.
        if p.type in ('TIMES', 'DIV', 'AND'):
            print(f"ERRO SINTÁTICO na linha {p.lineno}: token inesperado '{p.value}'. O parser esperava um fator (variável, número, '(', 'not' ou '-')")
        elif p.type in ('PLUS', 'MINUS', 'OR'):
            print(f"ERRO SINTÁTICO na linha {p.lineno}: token inesperado '{p.value}'. O parser esperava um termo")
        else:
            # Mensagem genérica para outros tokens
            print(f"ERRO SINTÁTICO na linha {p.lineno}: token inesperado '{p.value}'")
        
        # Modo pânico: sincronizar em pontos seguros
        sync_count = 0
        while sync_count < 10:  # Limite de tokens para sincronização
            tok = parser_obj.token() if parser_obj else None
            if not tok:
                break
            
            # Pontos de sincronização
            if tok.type in ('SEMI', 'END', 'BEGIN', 'DOT'):
                if parser_obj:
                    parser_obj.errok()
                return tok
            
            sync_count += 1
        
        if parser_obj:
            parser_obj.errok()
    else:
        # EOF sem token - provavelmente falta algo no final do arquivo
        print("ERRO SINTÁTICO: fim de arquivo inesperado (EOF)")

# Construir parser
def make_parser():
    global _active_parser
    _active_parser = yacc.yacc(start='program')
    return _active_parser

# Teste do parser
if __name__ == '__main__':
    # Resetar variáveis globais
    error_count = 0
    recovering = False
    last_token = None
    
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
    
    # Criar lexer com rastreamento (global para acesso em p_error)
    tracked_lexer = TokenTracker(lexer)
    
    # Criar parser e fazer análise
    parser = make_parser()
    
    try:
        resultado = parser.parse(data, lexer=tracked_lexer)
        
        print("\n" + "=" * 60)
        if error_count == 0:
            print("ANÁLISE SINTÁTICA BEM-SUCEDIDA")
            print("=" * 60)
            
            if resultado:
                print("\nÁRVORE SINTÁTICA ABSTRATA (AST):\n")
                write_ast_verbose(resultado)
        else:
            print(f"ANÁLISE SINTÁTICA COMPLETADA COM {error_count} ERRO(S)")
            print("=" * 60)
            
            if resultado:
                print("\nÁRVORE SINTÁTICA ABSTRATA (PARCIAL):\n")
                write_ast_verbose(resultado)
            else:
                print("\nNão foi possível construir uma AST parcial devido aos erros encontrados.")
        
        print("\n" + "=" * 60)
        
        # Retornar código de erro se houver erros
        sys.exit(1 if error_count > 0 else 0)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("ANÁLISE SINTÁTICA ABORTADA")
        print(f"Erro: {e}")
        print("=" * 60)
        sys.exit(1)