import ply.yacc as yacc
import parser

print('Construindo parser com debug...')
parser_obj = yacc.yacc(start='program', debug=True)
print('Parser construído com debug')
# Fazer parse do arquivo de teste
with open('input/sintatico07.ras', 'r', encoding='utf-8') as f:
    data = f.read()

print('\nFazendo parse...')
res = parser_obj.parse(data, lexer=parser.TokenTracker(parser.lexer))
print('Parse terminado. Resultado:', res)
