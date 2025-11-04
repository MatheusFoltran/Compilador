# Regras de Erro do Parser

Este documento lista todas as regras de erro específicas implementadas no parser.

## 1. Programa (`p_program_error`)
**Captura:**
- Identificador faltando após `program`
- `;` faltando após identificador
- `.` faltando no final do programa
- EOF inesperado

**Mensagens:**
- "identificador esperado após 'program'"
- "';' esperado após o identificador do programa"
- "fim de arquivo inesperado (EOF). O parser esperava o token '.'"

---

## 2. Declaração de Variáveis (`p_var_decl_list_error`)
**Captura:**
- Palavra-chave `var` duplicada no meio das declarações

**Mensagem:**
- "palavra-chave 'var' inesperada. A gramática só permite uma <seção_declaração_variáveis>"

---

## 3. Declaração de Variáveis - Sintaxe (`p_decl_vars_error`)
**Captura:**
- `:` faltando na declaração
- Tipo faltando ou inválido
- Lista de identificadores inválida

**Mensagens:**
- "':' esperado na declaração de variáveis"
- "tipo esperado (integer ou boolean)"
- "lista de identificadores inválida"

---

## 4. Functions - Parênteses Vazios (`p_func_decl_error_empty_params`)
**Captura:**
- `function nome() : tipo` (não deve ter `()` quando não há parâmetros)

**Mensagem:**
- "token ')' inesperado. Não deveria ter () em function sem parâmetros"

---

## 5. Procedures - Parênteses Vazios (`p_proc_decl_error_empty_params`)
**Captura:**
- `procedure nome()` (não deve ter `()` quando não há parâmetros)

**Mensagem:**
- "token ')' inesperado. Não deveria ter () em procedure sem parâmetros"

---

## 6. Subrotinas Aninhadas (`p_nested_subr_error`)
**Captura:**
- Tentativa de declarar function/procedure dentro de outra subrotina
- A gramática NÃO permite aninhamento

**Mensagem:**
- "palavra-chave 'function/procedure' inesperada. A regra <bloco_subrot> não permite aninhamento de sub-rotinas"

---

## 7. Comando Composto - Ponto-e-vírgula extra (`p_comando_composto_error_semi_before_end`)
**Captura:**
- `;` antes do `end` (último comando não deve ter `;`)
- Ex: `begin write(1); end` ← erro!

**Mensagem:**
- "token 'end' inesperado. Não deveria haver o ';' no último comando"

---

## 8. Lista de Comandos (`p_cmd_list_tail_error`)
**Captura:**
- Erro genérico em lista de comandos
- Sincroniza e continua parsing

**Sem mensagem específica** (apenas incrementa contador)

---

## 9. Atribuição (`p_atribuicao_error`)
**Captura:**
- `:=` faltando
- Expressão inválida após `:=`

**Mensagens:**
- "':=' esperado para atribuição"
- "expressão inválida na atribuição"

---

## 10. Condicional (`p_condicional_error`)
**Captura:**
- Expressão inválida após `if`
- `then` faltando
- Comando inválido após `then`

**Mensagens:**
- "expressão inválida após 'if'"
- "'then' esperado após expressão do 'if'"
- "comando inválido após 'then'"

---

## 11. Repetição (`p_repeticao_error`)
**Captura:**
- Expressão inválida após `while`
- `do` faltando após expressão

**Mensagens:**
- "expressão inválida após 'while'"
- "'do' esperado após expressão do 'while'"

---

## 12. Expressão com Relação (`p_expressao_error`)
**Captura:**
- Expressão inválida após operador relacional (`=`, `<>`, `<`, etc.)

**Mensagem:**
- "expressão inválida após operador relacional '<op>'"

---

## 13. Fator (`p_fator_error`)
**Captura:**
- Expressão entre parênteses incompleta
- Expressão inválida após `not` ou `-`

**Mensagem:**
- "expressão inválida"

---

## Função `p_error` (Genérica)

**Quando é chamada:**
- Quando NENHUMA regra específica acima consegue tratar o erro
- É o "último recurso" do parser

**O que faz:**
- Mensagem genérica: "token inesperado 'X'"
- Sincronização (modo pânico) em `;`, `end`, `begin`, `.`
- **NÃO deve** ter lógica específica de erros

**Importante:**
- Casos específicos devem ser tratados nas regras acima
- `p_error` deve permanecer simples e genérica
