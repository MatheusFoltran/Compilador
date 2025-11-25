import sys
from pathlib import Path
import ply.yacc as yacc

# garantir que o diretório do projeto esteja no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import parser

yacc.yacc(module=parser, start='program', debug=True)
print('Construindo tabelas LALR (debug) — isso exibirá conflitos (shift/reduce)')
# Constrói o parser com debug para que o PLY liste conflitos
try:
	# tentar escrever debug diretamente no stdout
	import sys as _sys
	yacc.yacc(module=parser, start='program', debug=1, debugfile=_sys.stdout)
except TypeError:
	# fallback para versões do PLY que não aceitam debugfile
	yacc.yacc(module=parser, start='program', debug=True)
print('Construção finalizada')
