# Regras de Erro do Parser (atualizado)

Este documento lista as regras de erro específicas implementadas em
`parser.py` e descreve o comportamento da função genérica `p_error`.

O parser inclui um wrapper `TokenTracker` (mantém `prev_token` e
`last_token`) para fornecer contexto adicional nas mensagens de erro. A
função `make_parser()` armazena o parser em `_active_parser` para que
`p_error` consiga invocar `token()`/`errok()` sem causar NameError.

## Regras específicas implementadas

- `p_program_error`: erros na declaração do `program` (identificador
	ausente, `;` ausente, `.` ausente, EOF inesperado). Emite mensagens
	contextuais indicando o token esperado.

- `p_var_decl_list_error`: detecta `var` duplicado no meio da seção de
	variáveis.

- `p_decl_vars_error`: captura erros de sintaxe em `decl_vars` (`:`
	faltando, tipo inválido, lista de ids inválida).

- `p_func_decl_error_empty_params` / `p_proc_decl_error_empty_params`:
	detectam e tratam `()` em declaration sem parâmetros.

- `p_nested_subr_error`: consome subrotinas aninhadas inválidas (a
	gramática não permite aninhamento de procedures/functions dentro de
	sub-rotinas) e continua parsing.

- `p_comando_composto_error_semi_before_end`: detecta `;` extra antes de
	`end` em blocos `begin ... end`.

- `p_cmd_list_tail_error`: captura erros em listas de comandos e faz
	sincronização simples (sem mensagem detalhada).

- `p_atribuicao_error`, `p_condicional_error`, `p_repeticao_error`,
	`p_expressao_error`, `p_fator_error`: regras locais que emitem mensagens
	específicas para cada contexto quando possível.

## `p_error` (tratamento genérico)

Comportamento atual em `parser.py`:

- Usa a flag global `recovering` para evitar mensagens repetidas em cascata.
- Ao encontrar o primeiro erro, incrementa `error_count` e define
	`recovering = True`.
- Se já estiverem em modo de recuperação, chama `parser_obj.errok()` e
	retorna sem emitir nova mensagem.
- Quando tiver um token `p`, tenta dar mensagens um pouco mais
	contextuais para operadores comuns (casos que o PLY não cobre bem):
	- `TIMES`, `DIV`, `AND` → mensagem sugerindo que era esperado um fator
	- `PLUS`, `MINUS`, `OR` → mensagem sugerindo que era esperado um termo
	- outros tokens → mensagem genérica "token inesperado 'X'"

- Em seguida realiza sincronização (modo pânico): consome até 10 tokens
	ou até encontrar um token de sincronização (`SEMI`, `END`, `BEGIN`,
	`DOT`). Ao encontrar um token de sincronização, chama
	`parser_obj.errok()` e retorna o token para permitir retomada.
- Se não houver token (EOF), imprime mensagem de EOF inesperado.

## Boas práticas e observações

- Prefira regras específicas `p_xxx_error` sempre que for possível fornecer
	uma mensagem contextual e montar parte da AST. `p_error` deve ser o
	último recurso genérico.
- A sincronização tem limite (10 tokens) para evitar loops longos durante a
	recuperação; esse valor pode ser ajustado conforme necessidade.

