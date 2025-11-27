"""Pytest conftest: garante import do código do projeto.

Insere a raiz do projeto no `sys.path` para que módulos como
`parser`, `lexer`, etc. sejam importáveis durante os testes.
"""
import sys
from pathlib import Path

# diretório 'testes' -> pai é a raiz do projeto
ROOT = Path(__file__).resolve().parent.parent
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    # inserir no início para priorizar código local
    sys.path.insert(0, ROOT_STR)
