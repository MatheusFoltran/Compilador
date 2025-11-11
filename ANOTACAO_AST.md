# Anotação da AST - Implementação Completa

## Visão Geral

A AST (Abstract Syntax Tree) é anotada durante a primeira passagem (análise semântica) com informações que serão necessárias para a geração de código. Isso implementa a estratégia de duas passagens:

1. **Passagem 1**: Análise semântica + Anotação da AST
2. **Passagem 2**: Geração de código usando a AST anotada

## Motivação

A tabela de símbolos é **destrutiva** - quando saímos de um escopo local, os símbolos daquele escopo são removidos. Portanto, ao gerar código posteriormente, não teríamos acesso às informações de variáveis locais.

**Solução**: Anotar a AST durante a análise semântica, armazenando todas as informações necessárias diretamente nos nós da árvore.

## Anotações Implementadas

### 1. Variáveis (Var)
```python
@dataclass
class Var(Expr):
    id: str
    # Anotações semânticas
    tipo: Optional[str] = None           # Tipo da variável ('integer' ou 'boolean')
    scope_level: Optional[int] = None    # Nível léxico (0=global, 1+=local)
    offset: Optional[int] = None         # Offset na pilha (calculado depois)
```

**Quando**: Durante `visit_Var`
**Informações**: 
- `tipo`: O tipo da variável (integer/boolean) obtido da tabela de símbolos
- `scope_level`: O nível de escopo onde a variável foi declarada
- `offset`: Será calculado na fase de geração de código

### 2. Atribuições (Assign)
```python
@dataclass
class Assign(Cmd):
    id: str
    expr: Expr
    # Anotações semânticas
    var_type: Optional[str] = None       # Tipo da variável
    var_scope_level: Optional[int] = None  # Nível léxico
    var_offset: Optional[int] = None       # Offset na pilha
```

**Quando**: Durante `visit_Assign`
**Informações**:
- `var_type`: Tipo da variável sendo atribuída
- `var_scope_level`: Nível de escopo da variável
- `var_offset`: Será calculado depois

**Nota**: Funções podem receber atribuições (para retornar valor)

### 3. Operações Binárias (BinOp)
```python
@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr
    # Anotações semânticas
    result_type: Optional[str] = None  # Tipo resultante da operação
```

**Quando**: Durante `visit_BinOp`
**Informações**:
- `result_type`: O tipo do resultado após a operação
  - Aritméticos (+, -, *, div) → `integer`
  - Relacionais (=, <>, <, <=, >, >=) → `boolean`
  - Lógicos (and, or) → `boolean`

### 4. Operações Unárias (UnOp)
```python
@dataclass
class UnOp(Expr):
    op: str
    operand: Expr
    # Anotações semânticas
    result_type: Optional[str] = None  # Tipo resultante
```

**Quando**: Durante `visit_UnOp`
**Informações**:
- `result_type`: Tipo do resultado ('+'/'-' → integer, 'not' → boolean)

### 5. Chamadas de Função (FuncCall)
```python
@dataclass
class FuncCall(Expr):
    name: str
    args: List[Expr]
    # Anotações semânticas
    return_type: Optional[str] = None        # Tipo de retorno
    param_types: Optional[List[str]] = None  # Tipos dos parâmetros
```

**Quando**: Durante `visit_FuncCall`
**Informações**:
- `return_type`: O tipo de retorno da função
- `param_types`: Lista dos tipos dos parâmetros (para verificação)

### 6. Chamadas de Procedimento (ProcCall)
```python
@dataclass
class ProcCall(Cmd):
    name: str
    args: List[Expr]
    # Anotações semânticas
    param_types: Optional[List[str]] = None  # Tipos dos parâmetros
```

**Quando**: Durante `visit_ProcCall`
**Informações**:
- `param_types`: Lista dos tipos dos parâmetros esperados

### 7. Condicionais (If)
```python
@dataclass
class If(Cmd):
    cond: Expr
    then_cmd: Cmd
    else_cmd: Optional[Cmd] = None
    # Anotações semânticas
    cond_type: Optional[str] = None  # Tipo da condição
```

**Quando**: Durante `visit_If`
**Informações**:
- `cond_type`: Tipo da condição (deve ser `boolean`)

### 8. Repetição (While)
```python
@dataclass
class While(Cmd):
    cond: Expr
    body: Cmd
    # Anotações semânticas
    cond_type: Optional[str] = None  # Tipo da condição
```

**Quando**: Durante `visit_While`
**Informações**:
- `cond_type`: Tipo da condição (deve ser `boolean`)

### 9. Leitura (Read)
```python
@dataclass
class Read(Cmd):
    ids: List[str]
    # Anotações semânticas
    var_types: Optional[List[str]] = None  # Tipos das variáveis
```

**Quando**: Durante `visit_Read`
**Informações**:
- `var_types`: Lista com os tipos de cada variável sendo lida

### 10. Escrita (Write)
```python
@dataclass
class Write(Cmd):
    exprs: List[Expr]
    # Anotações semânticas
    expr_types: Optional[List[str]] = None  # Tipos das expressões
```

**Quando**: Durante `visit_Write`
**Informações**:
- `expr_types`: Lista com os tipos de cada expressão sendo escrita

### 11. Números Literais (Num)
```python
@dataclass
class Num(Expr):
    value: int
    # Anotações semânticas
    tipo: Optional[str] = None  # Sempre 'integer'
```

**Quando**: Durante `visit_Num`
**Informações**:
- `tipo`: Sempre `'integer'` para literais numéricos

### 12. Booleanos Literais (Bool)
```python
@dataclass
class Bool(Expr):
    value: bool
    # Anotações semânticas
    tipo: Optional[str] = None  # Sempre 'boolean'
```

**Quando**: Durante `visit_Bool`
**Informações**:
- `tipo`: Sempre `'boolean'` para literais booleanos

## Estratégia de Uso

### Fase 1: Análise Semântica (IMPLEMENTADA)
```python
# Em interpreter.py - SemanticAnalyzer
def visit_Var(self, node):
    symbol = self.symbol_table.lookup(node.id)
    # ANOTAR AST
    node.tipo = symbol.tipo
    node.scope_level = symbol.scope_level
    return symbol.tipo
```

### Fase 2: Geração de Código (A IMPLEMENTAR)
```python
# Futuro CodeGenerator
def visit_Var(self, node):
    # Usar informações anotadas
    tipo = node.tipo          # Sem consultar tabela de símbolos!
    level = node.scope_level
    offset = node.offset
    # Gerar código de acesso à variável
    ...
```

## Vantagens

1. **Auto-suficiência**: AST anotada contém todas as informações necessárias
2. **Simplicidade**: Gerador de código não precisa da tabela de símbolos
3. **Separação**: Análise semântica e geração de código são independentes
4. **Eficiência**: Informações calculadas uma vez, usadas múltiplas vezes

## Teste

Execute `test_ast_annotation.py` para visualizar as anotações:

```bash
python test_ast_annotation.py teste/correto01.ras
```

Saída mostrará algo como:
```
Var: [tipo=integer, scope_level=0]
BinOp: [result_type=integer]
Assign: [var_type=integer, var_scope_level=0]
FuncCall: [return_type=integer, param_types=['integer']]
```

## Próximos Passos

1. ✅ Implementação da anotação (COMPLETO)
2. ⏳ Cálculo de offsets para variáveis
3. ⏳ Implementação do gerador de código usando AST anotada
4. ⏳ Geração de TAC (Three-Address Code) ou Assembly

## Arquivos Modificados

- `ast_nodes.py`: Adicionados campos de anotação em todas as classes
- `interpreter.py`: Todos os métodos `visit_*` anotam a AST
- `test_ast_annotation.py`: Script de teste para visualizar anotações
- `DECISOES_SEMANTICA.md`: Documentação da decisão arquitetural
- `ANOTACAO_AST.md`: Este documento
