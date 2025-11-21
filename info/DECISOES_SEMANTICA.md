# Decisões de projeto — resumo e estado atual

Este arquivo documenta as decisões arquiteturais tomadas para a análise
semântica do compilador, incluindo trade-offs e o estado atual da
implementação.

## Estratégia adotada

- Abordagem em duas fases (recomendada):
    1. 1ª passagem — Análise semântica e anotação da AST (`SemanticAnalyzer`).
    2. 2ª passagem — Geração de código a partir da AST anotada (pendente).

Motivação: a tabela de símbolos é gerenciada como uma pilha (destrutiva ao
final de cada escopo). Anotar a AST preserva a informação necessária para a
geração de código sem manter uma tabela global não-destrutiva.

## Escolhas importantes

- Representação de escopo: pilha de dicionários (`scope_stack`) com metadados
    (`scope_stack_meta`) e snapshots arquivados (`archived_scopes`).
- Modelagem de símbolos: classes `VarSymbol`, `ProcSymbol`, `FuncSymbol`
    provendo propriedades uniformes (`tipo`, `params`).
- Impressão: saída ASCII legível (funcionalidade em
    `SemanticAnalyzer.print_symbol_table`) que inclui escopos arquivados.

## Estado atual da implementação

- Anotação da AST: já implementada (várias anotações preenchidas por
    `SemanticAnalyzer.visit_*`).
- Impressão de tabela de símbolos com escopos arquivados: implementada.
- Geração de código (TAC/assembly) e cálculo de offsets: pendentes.

## Alternativas consideradas

- Manter uma TS não-destrutiva (persistente): simples, porém mantém em
    memória todos os símbolos e exige gerenciamento adicional.
- Reconstruir TS na 2ª passagem: mais custoso e duplicativo.

Racionalidade: anotação da AST (opção escolhida) oferece melhor separação de
responsabilidades e facilidade para gerar código posteriormente.

## Próximos passos e dependências

1. Calcular `offset` por variável/argumento (usar as anotações de nível e
     layout de frame) — necessário para geração de código.
2. Implementar gerador intermediário (TAC) usando apenas as anotações da
     AST (sem consultar `SymbolTable`).
3. Eventualmente, adicionar otimizações baseadas em TAC.
