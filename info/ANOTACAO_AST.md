
# Anotação da AST — campos atuais e onde são preenchidos

Este documento lista os campos de anotação efetivamente presentes nos
nós da AST (`ast_nodes.py`) e indica quais métodos do analisador
(`interpreter.py` — `SemanticAnalyzer`) os preenchem.

Observação: a implementação atual já preenche a maioria dos campos
necessários para a geração de código; o cálculo de `offset` ficará para a
etapa de geração de código.

## Campos principais por nó

- `Var` (em `ast_nodes.py`):
    - `tipo: Optional[str]` — preenchido em `SemanticAnalyzer.visit_Var`
    - `scope_level: Optional[int]` — nível léxico da declaração (preenchido)
    - `offset: Optional[int]` — reservado para futura geração de código

- `Assign`:
    - `var_type: Optional[str]` — tipo da variável alvo (preenchido em
        `visit_Assign`)
    - `var_scope_level: Optional[int]` — nível léxico da variável
    - `var_offset: Optional[int]` — reservado para geração de código

- `BinOp`:
    - `result_type: Optional[str]` — preenchido em `visit_BinOp`

- `UnOp`:
    - `result_type: Optional[str]` — preenchido em `visit_UnOp`

- `FuncCall`:
    - `return_type: Optional[str]` — setado em `visit_FuncCall`
    - `param_types: Optional[List[str]]` — tipos esperados dos parâmetros
        (quando aplicável)

- `ProcCall`:
    - `param_types: Optional[List[str]]` — tipos esperados dos parâmetros

- `Read`:
    - `var_types: Optional[List[str]]` — populado em `visit_Read` com tipos
        das variáveis lidas

- `Write`:
    - `expr_types: Optional[List[str]]` — tipos das expressões a escrever
        (preenchido em `visit_Write`)

- `If` / `While`:
    - `cond_type: Optional[str]` — tipo da condição (deve ser `boolean`),
        preenchido em `visit_If` / `visit_While`

- `Num`:
    - `tipo` = `'integer'` (literal)

- `Bool`:
    - `tipo` = `'boolean'` (literal)

## Onde as anotações são definidas

- `SemanticAnalyzer.visit_Var` — consulta a `SymbolTable` e preenche
    `Var.tipo` e `Var.scope_level`.
- `visit_Assign` — anota `Assign.var_type` e `Assign.var_scope_level` antes
    de verificar compatibilidade entre `expr` e destino.
- `visit_BinOp` e `visit_UnOp` — calculam e preenchem `result_type`.
- `visit_ProcCall` / `visit_FuncCall` — preenchem `param_types` e
    `FuncCall.return_type` e verificam número/tipos de argumentos.
- `visit_Read` / `visit_Write` — preenchem `var_types` / `expr_types`.

## Uso na geração de código (próximo passo)

Na fase de geração de código o gerador deverá usar apenas as anotações da
AST (em vez de consultar a `SymbolTable`) — por exemplo: `Var.scope_level`
e `Var.offset` (quando computado) serão suficientes para gerar instruções
de acesso à variável.

---

Se preferir, gero um exemplo de AST anotada para um `correto*.ras` e coloco a
saída aqui como ilustração.

