# Análise Semântica - Compilador Rascal

## 📚 Visão Geral

Implementação completa de análise semântica para a linguagem Rascal, com verificação de tipos, controle de escopos e detecção de erros semânticos.

## 🏗️ Arquitetura da Tabela de Símbolos

### Estrutura de Dados Escolhida

**Hash Table (Dicionário Python)**
- **Vantagens:**
  - Inserção: O(1)
  - Busca: O(1)
  - Remoção: O(1)
  - Estrutura dinâmica (cresce conforme necessário)
- **Implementação:** Pilha de dicionários para suporte a escopo aninhado

### Modelo de Symbol

Cada símbolo contém:

```python
@dataclass
class Symbol:
    name: str              # Nome do identificador
    category: str          # 'var', 'proc' ou 'func'
    tipo: str              # Tipo (integer/boolean ou tipo de retorno)
    params: List[tuple]    # Parâmetros (para proc/func)
    scope_level: int       # Nível de escopo (0 = global)
```

### Controle de Escopo

**Escopo Estático/Léxico**
- Implementado via pilha de tabelas de símbolos
- Cada nível de aninhamento (programa, procedure, function) tem sua própria tabela
- Regra: **Contexto envolvente mais próximo** (busca de dentro para fora)

**Operações:**
1. **enter_scope()**: Cria novo nível quando entra em procedure/function
2. **exit_scope()**: Remove/torna inacessível símbolos locais ao sair
3. **declare()**: Insere símbolo no escopo atual (verifica duplicação no mesmo escopo)
4. **lookup()**: Busca símbolo do escopo mais interno para o mais externo

## 🔍 Verificações Implementadas

### 1. Declaração de Identificadores

**Variáveis:**
- ✅ Verifica se já foi declarada no mesmo escopo
- ✅ Permite shadowing (mesmo nome em escopos diferentes)
- ✅ Verifica uso antes da declaração

**Procedures:**
- ✅ Declaração com lista de parâmetros
- ✅ Parâmetros declarados como variáveis locais
- ✅ Escopo local para o corpo da procedure

**Functions:**
- ✅ Declaração com lista de parâmetros e tipo de retorno
- ✅ Parâmetros declarados como variáveis locais
- ✅ Escopo local para o corpo da function

### 2. Verificação de Tipos

**Operadores Aritméticos** (`+`, `-`, `*`, `div`):
- ✅ Ambos operandos devem ser `integer`
- ✅ Resultado é `integer`

**Operadores Relacionais** (`=`, `<>`, `<`, `<=`, `>`, `>=`):
- ✅ Operandos devem ser do mesmo tipo
- ✅ Resultado é `boolean`

**Operadores Lógicos** (`and`, `or`):
- ✅ Ambos operandos devem ser `boolean`
- ✅ Resultado é `boolean`

**Operadores Unários:**
- ✅ `-`: operando deve ser `integer`, resultado é `integer`
- ✅ `not`: operando deve ser `boolean`, resultado é `boolean`

**Atribuições:**
- ✅ Tipo da expressão deve ser compatível com tipo da variável
- ✅ Não permite atribuir a procedures/functions

**Condicionais (if/while):**
- ✅ Condição deve ser `boolean`

### 3. Chamadas de Procedures/Functions

**Verificações:**
- ✅ Procedure/Function foi declarada
- ✅ Número correto de argumentos
- ✅ Tipos dos argumentos compatíveis com parâmetros
- ✅ Function retorna o tipo correto

## 📋 Exemplos de Erros Detectados

### Erro 1: Variável Não Declarada
```rascal
program Err1;
begin
    x := 1  // ❌ ERRO: Variável 'x' não foi declarada
end.
```

### Erro 2: Incompatibilidade de Tipos
```rascal
program Err2;
var b: boolean;
begin
    b := 1 < 2 + true  // ❌ ERRO: Operador '+' requer operandos integer,
                       //            mas recebeu integer e boolean
end.
```

### Erro 3: Número Incorreto de Argumentos
```rascal
program Err3;
    procedure q(a: integer; b: integer);
    begin
        write(a + b)
    end;
begin
    q(1)  // ❌ ERRO: Procedure 'q' espera 2 argumento(s), mas recebeu 1
end.
```

## 🎯 Decisões de Projeto

### 1. Estrutura de Dados

**Escolha: Hash Table (dict) para cada escopo**

*Alternativas consideradas:*
- ❌ Lista encadeada: Busca O(n) - muito lenta
- ❌ Árvore de busca: Complexidade de implementação desnecessária
- ✅ Hash table: Melhor compromisso entre simplicidade e eficiência

### 2. Representação de Escopo

**Escolha: Pilha de tabelas (uma por escopo)**

*Alternativas consideradas:*
- ❌ Tabela única com campo "escopo": Dificuldade em remover símbolos ao sair de escopo
- ✅ Pilha de tabelas: Implementação natural de escopo estático, remoção automática ao sair

### 3. Tamanho da Tabela

**Escolha: Estrutura dinâmica**

*Justificativa:*
- Programas típicos: centenas a milhares de símbolos
- Dicionário Python cresce dinamicamente
- Sem necessidade de pré-dimensionamento

### 4. Organização dos Símbolos

**Escolha: Tabela única para todos os tipos de identificadores**

*Alternativas consideradas:*
- ❌ Tabelas separadas (uma para var, proc, func): Duplicação de código, busca em múltiplas tabelas
- ✅ Tabela única com campo "category": Simplicidade, busca unificada

## 🚀 Como Testar

### Teste Individual
```bash
venv/bin/python test_semantic.py teste/semantico01.ras
```

### Suite Completa
```bash
venv/bin/python test_semantic.py
```

## 📊 Saída da Tabela de Símbolos

A tabela é exibida de forma organizada por nível de escopo:

```
================================================================================
TABELA DE SÍMBOLOS (Escopo Estático/Léxico)
================================================================================

  ┌─ Escopo Global ─
  │  x                    : integer    (variável)
  │  soma                 (a: integer, b: integer) -> integer (function)
  │  imprimir             (msg: integer) (procedure)

  ┌─ Escopo Local (nível 1) ─
  │  a                    : integer    (variável)
  │  b                    : integer    (variável)
================================================================================
```

## 🔧 Extensões Futuras

### Possíveis Melhorias:
1. **Tipos compostos**: Arrays, records
2. **Inferência de tipos**: Para simplificar declarações
3. **Análise de fluxo**: Detecção de código inalcançável
4. **Verificação de inicialização**: Uso de variáveis antes de atribuição
5. **Anotação da AST**: Adicionar informações de tipo nos nós para geração de código

## 📖 Referências

- **Escopo estático**: Resolução de nomes em tempo de compilação
- **Regra do contexto envolvente**: Busca do escopo mais interno para o externo
- **Shadowing**: Variável local "esconde" variável de escopo externo com mesmo nome
