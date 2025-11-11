# Decisões de Projeto - Análise Semântica

## 🎯 Estratégia Escolhida: DUAS PASSAGENS

### Motivação
A linguagem Rascal tem procedures e functions com escopo aninhado. Para geração de código eficiente, precisamos saber:
- **Nível léxico** de cada variável (para calcular offset de acesso)
- **Endereço/offset** na pilha
- **Tipo** para conversões
- **Informações de procedures/functions** (número de parâmetros, variáveis locais, etc.)

Com uma TS **destrutiva** (que desempilha escopos), perderíamos essas informações na 2ª passagem.

### Solução: Duas Passagens

#### **1ª PASSAGEM: Verificação Semântica + Anotação da AST**
- ✅ Verifica tipos
- ✅ Detecta erros semânticos
- ✅ **ANOTA a AST** com informações da TS:
  - Tipo de cada expressão
  - Nível léxico de cada variável
  - Offset/endereço de cada variável
  - Informações de procedures/functions

**Vantagem:** AST anotada é **autossuficiente** para geração de código

#### **2ª PASSAGEM: Geração de Código**
- ✅ Percorre AST **anotada**
- ✅ Usa informações já calculadas (não precisa da TS)
- ✅ Gera código intermediário/final

---

## 📋 Implementação Atual vs. Ideal

### Status Atual ❌
```
Parser → AST → Análise Semântica (1 passagem)
                ├─ Verificação de tipos ✅
                ├─ Detecção de erros ✅
                └─ Anotação da AST ❌ (NÃO IMPLEMENTADO)
```

### Status Ideal ✅
```
Parser → AST → 1ª Passagem: Análise Semântica
                ├─ Verificação de tipos ✅
                ├─ Detecção de erros ✅
                └─ Anotação da AST ✅
            → AST Anotada → 2ª Passagem: Geração de Código
                                          └─ TAC/Assembly
```

---

## 🔧 Melhorias Necessárias

### 1. Anotar a AST com Informações Semânticas

Adicionar campos aos nós da AST:
- `Var`: adicionar `symbol_info` (tipo, nível léxico, offset)
- `FuncCall`: adicionar `function_info` (tipo retorno, parâmetros)
- `Assign`: adicionar `target_info` (informações da variável)

### 2. Preservar Informações para Geração de Código

Opções:
- **A) Anotar AST** (recomendado) - informações ficam nos nós
- **B) TS Persistente** - manter uma TS separada não-destrutiva
- **C) Tabela de Símbolos Global** - reconstruir TS na 2ª passagem

**Escolha:** Opção A (Anotar AST) - mais limpo e eficiente

---

## 📊 Informações a Anotar

### Variáveis
```python
@dataclass
class Var(Expr):
    name: str
    # Anotações semânticas:
    tipo: Optional[str] = None          # Tipo inferido
    scope_level: Optional[int] = None   # Nível léxico
    offset: Optional[int] = None        # Offset na pilha
```

### Expressões
```python
@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr
    # Anotações semânticas:
    result_type: Optional[str] = None   # Tipo do resultado
```

### Functions/Procedures
```python
@dataclass
class FuncCall(Expr):
    name: str
    args: List[Expr]
    # Anotações semânticas:
    return_type: Optional[str] = None   # Tipo de retorno
    param_types: Optional[List[str]] = None  # Tipos esperados
```

---

## 🚀 Próximos Passos

1. ✅ **Fase 1 Completa:** Verificação semântica básica
2. 🔄 **Fase 2 (Atual):** Anotar AST com informações semânticas
3. ⏳ **Fase 3 (Futuro):** Geração de código intermediário (TAC)
4. ⏳ **Fase 4 (Futuro):** Otimizações e geração de código final

---

## 💡 Alternativa: UMA PASSAGEM (mais simples)

Se a geração de código for **simples**, podemos fazer tudo em uma passagem:

### Modificação na TS: Torná-la NÃO-DESTRUTIVA
```python
def exit_scope(self):
    # Ao invés de desempilhar, marcar como "inacessível"
    self.scope_stack[-1]['_active'] = False
    self.current_scope_level -= 1
    # NÃO remove: self.scope_stack.pop()
```

**Vantagem:** Mais simples, menos código
**Desvantagem:** TS cresce durante compilação, menos limpo

---

## 🎓 Conclusão

**Decisão Final:** **DUAS PASSAGENS com Anotação da AST**

**Justificativa:**
1. Separa concerns (verificação vs. geração)
2. AST anotada é autossuficiente
3. Mais fácil de debugar
4. Padrão em compiladores modernos
5. Facilita otimizações futuras
