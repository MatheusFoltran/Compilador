# Análise Semântica — Estado atual do projeto

Documento conciso descrevendo a implementação atual da análise semântica e da
estrutura de símbolos usada pelo analisador em `interpreter.py`.

## Visão geral rápida

- Implementação em `interpreter.py` com a classe `SemanticAnalyzer`.
- Tabela de símbolos: `SymbolTable` (pilha de dicionários) com metadados de
    escopo e arquivamento de escopos ao sair (útil para debug/impressão).
- Símbolos modelados por `Symbol`, `VarSymbol`, `ProcSymbol`, `FuncSymbol`.
- A análise anota a AST (nós em `ast_nodes.py`) com tipos, níveis e demais
    metadados necessários para a futura geração de código.

## Estrutura da tabela de símbolos

- `SymbolTable.scope_stack`: lista de dicionários, um por escopo (0 = global).
- `SymbolTable.scope_stack_meta`: metadados por escopo ativo (level, owner,
    category, label, parent_label, order, status).
- `SymbolTable.archived_scopes`: lista de snapshots (metadados + símbolos)
    arquivados quando `exit_scope()` é chamado — preserva informação para
    impressão e depuração.

Operações públicas principais (em `SymbolTable`):

- `enter_scope(owner: Optional[str]=None, category: str='local')` — cria novo
    escopo; armazena metadados (owner, label, level, parent, order).
- `exit_scope()` — remove o escopo atual da pilha e arquiva uma cópia em
    `archived_scopes` (mantendo metadados e símbolos para impressão).
- `declare(name, category, tipo=None, params=None, *, is_param=False)` — cria
    e insere um símbolo no escopo atual (verifica duplicação apenas no escopo
    corrente).
- `lookup(name)` — busca do escopo corrente para o global (contexto
    envolvente mais próximo); levanta `SemanticError` se não encontrar.
- `exists(name)` — booleano se o símbolo é acessível em algum escopo.

Complexidades típicas:

- `declare`, `lookup`, `exists`: média O(1) (dicionário) por escopo; o
    `lookup` pode percorrer os N escopos no pior caso (O(depth)).

## Modelagem de símbolos

- `Symbol` (base): campos `name` e `scope_level`, propriedades `category`,
    `tipo` e `params` implementadas nas subclasses.
- `VarSymbol`: `var_type`, `is_param` → expõe `tipo`.
- `ProcSymbol`: `param_list` → expõe `params`.
- `FuncSymbol`: herda `ProcSymbol` e adiciona `return_type` → expõe `tipo`.

Essas classes fornecem uma interface consistente: `symbol.tipo` e
`symbol.params` são usados pela análise e pelo printer.

## O que o analisador checa / anota

- Declaração de variáveis/procedures/functions (duplicação local é erro).
- Verificação de tipos para expressões binárias (`+ - * div`, relacionais,
    lógicos) e operadores unários (`-`, `not`).
- Verificação de chamadas (existe, categoria correta, número e tipos de
    argumentos).
- Anotação da AST: tipos (por exemplo `Var.tipo`, `BinOp.result_type`),
    níveis léxicos (`Var.scope_level`), e metadados em `Assign`, `FuncCall`,
    `ProcCall`, `Read`, `Write`, `If`, `While`, etc. (veja `ast_nodes.py`).

A função utilitária `analyze_semantics(ast_root)` cria o `SemanticAnalyzer`,
executa a análise e imprime a tabela de símbolos (ativos + arquivados).

## Impressão da tabela de símbolos

- `SemanticAnalyzer.print_symbol_table()` produz saída ASCII legível que
    inclui tanto escopos ativos quanto os escopos arquivados (snapshots
    obtidos em `exit_scope()`).
- Os escopos são exibidos com um cabeçalho contendo `label`, `nivel`,
    `categoria`, `pai` e `status` (active/archived), e tabelas separadas para
    variáveis, procedures e functions.

## Testes e execução

- Testes automatizados (pytest) encontram-se na pasta `testes/`.
- Exemplos de entrada estão em `input/` (antes chamados `teste/`).
- Execução manual rápida:

```bash
# Parse + semantics via scripts de teste pytest (recomendado)
venv/bin/pytest testes

# Runner CLI para arquivos corretos (ex.: input/correto01.ras)
venv/bin/python run_corretos.py
```

## Estado atual e próximos passos

- Anotação da AST: implementada (vários campos já preenchidos durante
    análise semântica).
- Cálculo de `offset` para variáveis (para geração de código) ainda não
    implementado — ficará para a fase de geração de código (2ª passagem).
- Geração de código (TAC/assembly) é a próxima grande etapa.

---

Se quiser, aplico pequenas amostras de saída ou incluo exemplos concretos
gerados pela execução do analisador para ilustrar a impressão da tabela.
