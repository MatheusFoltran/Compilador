import ply.lex as lex

# Palavras reservadas (case-sensitive - apenas minúsculas)
reserved = {
    'program': 'PROGRAM',
    'procedure': 'PROCEDURE',
    'function': 'FUNCTION',
    'var': 'VAR',
    'begin': 'BEGIN',
    'end': 'END',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'false': 'FALSE',
    'true': 'TRUE',
    'while': 'WHILE',
    'do': 'DO',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'read': 'READ',
    'write': 'WRITE',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'div': 'DIV'
}

# Tokens básicos
tokens = [
    'ID', 'NUM',
    'PLUS', 'MINUS', 'TIMES',
    'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE',
    'ASSIGN',
    'LPAREN', 'RPAREN', 'SEMI', 'COLON', 'COMMA', 'DOT'
] + list(reserved.values())

# Operadores multi-caractere (definidos como funções para garantir precedência)
def t_NEQ(t):
    r'<>'
    return t

def t_LE(t):
    r'<='
    return t

def t_GE(t):
    r'>='
    return t

def t_ASSIGN(t):
    r':='
    return t

# Operadores e símbolos simples
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_EQ = r'='
t_LT = r'<'
t_GT = r'>'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMI = r';'
t_COLON = r':'
t_COMMA = r','
t_DOT = r'\.'

# Identificadores e palavras reservadas (case-sensitive)
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    # Verificar se é palavra reservada (exatamente como escrito)
    t.type = reserved.get(t.value, 'ID')
    return t

# Números inteiros
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Contar linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Espaços e tabs ignorados
t_ignore = ' \t\r'

# Detectar tentativas de comentário (mensagem amigável)
def t_comment_attempt(t):
    r'//|/\*|\{|\(\*|#'
    
    if t.value == '//':
        print(f"Erro léxico (linha {t.lineno}): comentários '//' não são permitidos em Rascal.")
        # Pular até o final da linha
        while t.lexer.lexpos < len(t.lexer.lexdata) and t.lexer.lexdata[t.lexer.lexpos] != '\n':
            t.lexer.skip(1)
    
    elif t.value == '#':
        print(f"Erro léxico (linha {t.lineno}): comentários '#' não são permitidos em Rascal.")
        # Pular até o final da linha
        while t.lexer.lexpos < len(t.lexer.lexdata) and t.lexer.lexdata[t.lexer.lexpos] != '\n':
            t.lexer.skip(1)
    
    elif t.value == '/*':
        print(f"Erro léxico (linha {t.lineno}): comentários '/* */' não são permitidos em Rascal.")
        t.lexer.skip(2)  # Pula /*
        # Tentar encontrar */ e pular tudo
        pos = t.lexer.lexdata.find('*/', t.lexer.lexpos)
        if pos != -1:
            # Encontrou o fechamento, pular até lá (incluindo o */)
            chars_to_skip = pos - t.lexer.lexpos + 2
            t.lexer.skip(chars_to_skip)
        # Se não encontrar */, deixa t_error tratar o resto
    
    elif t.value == '{':
        print(f"Erro léxico (linha {t.lineno}): comentários '{{ }}' não são permitidos em Rascal.")
        t.lexer.skip(1)  # Pula {
        # Tentar encontrar } e pular tudo
        pos = t.lexer.lexdata.find('}', t.lexer.lexpos)
        if pos != -1:
            # Encontrou o fechamento, pular até lá (incluindo o })
            chars_to_skip = pos - t.lexer.lexpos + 1
            t.lexer.skip(chars_to_skip)
        # Se não encontrar }, deixa t_error tratar o resto
    
    elif t.value == '(*':
        print(f"Erro léxico (linha {t.lineno}): comentários '(* *)' não são permitidos em Rascal.")
        t.lexer.skip(2)  # Pula (*
        # Tentar encontrar *) e pular tudo
        pos = t.lexer.lexdata.find('*)', t.lexer.lexpos)
        if pos != -1:
            # Encontrou o fechamento, pular até lá (incluindo o *)
            chars_to_skip = pos - t.lexer.lexpos + 2
            t.lexer.skip(chars_to_skip)
        # Se não encontrar *), deixa t_error tratar o resto

# Erro léxico padrão
def t_error(t):
    ch = t.value[0]
    print(f"Erro léxico (linha {t.lineno}): caractere inválido '{ch}'")
    t.lexer.skip(1)

# Construir lexer
lexer = lex.lex()