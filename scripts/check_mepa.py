#!/usr/bin/env python3
"""Checa um arquivo .mepa rodando o interpretador MEPA e reportando PASS/FAIL.

Uso:
    python3 scripts/check_mepa.py path/to/program.mepa

Retorna código 0 se o interpretador retornar -1 (terminou normalmente),
ou 1 em caso contrário.
"""
import sys
import io
from pathlib import Path

# Ensure project root is on sys.path so local `mepa` package can be imported
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if len(sys.argv) < 2:
    print("Uso: check_mepa.py <arquivo.mepa>")
    sys.exit(2)

mepa_path = Path(sys.argv[1])
if not mepa_path.exists():
    print(f"Arquivo não encontrado: {mepa_path}")
    sys.exit(2)

try:
    import mepa.mepa_defs as mepa_defs
    import mepa.mepa_interp as mepa_interp
except Exception as e:
    print(f"Erro ao importar módulos mepa: {e}")
    sys.exit(3)

# Abrir o arquivo .mepa e construir as estruturas P, L, MP
import re

# Read and sanitize MEPA labels so they conform to the interpreter's
# label syntax (alphanumeric labels starting with a letter). Some
# codegens use underscores in labels (e.g. INT_SQRT) which the
# interpreter rejects. We'll remove non-alphanumeric chars from
# label names and replace references accordingly.
with open(mepa_path, 'r', encoding='utf-8') as prog_file:
    raw_lines = prog_file.readlines()

label_map = {}
label_re = re.compile(r"^\s*([A-Za-z0-9_]+):")
for ln in raw_lines:
    m = label_re.match(ln)
    if m:
        lab = m.group(1)
        if not lab.isalnum():
            sanitized = ''.join(ch for ch in lab if ch.isalnum())
            if sanitized == "":
                sanitized = 'L'  # fallback
            label_map[lab] = sanitized

if label_map:
    print("Sanitizing MEPA labels:")
    for k, v in label_map.items():
        print(f"  {k} -> {v}")

    # Ordenar por comprimento decrescente para evitar substituições parciais
    sorted_labels = sorted(label_map.items(), key=lambda x: -len(x[0]))
    
    # Replace occurrences of original labels in the whole file
    new_lines = []
    for ln in raw_lines:
        new_ln = ln
        for orig, san in sorted_labels:
            new_ln = new_ln.replace(orig, san)
        new_lines.append(new_ln)
    prog_text = ''.join(new_lines)
else:
    prog_text = ''.join(raw_lines)

from io import StringIO

# Redirecionar mensagens do interpretador para evitar poluição do output
mepa_defs.MESS_FILE = io.StringIO()

prog_file_obj = StringIO(prog_text)
# Feed the in-memory file-like object to mepa_defs
mepa_defs.PROG_FILE = prog_file_obj
try:
    P, L = mepa_defs.inputProgram()
    mepa_defs.fixArgs(P, L)
    MP = mepa_defs.makeMepa(P)
except SystemExit:
    # O interpretador chamou sys.exit() com erro — ler mensagem de erro
    err_msg = mepa_defs.MESS_FILE.getvalue().strip()
    print(f"Falha ao ler/compilar MEPA: {err_msg}")
    sys.exit(4)
except Exception as e:
    print(f"Falha ao ler/compilar MEPA: {e}")
    sys.exit(4)

# Preparar IO do interpretador
msfile = io.StringIO()
# Entradas padrão para testes (valores típicos para equação quadrática: a=1, b=5, c=6)
# Isso dá delta = 25 - 24 = 1, raízes x1=-2, x2=-3
default_inputs = '1\n5\n6\n' + '0\n' * 29  # 3 inputs significativos + 29 zeros de backup
infile = io.StringIO(default_inputs)
outfile = io.StringIO()

# Executar o interpretador
try:
    res = mepa_interp.execute(MP, P, L, msfile, infile, outfile)
except Exception as e:
    print(f"Erro ao executar MEPA: {e}")
    sys.exit(5)

# Imprimir resultados resumidos
print(f"MEPA file: {mepa_path}")
print(f"Interpreter result: {res}")
stdout_contents = outfile.getvalue()
if stdout_contents:
    print("--- Program Output ---")
    print(stdout_contents)
    print("--- End Output ---")

# Conclusão: res == -1 significa execução normal no nosso convenção testada
if res == -1:
    print("PASS: programa terminou normalmente (res == -1)")
    sys.exit(0)
else:
    print("FAIL: programa não terminou normalmente")
    sys.exit(1)
