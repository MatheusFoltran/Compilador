import ply.lex as lex
import sys

# Contador global de erros léxicos
lex_error_count = 0

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

# Identificadores e palavras reservadas (DEVE vir PRIMEIRO)
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# Números inteiros
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Operadores multi-caractere (ordem importa!)
def t_ASSIGN(t):
    r':='
    return t

def t_NEQ(t):
    r'<>'
    return t

def t_LE(t):
    r'<='
    return t

def t_GE(t):
    r'>='
    return t

# Detectar tentativas de comentário (SEM { e ()
def t_COMMENT_SLASHSLASH(t):
    r'//.*'
    print(f"Erro léxico (linha {t.lineno}): comentários '//' não são permitidos em Rascal.")
    # Não retorna nada, token é descartado

def t_COMMENT_HASH(t):
    r'\#.*'
    print(f"Erro léxico (linha {t.lineno}): comentários '#' não são permitidos em Rascal.")
    # Não retorna nada, token é descartado

def t_COMMENT_CBLOCK(t):
    r'/\*(.|\n)*?\*/'
    print(f"Erro léxico (linha {t.lineno}): comentários '/* */' não são permitidos em Rascal.")
    t.lexer.lineno += t.value.count('\n')
    # Não retorna nada, token é descartado

# ADICIONAR ANTES de t_LPAREN
def t_COMMENT_BRACE(t):
    r'\{[^}]*\}'
    print(f"Erro léxico (linha {t.lineno}): comentários '{{}}' não são permitidos em Rascal.")
    t.lexer.lineno += t.value.count('\n')

def t_COMMENT_PAREN(t):
    r'\(\*(.|\n)*?\*\)'
    print(f"Erro léxico (linha {t.lineno}): comentários '(* *)' não são permitidos em Rascal.")
    t.lexer.lineno += t.value.count('\n')

# Contar linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Operadores e símbolos simples (string literals, não funções)
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

# Espaços e tabs ignorados
t_ignore = ' \t\r'

# Erro léxico padrão
def t_error(t):
    global lex_error_count
    lex_error_count += 1
    print(f"Erro léxico (linha {t.lineno}): caractere inválido '{t.value[0]}'")
    t.lexer.skip(1)

# Construir lexer
lexer = lex.lex()


# ============ TESTE DO LEXER ============
if __name__ == '__main__':
    # Verificar se foi passado arquivo como argumento ou via stdin
    if len(sys.argv) > 1:
        # Modo: python3 lexer.py exemplo.rascal
        filename = sys.argv[1]
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = f.read()
        except FileNotFoundError:
            print(f"Erro: arquivo '{filename}' não encontrado.")
            sys.exit(1)
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
            sys.exit(1)
    else:
        # Modo: python3 lexer.py < exemplo.rascal
        data = sys.stdin.read()
    
    # Se entrada vazia
    if not data.strip():
        print("Erro: entrada vazia.")
        sys.exit(1)
    
    # Processar tokens
    lexer.input(data)
    
    print("=" * 60)
    print("ANÁLISE LÉXICA - Tokens Reconhecidos")
    print("=" * 60)
    
    token_count = 0
    
    for tok in lexer:
        token_count += 1
        print(f'<{tok.type:12}, {tok.value!r:>15}> na linha: {tok.lineno}')
    
    print("=" * 60)
    print(f"Total de tokens reconhecidos: {token_count}")
    print("=" * 60)