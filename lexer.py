# lexer.py
import ply.lex as lex

# palavras reservadas
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

# tokens básicos (IDs e NUM também)
tokens = [
    'ID', 'NUM',
    'PLUS', 'MINUS', 'TIMES',
    'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE',
    'ASSIGN',
    'LPAREN', 'RPAREN', 'SEMI', 'COLON', 'COMMA', 'DOT'
] + list(reserved.values())

# símbolos — agrupando operadores relacionais para evitar ambiguidade
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
# cobrir oper. relacionais multi-char primeiro via alternância:
t_EQ     = r'='
t_NEQ    = r'<>'
# alternativa segura: combine em uma só regex (opcional)
t_LE     = r'<='
t_GE     = r'>='
t_LT     = r'<'
t_GT     = r'>'
t_ASSIGN = r':='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMI   = r';'
t_COLON  = r':'
t_COMMA  = r','
t_DOT    = r'\.'

# identificadores e palavras reservadas
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    # case-sensitive: manter o lexema original
    t.type = reserved.get(t.value, 'ID')
    return t

# números inteiros
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# contar linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# espaços e tabs ignorados
t_ignore = ' \t\r'

# detectar tentativas de comentário (não permitidas em Rascal)
def t_comment_attempt(t):
    r'//|\{'
    # mensagem mais amigável
    if t.value == '//':
        print(f"Erro léxico (linha {t.lineno}): comentários '//' não são permitidos em Rascal.")
    else:
        print(f"Erro léxico (linha {t.lineno}): comentários '{t.value}' não são permitidos em Rascal.")
    # não consumir o resto da linha automaticamente — permitir t_error cuidar do caractere
    # pular 0 caracteres: avançar 1 para evitar loop
    t.lexer.skip(1)

# erro léxico padrão
def t_error(t):
    ch = t.value[0]
    print(f"Caractere inválido na linha {t.lineno}: '{ch}' (offset {t.lexpos})")
    t.lexer.skip(1)

# construir lexer
lexer = lex.lex()
