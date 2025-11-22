# Compilador (Rascal subset)
Este repositório contém um compilador educacional para a linguagem rascal.
Ele implementa as fases clássicas: lexer, parser (PLY), análise semântica e geração de código para uma máquina virtual MEPA.

## Estrutura do repositório (resumo)
- `lexer.py` — regras léxicas (PLY).
- `parser.py` — gramática e construção da AST (PLY).
- `ast_nodes.py` — definição dos nós AST e funções de impressão (verbose / s-expression).
- `interpreter.py` — analisador semântico, tabela de símbolos e utilitários de diagnóstico.
- `mepa_codegen.py` — geração de código MEPA.
- `scripts/show_mepa.py` — gera arquivos `.mepa` para exemplos em `input/`.
- `main.py` — executa pipeline completo (lexer → parser → semântico → gera `.mepa` em `output_main/`).
- `testes/` — testes pytest.

## Requisitos
- Python 3.8+ (testado em Python 3.12).
- Dependências (instalar no virtualenv):

```bash
python3 -m pip install -r requirements.txt
```

## Como usar

- Criar e ativar um virtualenv (recomendado):

```bash
python3 -m venv venv
source venv/bin/activate -> Linux
venv\Scripts\activate -> Windows
```

- Rodar o pipeline para um arquivo (`main.py` gera `.mepa` em `output_main/` e imprime tokens, AST e tabela de símbolos):

```bash
python3 main.py input/correto02.ras
```

- Gerar `.mepa` para todos os exemplos `input/correto*.ras` (usa `output_mepa/`):

```bash
python3 scripts/show_mepa.py
```

- Executar o parser manualmente e imprimir AST verbose:

```bash
python3 parser.py input/correto01.ras
```

- Rodar testes (pytest):

```bash
python3 -m pytest -q
```